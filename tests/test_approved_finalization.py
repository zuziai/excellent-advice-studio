"""Isolated fixtures: this never calls the real Excel writer or changes book images."""
from pathlib import Path
import base64, copy, hashlib, json, sys, tempfile, unittest

WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE / 'book-review'))
from finalization import Finalizer, atomic_json, digest, prompt_cell_hash
import server

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jhCkAAAAASUVORK5CYII=')
PROMPT = 'Create a complete square watercolor book illustration.\n\nUse round heads and neutral balanced bodies.  The character learns to inspect and fix their own mistake, and the final panel shows the benefit of that change.'

class FinalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='approved-finalization-fixture-', dir=WORKSPACE / 'review-data')
        self.root = Path(self.temp.name).resolve()
        assert self.root.is_relative_to((WORKSPACE / 'review-data').resolve())
        self.project = self.root / 'book-review'
        self.art = self.project / 'dist' / 'art'
        self.art.mkdir(parents=True)
        (self.root / 'Images').mkdir()
        self.wave = {'id':'fixture-wave', 'sentences':[{'id':151, 'ideas':[{'id':'151-test-v2', 'image':'art/151-test-v2.png', 'version':2}, {'id':'151-other-v3','image':'art/151-other-v3.png','version':3}]}, {'id':152,'ideas':[{'id':'152-test-v2','image':'art/152-test-v2.png','version':2}]}]}
        for sentence in self.wave['sentences']:
            for idea in sentence['ideas']:
                (self.project / 'dist' / idea['image']).write_bytes(PNG + idea['id'].encode())
        atomic_json(self.project / 'dist' / 'wave.json', self.wave)
        self.feedback = {'format':'excellent-advice-feedback','version':1,'waveId':self.wave['id'],'records':[self.record(151,'151-test-v2','approved'),self.record(152,'152-test-v2','revise')]}
        self.manifest = {'jobs':[{'sentenceId':151,'ideaId':i,'prompt':PROMPT,'imageHash':digest(self.art/(i+'.png'))} for i in ('151-test-v2','151-other-v3')]}
        atomic_json(self.root / 'review-data' / 'finalization-2026-10-10' / 'approved-prompts.json',self.manifest)
        self.calls = []
        def writer(jobs):
            self.calls.append(copy.deepcopy(jobs))
            return {'saved':True,'jobs':[{'sentenceId':j['sentenceId'],'ideaId':j['ideaId'],'row':j['sentenceId']+1,'column':'D','workbookPath':str(self.root/'fixture.xlsx'),'sourcePromptSha256':j['promptSha256'],'promptSha256':prompt_cell_hash(j['prompt'])} for j in jobs]}
        self.writer = writer
        self.finalizer = Finalizer(self.project, writer)
        self.original_server = server.PROJECT,server.DATA,server.FEEDBACK,server.Finalizer
        server.PROJECT,server.DATA,server.FEEDBACK = self.project,self.root/'review-data',self.root/'review-data'/'feedback.json'
        server.Finalizer = lambda project: Finalizer(project,self.writer)

    def tearDown(self):
        server.PROJECT,server.DATA,server.FEEDBACK,server.Finalizer = self.original_server
        self.temp.cleanup()

    def record(self,sid,cid,status):
        return {'sentenceId':sid,'waveId':'fixture-wave','status':status,'chosenIdeaId':cid,'ideaNotes':{cid:'keep this exact comment'},'note':'keep sentence note','updatedAt':'2026-10-10T10:00:00Z'}

    def test_approval_original_bytes_and_repeat_are_idempotent(self):
        results=self.finalizer.finalize(self.feedback)
        self.assertEqual([r['status'] for r in results],['finalized'])
        self.assertEqual((self.root/'Images'/'151.png').read_bytes(),(self.art/'151-test-v2.png').read_bytes())
        self.assertFalse((self.root/'Images'/'152.png').exists())
        self.assertEqual(self.calls[0][0]['prompt'],PROMPT)
        self.assertEqual(results[0]['excel']['column'],'D')
        self.assertNotEqual(results[0]['sourcePromptSha256'],results[0]['promptCellSha256'])
        self.finalizer.finalize(self.feedback)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(len(self.finalizer.ledger()['entries']),1)
        state=json.loads(self.finalizer.project_state_path.read_text())
        self.assertEqual(len(state['approved']),1)
        self.assertEqual(self.finalizer.inspect(self.feedback)[0]['status'],'finalized')

    def test_previous_prompt_column_is_rejected(self):
        def wrong_column(jobs):
            result=self.writer(jobs)
            for job in result['jobs']: job['column']='C'
            return result
        results=Finalizer(self.project,wrong_column).finalize(self.feedback)
        self.assertEqual(results[0]['status'],'pending')
        self.assertFalse((self.root/'Images'/'151.png').exists())

    def test_new_approval_backs_up_previous_bytes_and_preserves_history(self):
        self.finalizer.finalize(self.feedback)
        previous=(self.root/'Images'/'151.png').read_bytes()
        self.feedback['records'][0]['chosenIdeaId']='151-other-v3'
        results=self.finalizer.finalize(self.feedback)
        self.assertEqual(results[0]['status'],'finalized')
        self.assertEqual((self.root/'Images'/'151.png').read_bytes(),(self.art/'151-other-v3.png').read_bytes())
        ledger=self.finalizer.ledger()
        self.assertEqual(len(ledger['entries']),2)
        backup=Path(ledger['entries'][-1]['backupPath'])
        self.assertEqual(backup.read_bytes(),previous)
        self.assertEqual(len(json.loads(self.finalizer.project_state_path.read_text())['approved']),2)

    def test_revise_and_historical_or_old_wave_approval_never_finalize(self):
        r=self.feedback['records'][0]
        r['status']='revise';r['history']=[{'status':'approved','chosenIdeaId':'151-test-v2'}]
        self.assertEqual(self.finalizer.finalize(self.feedback),[])
        self.assertFalse(self.calls)
        r['status']='approved';r['waveId']='previous-wave'
        self.assertEqual(self.finalizer.finalize(self.feedback),[])
        self.assertFalse((self.root/'Images'/'151.png').exists())

    def test_missing_standalone_prompt_stays_pending_and_edit_prompt_is_rejected(self):
        atomic_json(self.root/'review-data'/'finalization-2026-10-10'/'approved-prompts.json',{'jobs':[]})
        atomic_json(self.root/'review-data'/'151-test-v2.metadata.json',{'sha256':digest(self.art/'151-test-v2.png'),'generation':{'mode':'edit'},'prompt':PROMPT,'parentIdeaId':'151-test-v1'})
        results=self.finalizer.finalize(self.feedback)
        self.assertEqual(results[0]['status'],'pending')
        self.assertFalse(self.calls)
        self.assertFalse((self.root/'Images'/'151.png').exists())

    def test_excel_lock_keeps_feedback_and_previous_png_without_final_claim(self):
        previous=PNG+b'previous approved original'
        (self.root/'Images'/'151.png').write_bytes(previous)
        def locked(jobs): raise PermissionError('Fixture workbook is locked')
        self.writer=locked
        result=server.save_feedback(copy.deepcopy(self.feedback),apply_approved=True)
        self.assertEqual(result['finalizations'][0]['status'],'pending')
        self.assertEqual((self.root/'Images'/'151.png').read_bytes(),previous)
        saved=json.loads(server.FEEDBACK.read_text(encoding='utf-8'))
        self.assertEqual(saved['records'][0]['status'],'approved')
        self.assertEqual(saved['records'][0]['ideaNotes'],self.feedback['records'][0]['ideaNotes'])
        self.assertFalse(self.finalizer.project_state_path.exists())

    def test_server_preserves_previous_approval_when_changed_to_revision(self):
        server.save_feedback(copy.deepcopy(self.feedback),apply_approved=True)
        approved_bytes=(self.root/'Images'/'151.png').read_bytes()
        payload=copy.deepcopy(self.feedback);payload['records'][0]['status']='revise';payload['records'][0]['updatedAt']='2026-10-10T11:00:00Z'
        result=server.save_feedback(payload,apply_approved=True)
        self.assertEqual(result['finalizations'],[])
        r=next(r for r in result['records'] if r['sentenceId']==151)
        self.assertEqual(r['history'][-1]['status'],'approved')
        self.assertEqual((self.root/'Images'/'151.png').read_bytes(),approved_bytes)
        self.assertEqual(len(self.calls),1)

    def test_repair_missing_png_does_not_duplicate_approval_history(self):
        self.finalizer.finalize(self.feedback)
        (self.root/'Images'/'151.png').unlink()
        self.finalizer.finalize(self.feedback)
        self.assertEqual(len(self.finalizer.ledger()['entries']),1)
        self.assertEqual(len(json.loads(self.finalizer.project_state_path.read_text())['approved']),1)

if __name__=='__main__':unittest.main(verbosity=2)
