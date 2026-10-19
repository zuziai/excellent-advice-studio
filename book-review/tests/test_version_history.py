"""Read-only ancestry and HTTP boundary tests; fixtures never touch real reviews."""
from hashlib import sha256
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json
import struct
import sys
import threading
import unittest
import zlib

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
from version_history import HistoryError, ImageHistory


def png(shade):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes((0, shade, 0, 0)))) + chunk(b'IEND', b''))


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / 'book-review'
        self.art = self.project / 'dist' / 'art'
        self.archives = self.root / 'review-data' / 'waves'
        self.art.mkdir(parents=True)
        self.archives.mkdir(parents=True)
        self.history = ImageHistory(self.project)

    def tearDown(self):
        self.temporary.cleanup()

    def candidate(self, version, parent=None):
        idea_id = f'154-test-v{version}'
        content = png(version)
        (self.art / (idea_id + '.png')).write_bytes(content)
        return {'id': idea_id, 'version': version, 'parentIdeaId': parent,
                'image': f'art/{idea_id}.png', 'imageHash': sha256(content).hexdigest(),
                'titleFa': 'نمونه', 'storyFa': 'روایت', 'width': 1, 'height': 1,
                'fullGenerationPromptEnglish': 'Full image prompt',
                'metadataPaths': ['private/local/metadata'], 'token': 'never-return'}

    def wave(self, ideas, archive=None):
        path = self.archives / archive if archive else self.project / 'dist' / 'wave.json'
        path.write_text(json.dumps({'sentences': [{'id': 154, 'ideas': ideas}]}), encoding='utf-8')

    def chain(self, count=5):
        ideas = [self.candidate(n, f'154-test-v{n-1}' if n > 1 else None)
                 for n in range(1, count + 1)]
        self.wave(ideas[:-1], 'published-old.json')
        self.wave(ideas[-1:])
        return ideas

    def test_five_versions_oldest_first_without_orphan_drafts_or_secrets(self):
        ideas = self.chain()
        orphan = self.candidate(6, ideas[-1]['id'])
        draft = self.root / 'review-data' / 'unpublished'
        draft.mkdir()
        (draft / (orphan['id'] + '.metadata.json')).write_text(json.dumps(orphan), encoding='utf-8')
        result = self.history.get(ideas[-1]['id'])
        self.assertEqual([i['id'] for i in result['versions']], [i['id'] for i in ideas])
        self.assertFalse(result['incomplete'])
        self.assertNotIn('metadataPaths', result['versions'][0])
        self.assertNotIn('token', result['versions'][0])
        with self.assertRaises(HistoryError) as raised:
            self.history.get(orphan['id'])
        self.assertEqual(raised.exception.status, 404)

    def test_exact_linked_legacy_metadata_recovers_missing_ancestor(self):
        first, second, third = self.chain(3)
        self.wave([first], 'published-old.json')
        legacy = self.root / 'review-data' / 'revision-example'
        legacy.mkdir()
        metadata = {**second, 'sentenceNumber': 154, 'sha256': second['imageHash'],
                    'outputPath': 'C:\\old-workspace\\' + second['id'] + '.png'}
        metadata.pop('image')
        metadata.pop('imageHash')
        (legacy / (second['id'] + '.metadata.json')).write_text(json.dumps(metadata), encoding='utf-8')
        result = self.history.get(third['id'])
        self.assertEqual([i['version'] for i in result['versions']], [1, 2, 3])
        self.assertFalse(result['incomplete'])

    def test_missing_ancestor_keeps_current_visible_and_warns(self):
        current = self.candidate(2, '154-missing-v1')
        self.wave([current])
        result = self.history.get(current['id'])
        self.assertEqual([i['id'] for i in result['versions']], [current['id']])
        self.assertTrue(result['incomplete'])

    def test_cycle_is_bounded(self):
        one = self.candidate(1, '154-test-v2')
        two = self.candidate(2, one['id'])
        self.wave([one], 'old.json')
        self.wave([two])
        result = self.history.get(two['id'])
        self.assertEqual(len(result['versions']), 2)
        self.assertTrue(result['incomplete'])

    def test_tampered_ancestor_is_omitted_but_valid_ancestry_continues(self):
        ideas = self.chain(3)
        (self.art / '154-test-v2.png').write_bytes(png(99))
        result = self.history.get(ideas[-1]['id'])
        self.assertEqual([i['version'] for i in result['versions']], [1, 3])
        self.assertTrue(result['incomplete'])

    def test_current_hash_mismatch_cannot_be_displayed(self):
        current = self.chain(1)[0]
        (self.art / '154-test-v1.png').write_bytes(png(99))
        with self.assertRaises(HistoryError) as raised:
            self.history.get(current['id'])
        self.assertEqual(raised.exception.status, 409)

    def test_traversal_is_rejected_in_input_and_published_asset(self):
        current = self.chain(1)[0]
        for value in ('../secret', 'foo/bar', '', 'a' * 101):
            with self.assertRaises(HistoryError) as raised:
                self.history.get(value)
            self.assertEqual(raised.exception.status, 400)
        current['image'] = 'art/../../secret.png'
        self.wave([current])
        with self.assertRaises(HistoryError) as raised:
            self.history.get(current['id'])
        self.assertEqual(raised.exception.status, 409)

    def test_index_refreshes_after_new_published_wave(self):
        first = self.chain(1)[0]
        self.assertEqual(len(self.history.get(first['id'])['versions']), 1)
        second = self.candidate(2, first['id'])
        self.wave([first], 'old.json')
        self.wave([second])
        self.assertEqual(len(self.history.get(second['id'])['versions']), 2)

    def test_http_endpoint_query_validation_and_local_host(self):
        current = self.chain(1)[0]
        specification = importlib.util.spec_from_file_location('history_server_fixture', CODE / 'server.py')
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        module.PROJECT = self.project
        module.IMAGE_HISTORY = self.history
        class QuietHandler(module.Handler):
            def log_message(self, *_args):
                pass
        httpd = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        module.PORT = httpd.server_port
        worker = threading.Thread(target=httpd.serve_forever, daemon=True)
        worker.start()
        try:
            for path, expected in [('/api/image-history?ideaId=' + current['id'], 200),
                                   ('/api/image-history?ideaId=unknown', 404),
                                   ('/api/image-history?ideaId=..%2Fsecret', 400),
                                   ('/api/image-history', 400),
                                   ('/api/image-history?ideaId=a&ideaId=b', 400)]:
                connection = HTTPConnection('127.0.0.1', module.PORT)
                connection.request('GET', path)
                response = connection.getresponse()
                self.assertEqual(response.status, expected)
                self.assertEqual(response.getheader('Cache-Control'), 'no-store')
                body = json.loads(response.read())
                if expected == 200:
                    self.assertEqual(body['currentIdeaId'], current['id'])
                connection.close()
            connection = HTTPConnection('127.0.0.1', module.PORT)
            connection.request('GET', '/api/image-history?ideaId=' + current['id'], headers={'Host': 'evil.example'})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            connection.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            worker.join()


if __name__ == '__main__':
    unittest.main()
