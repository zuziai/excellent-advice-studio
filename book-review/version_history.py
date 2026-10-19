"""Read-only illustration ancestry from the current and archived published waves."""
from hashlib import sha256
from pathlib import Path
import json
import re
import threading


IDEA_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z')
ART_IMAGE = re.compile(r'art/([A-Za-z0-9][A-Za-z0-9_.-]*\.(png|jpg|jpeg|webp))\Z', re.I)
IMAGE_HASH = re.compile(r'[0-9a-f]{64}\Z', re.I)
PUBLIC_FIELDS = ('id', 'version', 'image', 'title', 'titleFa', 'summaryFa',
                 'storyFa', 'meaningFa', 'alt', 'width', 'height', 'parentIdeaId',
                 'revisionSummaryFa')


class HistoryError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class ImageHistory:
    """Only explicit parent links count as revisions; filenames are never inferred."""
    def __init__(self, project):
        self.project = Path(project).resolve()
        self.data = self.project.parent / 'review-data'
        self.archives = self.data / 'waves'
        self.art = (self.project / 'dist' / 'art').resolve()
        self._lock = threading.Lock()
        self._signature = None
        self._index = {}

    def _published_sources(self):
        current = self.project / 'dist' / 'wave.json'
        archives = []
        if self.archives.is_dir():
            for path in self.archives.glob('*.json'):
                try:
                    if path.resolve().parent == self.archives.resolve():
                        stat = path.stat()
                        archives.append((stat.st_mtime_ns, str(path), path))
                except OSError:
                    continue
        # Current content wins when immutable candidates are repeated in snapshots.
        return [current, *(item[2] for item in sorted(archives, reverse=True))]

    def _load_index(self):
        with self._lock:
            sources = self._published_sources()
            try:
                signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size)
                                  for p in sources)
            except OSError:
                raise HistoryError('Published image history is unavailable', 503)
            if signature == self._signature:
                return self._index
            index = {}
            for position, path in enumerate(sources):
                try:
                    wave = json.loads(path.read_text(encoding='utf-8-sig'))
                except (OSError, UnicodeError, json.JSONDecodeError):
                    if position == 0:
                        raise HistoryError('Published image history is unavailable', 503)
                    continue
                if not isinstance(wave, dict) or not isinstance(wave.get('sentences'), list):
                    continue
                for sentence in wave['sentences']:
                    if not isinstance(sentence, dict) or not isinstance(sentence.get('ideas'), list):
                        continue
                    for idea in sentence['ideas']:
                        if (isinstance(idea, dict) and isinstance(idea.get('id'), str)
                                and IDEA_ID.fullmatch(idea['id'])):
                            index.setdefault(idea['id'], (sentence.get('id'), idea))
            self._index, self._signature = index, signature
            return index

    def _public_candidate(self, idea):
        image = idea.get('image')
        match = ART_IMAGE.fullmatch(image) if isinstance(image, str) else None
        if not match:
            raise HistoryError('Published image is unavailable', 409)
        path = (self.art / match[1]).resolve()
        if path.parent != self.art or not path.is_file():
            raise HistoryError('Published image is unavailable', 409)
        try:
            with path.open('rb') as source:
                header = source.read(12)
                suffix = match[2].lower()
                valid = ((suffix == 'png' and header.startswith(b'\x89PNG\r\n\x1a\n'))
                         or (suffix in ('jpg', 'jpeg') and header.startswith(b'\xff\xd8\xff'))
                         or (suffix == 'webp' and header[:4] == b'RIFF' and header[8:12] == b'WEBP'))
                if not valid:
                    raise HistoryError('Published image failed verification', 409)
                digest = sha256(header)
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(block)
                actual_hash = digest.hexdigest()
        except OSError:
            raise HistoryError('Published image is unavailable', 409)
        expected_hash = idea.get('imageHash')
        if expected_hash is not None and (not isinstance(expected_hash, str)
                or not IMAGE_HASH.fullmatch(expected_hash)
                or actual_hash != expected_hash.lower()):
            raise HistoryError('Published image failed verification', 409)
        candidate = {key: idea.get(key) for key in PUBLIC_FIELDS}
        candidate['version'] = idea.get('version', 1)
        candidate['imageHash'] = actual_hash
        candidate['fullGenerationPromptEnglish'] = (
            idea.get('fullGenerationPromptEnglish') or idea.get('prompt') or '')
        return candidate

    def _ancestor_metadata(self, idea_id, sentence_id):
        """Recover an exact linked legacy ancestor, never enumerate draft candidates."""
        # Older published waves did not archive every intermediate revision. A
        # published child's explicit parent link is the evidence that this exact
        # ancestor belongs to its history. Only bounded-depth exact-name lookups
        # are allowed, and the displayed art must still match its recorded hash.
        excluded = {'node_modules', 'waves', 'tests', 'fixtures', 'github-export'}
        try:
            parents = [p for p in self.data.iterdir() if p.name not in excluded
                       and p.is_dir() and p.resolve().parent == self.data.resolve()]
        except OSError:
            return None
        for directory in parents:
            possible = [directory / (idea_id + '.metadata.json')]
            try:
                possible.extend(child / (idea_id + '.metadata.json')
                                for child in directory.iterdir()
                                if child.name not in excluded and child.is_dir()
                                and child.resolve().parent == directory.resolve())
            except OSError:
                pass
            for path in possible:
                try:
                    if not path.is_file() or path.resolve().parent != path.parent.resolve():
                        continue
                    metadata = json.loads(path.read_text(encoding='utf-8-sig'))
                except (OSError, UnicodeError, json.JSONDecodeError):
                    continue
                if (not isinstance(metadata, dict) or metadata.get('id') != idea_id
                        or metadata.get('sentenceNumber', metadata.get('sentenceId')) != sentence_id):
                    continue
                recorded_hash = metadata.get('imageHash') or metadata.get('sha256')
                if not isinstance(recorded_hash, str) or not IMAGE_HASH.fullmatch(recorded_hash):
                    continue
                candidate = dict(metadata)
                if not candidate.get('image'):
                    output = candidate.get('outputPath')
                    if not isinstance(output, str):
                        continue
                    candidate['image'] = 'art/' + output.replace('\\', '/').rsplit('/', 1)[-1]
                candidate['imageHash'] = recorded_hash
                return sentence_id, candidate
        return None

    def get(self, idea_id):
        if not isinstance(idea_id, str) or not IDEA_ID.fullmatch(idea_id):
            raise HistoryError('Invalid idea identifier')
        index = self._load_index()
        if idea_id not in index:
            raise HistoryError('Published idea not found', 404)
        sentence_id = index[idea_id][0]
        versions, warnings, seen = [], [], set()
        cursor = idea_id
        while cursor:
            if cursor in seen:
                warnings.append('زنجیرهٔ نسخه‌های قبلی دارای پیوند تکراری است؛ نمایش در این نقطه متوقف شد.')
                break
            seen.add(cursor)
            entry = index.get(cursor)
            if entry is None and cursor != idea_id:
                entry = self._ancestor_metadata(cursor, sentence_id)
            if entry is None or entry[0] != sentence_id:
                warnings.append('اطلاعات یکی از نسخه‌های قبلی در آرشیو انتشار موجود نیست.')
                break
            idea = entry[1]
            try:
                versions.append(self._public_candidate(idea))
            except HistoryError:
                if cursor == idea_id:
                    raise
                warnings.append('یکی از نسخه‌های قبلی قابل تأیید یا نمایش نیست؛ بقیهٔ نسخه‌ها نمایش داده می‌شوند.')
            parent = idea.get('parentIdeaId')
            if parent is not None and (not isinstance(parent, str) or not IDEA_ID.fullmatch(parent)):
                warnings.append('پیوند یکی از نسخه‌های قبلی معتبر نیست.')
                break
            cursor = parent
        return {'currentIdeaId': idea_id, 'versions': list(reversed(versions)),
                'incomplete': bool(warnings), 'warningsFa': warnings}
