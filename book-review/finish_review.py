"""Import feedback and finalize only current explicit approvals, including Excel prompts."""
from pathlib import Path
import argparse, json, sys

if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
from server import save_feedback, read_feedback, finalize_current
from finalization import Finalizer

ROOT=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--feedback',type=Path,help='Downloaded feedback JSON; omitted uses local feedback')
    parser.add_argument('--apply-approved',action='store_true',help='Save current approved original PNGs and complete English prompts in Excel')
    args=parser.parse_args()
    if args.feedback:save_feedback(json.loads(args.feedback.read_text(encoding='utf-8-sig')))
    feedback=read_feedback();wave=json.loads((ROOT/'dist'/'wave.json').read_text(encoding='utf-8'))
    mapping={s['id']:{i['id']:i for i in s['ideas']} for s in wave['sentences']}
    finalizer=Finalizer(ROOT)
    finalizations=finalize_current() if args.apply_approved else finalizer.inspect(feedback)
    approved=[];revise=[];revision_requests=[];revise_all=[];custom_ideas=[];rejected=[];batch_requests=[]
    for r in feedback.get('records',[]):
        if r['sentenceId'] not in mapping or r.get('waveId',feedback.get('waveId'))!=wave['id']:continue
        sid=r['sentenceId']; status=r['status']
        if status in ('revise_all','custom_idea','rejected') and r.get('batchRequest'):batch_requests.append(r['batchRequest'])
        if status=='revise':
            revise.append(sid)
            revision_requests.append({'sentenceId':sid,**(r.get('revisionRequest') or {'baseIdeaId':r['chosenIdeaId'],'comment':r.get('ideaNotes',{}).get(r['chosenIdeaId'],'')}),'progress':r.get('revisionProgress'),'note':r.get('note','')})
        if status=='revise_all':revise_all.append(sid)
        if status=='custom_idea':
            batch=r.get('batchRequest') or {}
            custom_ideas.append({'sentenceId':sid,'customIdea':batch.get('customIdea',r['customIdea']),'requestedVariants':r['requestedVariants'],'note':batch.get('comment',r.get('note',''))})
        if status=='rejected':rejected.append(sid)
        if status!='approved':continue
        candidate=mapping[sid].get(r['chosenIdeaId'])
        if not candidate:raise ValueError('Approved candidate unavailable')
        result=next((x for x in finalizations if x['sentenceId']==sid and x['ideaId']==candidate['id']),{})
        chosen={'sentenceId':sid,'ideaId':candidate['id'],**result}
        approved.append(chosen)
    report={'approved':approved,'finalizations':finalizations,'pendingFinalization':[r for r in finalizations if r['status']!='finalized'],'revise':revise,'revision_requests':revision_requests,'revise_all':revise_all,'batch_requests':batch_requests,'custom_ideas':custom_ideas,'retry':rejected,'copied':args.apply_approved and bool(approved) and all(r.get('status')=='finalized' for r in approved)}
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
