"""Local review server. Feedback stays in the workspace; no image is auto-approved."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json, secrets, threading, os, re, mimetypes
from finalization import Finalizer

PROJECT = Path(__file__).resolve().parent
DATA = PROJECT.parent / 'review-data'
FEEDBACK = DATA / 'feedback.json'
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.RLock()
PORT = 8765

def read_feedback():
    if FEEDBACK.exists():
        return json.loads(FEEDBACK.read_text(encoding='utf-8'))
    return {'format':'excellent-advice-feedback','version':1,'records':[]}

def validate_feedback(payload):
    wave = json.loads((PROJECT/'dist'/'wave.json').read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or payload.get('format') != 'excellent-advice-feedback' or payload.get('version') != 1:
        raise ValueError('Unknown feedback format')
    if payload.get('waveId') != wave['id']:
        raise ValueError('Feedback is for a different wave')
    records = payload.get('records')
    if not isinstance(records, list) or len(records) > 460:
        raise ValueError('Invalid records')
    valid = {s['id']:{i['id'] for i in s['ideas']} for s in wave['sentences']}
    versions = {i['id']:i.get('version',1) for s in wave['sentences'] for i in s['ideas']}
    old = {r['sentenceId']:r for r in read_feedback().get('records', [])}
    seen = set()
    for r in records:
        if not isinstance(r, dict) or type(r.get('sentenceId')) is not int or r['sentenceId'] in seen:
            raise ValueError('Invalid sentence record')
        sid = r['sentenceId']; seen.add(sid)
        if sid not in valid:
            continue  # A browser may also hold records from previous waves.
        if r.get('status') not in ('pending','approved','revise','revise_all','custom_idea','rejected'):
            raise ValueError('Invalid decision')
        chosen = r.get('chosenIdeaId')
        if r['status'] in ('approved','revise') and chosen not in valid[sid]:
            raise ValueError('Unknown chosen idea')
        if r['status'] in ('pending','revise_all','custom_idea','rejected') and chosen is not None:
            raise ValueError('Unexpected choice')
        notes = r.get('ideaNotes',{})
        # Keep earlier-candidate comments when a rejected/revised sentence gets a new set.
        if not isinstance(notes,dict) or len(notes)>100 or any(not isinstance(k,str) or len(k)>100 or not isinstance(v,str) or len(v)>10000 for k,v in notes.items()):
            raise ValueError('Invalid idea feedback')
        if not isinstance(r.get('note',''), str) or len(r.get('note','')) > 10000:
            raise ValueError('Invalid sentence feedback')
        custom = r.get('customIdea','')
        if not isinstance(custom,str) or len(custom)>10000:
            raise ValueError('Invalid custom idea')
        variants = r.get('requestedVariants')
        if variants is not None and (type(variants) is not int or variants != 5):
            raise ValueError('Invalid variant count')
        batch = r.get('batchRequest')
        submitted_custom = batch.get('customIdea','') if isinstance(batch,dict) else custom
        if r['status']=='custom_idea' and (not isinstance(submitted_custom,str) or not submitted_custom.strip() or variants != 5):
            raise ValueError('A custom idea and five variants are required')
        if batch is not None:
            if not isinstance(batch,dict) or r['status'] not in ('revise_all','custom_idea','rejected') or batch.get('status')!=r['status'] or batch.get('sentenceId')!=sid:
                raise ValueError('Invalid batch request')
            if any(not isinstance(batch.get(k),str) or not batch[k].strip() or len(batch[k])>100 for k in ('requestId','submittedAt')):
                raise ValueError('Invalid batch identity')
            candidates=batch.get('baseCandidateIds')
            if not isinstance(candidates,list) or len(candidates)!=len(valid[sid]) or any(not isinstance(c,str) for c in candidates) or set(candidates)!=valid[sid]:
                raise ValueError('Invalid batch candidates')
            if not isinstance(batch.get('comment'),str) or len(batch['comment'])>10000 or not isinstance(batch.get('customIdea'),str) or len(batch['customIdea'])>10000:
                raise ValueError('Invalid batch text')
            expected=5 if r['status']=='custom_idea' else len(valid[sid])
            if type(batch.get('requestedVariants')) is not int or batch['requestedVariants']!=expected:
                raise ValueError('Invalid batch variant count')
            batch_notes=batch.get('ideaNotes',{})
            if not isinstance(batch_notes,dict) or len(batch_notes)>100 or any(not isinstance(k,str) or len(k)>100 or not isinstance(v,str) or len(v)>10000 for k,v in batch_notes.items()):
                raise ValueError('Invalid batch idea notes')
        revision = r.get('revisionRequest')
        if revision is not None:
            if not isinstance(revision,dict) or r['status']!='revise' or revision.get('baseIdeaId')!=chosen:
                raise ValueError('Invalid revision target')
            if any(not isinstance(revision.get(k),str) or not revision[k].strip() or len(revision[k])>limit for k,limit in [('requestId',100),('submittedAt',100),('comment',10000)]):
                raise ValueError('Invalid revision request')
            if type(revision.get('baseVersion')) is not int or revision['baseVersion']!=versions[chosen]:
                raise ValueError('Invalid revision version')
        progress = r.get('revisionProgress')
        if progress is not None:
            if not isinstance(progress,dict) or revision is None or progress.get('requestId')!=revision['requestId'] or progress.get('status') not in ('queued','in_progress','failed'):
                raise ValueError('Invalid revision progress')
            if not isinstance(progress.get('message',''),str) or len(progress.get('message',''))>500:
                raise ValueError('Invalid progress message')
            if any(progress.get(k) is not None and not isinstance(progress[k],str) for k in ('updatedAt','startedAt','finishedAt')):
                raise ValueError('Invalid progress timestamp')
        if r.get('updatedAt') is not None and not isinstance(r['updatedAt'],str):
            raise ValueError('Invalid timestamp')
        if not isinstance(r.get('history', []), list) or len(r.get('history', [])) > 500:
            raise ValueError('Invalid review history')
        intent = r.get('decisionIntent')
        if intent is not None:
            if (not isinstance(intent,dict) or intent.get('status') != r['status']
                    or intent.get('chosenIdeaId') != chosen
                    or any(not isinstance(intent.get(k),str) or not intent[k].strip()
                           or len(intent[k]) > 100 for k in ('id','submittedAt'))):
                raise ValueError('Invalid explicit decision')
        previous = old.get(sid)
        if previous and previous.get('status') == 'approved' and r['status'] == 'pending':
            explicit_clear = (intent is not None and intent['status'] == 'pending'
                              and intent['submittedAt'] > (previous.get('updatedAt') or ''))
            if not explicit_clear:
                # Loading an old browser cache is not an instruction to cancel a choice.
                r = {**r, **{k:previous.get(k) for k in
                    ('status','chosenIdeaId','revisionRequest','revisionProgress',
                     'batchRequest','requestedVariants','updatedAt')}}
                if previous.get('decisionIntent') is not None:
                    r['decisionIntent'] = previous['decisionIntent']
                else:
                    r.pop('decisionIntent', None)
        if sid not in old or (r.get('updatedAt') or '') >= (old[sid].get('updatedAt') or ''):
            previous = old.get(sid)
            if previous:
                # A browser cannot accidentally erase earlier server-side review history.
                combined = list(previous.get('history', []))
                for entry in r.get('history', []):
                    if entry not in combined: combined.append(entry)
                if previous.get('status') == 'approved' and (r.get('status'), chosen) != ('approved', previous.get('chosenIdeaId')):
                    snapshot = {k:previous.get(k) for k in ('status','chosenIdeaId','updatedAt','waveId','ideaNotes','note')}
                    if snapshot not in combined: combined.append(snapshot)
                if combined: r['history'] = combined
            old[sid] = r
    return {**payload, 'records':list(old.values())}

def finalization_status():
    try:
        return Finalizer(PROJECT).inspect(read_feedback())
    except Exception:
        return []

def finalize_current(sentence_id=None, idea_id=None):
    with LOCK:
        feedback = read_feedback()
        if sentence_id is not None:
            current = next((r for r in feedback.get('records',[]) if r.get('sentenceId') == sentence_id), None)
            if not current or current.get('status') != 'approved' or current.get('chosenIdeaId') != idea_id:
                raise ValueError('This image is not currently approved')
        try:
            return Finalizer(PROJECT).finalize(feedback)
        except Exception as error:
            return [{'sentenceId':r['sentenceId'],'ideaId':candidate['id'],'status':'pending',
                     'messageFa':'نظرها ذخیره شدند؛ ذخیرهٔ نهایی کامل نشد. دوباره تلاش کنید.'}
                    for r,candidate in Finalizer(PROJECT).current_approvals(feedback)]

def save_feedback(payload, apply_approved=False):
    with LOCK:
        checked = validate_feedback(payload)
        DATA.mkdir(exist_ok=True)
        temporary = FEEDBACK.with_suffix('.json.new')
        temporary.write_text(json.dumps(checked, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, FEEDBACK)
        if apply_approved:
            checked = {**checked, 'finalizations':finalize_current()}
        return checked

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(PROJECT/'dist'),**kwargs)
    def send_json(self,value,status=200):
        data=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def allowed_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{PORT}',f'localhost:{PORT}')
    def send_original_download(self, head_only=False):
        name = unquote(urlsplit(self.path).path.removeprefix('/download/'))
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.(?:png|jpg|jpeg|webp)', name, re.IGNORECASE):
            return self.send_json({'error':'Invalid image filename'},400)
        art = (PROJECT/'dist'/'art').resolve()
        image = (art/name).resolve()
        if image.parent != art or not image.is_file():
            return self.send_json({'error':'Image not found'},404)
        with image.open('rb') as source:
            self.send_response(200)
            self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream')
            self.send_header('Content-Disposition',f'attachment; filename="{name}"')
            self.send_header('Content-Length',str(os.fstat(source.fileno()).st_size))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers()
            if not head_only:
                self.copyfile(source,self.wfile)
    def do_HEAD(self):
        if not self.allowed_host():
            return self.send_json({'error':'Invalid local host'},403)
        if urlsplit(self.path).path.startswith('/download/'):
            return self.send_original_download(head_only=True)
        return super().do_HEAD()
    def do_GET(self):
        if not self.allowed_host():
            return self.send_json({'error':'Invalid local host'},403)
        if urlsplit(self.path).path == '/api/feedback':
            return self.send_json({**read_feedback(),'localReview':True,'token':TOKEN,'finalizations':finalization_status()})
        if urlsplit(self.path).path == '/api/finalizations':
            return self.send_json({'finalizations':finalization_status()})
        if urlsplit(self.path).path.startswith('/download/'):
            return self.send_original_download()
        return super().do_GET()
    def do_POST(self):
        route = urlsplit(self.path).path
        if route not in ('/api/feedback','/api/finalize'):
            return self.send_json({'error':'Unknown route'},404)
        if not self.allowed_host() or self.headers.get('X-Review-Token') != TOKEN:
            return self.send_json({'error':'Invalid local review session'},403)
        origin=self.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}'):
            return self.send_json({'error':'Invalid origin'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 1000000: raise ValueError('Invalid payload size')
            payload=json.loads(self.rfile.read(length).decode('utf-8'))
            if route == '/api/finalize':
                if not isinstance(payload,dict) or type(payload.get('sentenceId')) is not int or not isinstance(payload.get('ideaId'),str):
                    raise ValueError('Invalid finalization target')
                return self.send_json({'saved':True,'finalizations':finalize_current(payload['sentenceId'],payload['ideaId'])})
            result=save_feedback(payload, apply_approved=True)
            return self.send_json({'saved':True,'records':len(result['records']),'finalizations':result.get('finalizations',[])})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as error:
            return self.send_json({'error':str(error)},400)

if __name__ == '__main__':
    print(f'Illustration review: http://127.0.0.1:{PORT}',flush=True)
    print(f'Feedback: {FEEDBACK}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
