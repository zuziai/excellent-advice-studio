'use strict';
const $ = (id) => document.getElementById(id);
const STORAGE_KEY = 'excellent-advice-review-v1';
const LOCAL_ORIGIN = ['127.0.0.1','localhost'].includes(location.hostname);
let localDisconnected = false;
const state = {wave:null, sentenceIndex:0, ideaIndex:0, feedback:{}, customPanels:{}, local:false, localToken:null, storage:true, saveTimer:null, saveChain:Promise.resolve(), revision:0, syncedRevision:0, wavePoll:null, refreshingWave:false, finalizations:{}, finalizing:{}, approvalDownloads:new Set()};
const imageHistory = {key:null, versions:[], selectedId:null, loading:false, error:false, serial:0, cache:new Map()};
const labels = {pending:'در انتظار بررسی',approved:'انتخاب نهایی',revise:'نیاز به ویرایش',revise_all:'ویرایش همهٔ ایده‌ها',custom_idea:'۵ طرح از ایدهٔ شما',rejected:'ساخت دوبارهٔ ایده‌ها'};
const faNumber = (n) => Number(n).toLocaleString('fa-IR');
const escapeHTML = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sentence = () => state.wave.sentences[state.sentenceIndex];
const idea = () => sentence().ideas[state.ideaIndex];
const downloadName = (i) => `${i.id}.${i.image.split('?')[0].split('.').pop()}`;
const imageDimensions = (i) => `${faNumber(i.width)} × ${faNumber(i.height)} پیکسل`;
function downloadHref(i){
  const original=new URL(i.image,location.href);
  return state.local&&original.origin===location.origin&&/^\/art\/[A-Za-z0-9_.-]+\.(png|jpe?g|webp)$/i.test(original.pathname)
    ?`/download/${encodeURIComponent(original.pathname.split('/').pop())}`:i.image;
}
function applyFinalizationResults(results,allowDownload=false){
  for(const result of results||[]){
    const r=state.feedback[result.sentenceId];
    if(!r||r.status!=='approved'||r.chosenIdeaId!==result.ideaId)continue;
    state.finalizations[result.sentenceId]=result;
    if(allowDownload&&result.status==='finalized'&&state.approvalDownloads.has(result.ideaId)){
      const current=state.wave.sentences.find(s=>s.id===result.sentenceId)?.ideas.find(i=>i.id===result.ideaId);
      if(current){const a=document.createElement('a');a.href=downloadHref(current);a.download=downloadName(current);a.click();a.remove();state.approvalDownloads.delete(result.ideaId);}
    }
  }
  if(state.wave&&$('viewer').open)drawFinalizationActivity();
}
function drawFinalizationActivity(){
  const r=record(),i=idea(),active=!viewingPreviousVersion()&&r.status==='approved'&&r.chosenIdeaId===i.id;
  $('finalization-activity').hidden=!active;
  if(!active)return;
  const result=state.finalizations[sentence().id],matches=result?.ideaId===i.id,busy=!!state.finalizing[sentence().id],done=matches&&result.status==='finalized';
  $('finalization-spinner').hidden=!busy;$('retry-finalization').hidden=busy||done||!state.local;
  $('finalization-title').textContent=busy?'در حال ذخیرهٔ تصویر اصلی و پرامپت…':done?'ذخیرهٔ نهایی کامل شد':'انتخاب ثبت شد؛ ذخیرهٔ نهایی در انتظار تکمیل است';
  $('finalization-description').textContent=busy?'تصویر همین نسخه در Images و پرامپت کامل انگلیسی در ستون D اکسل ثبت می‌شود.':done?result.messageFa:!state.local?'انتخاب در این مرورگر ذخیره شده است. برای ذخیرهٔ نهایی کتاب، ارتباط با سرور محلی باید برقرار باشد.':matches&&result.messageFa?result.messageFa:'نظرها حفظ شده‌اند. برای ذخیرهٔ تصویر و پرامپت، دوباره تلاش کنید.';
}
async function refreshFinalizationStatus(){
  if(!state.local)return;
  const response=await fetch('/api/finalizations',{cache:'no-store'});
  if(response.ok){const data=await response.json();applyFinalizationResults(data.finalizations,false);}
}
async function retryFinalization(){
  const s=sentence(),r=record();if(!state.local||r.status!=='approved'||state.finalizing[s.id])return;
  if(state.finalizations[s.id]?.ideaId!==r.chosenIdeaId||state.finalizations[s.id]?.status!=='finalized')state.approvalDownloads.add(r.chosenIdeaId);
  state.finalizing[s.id]=true;drawFinalizationActivity();
  try{
    await state.saveChain;
    if(state.syncedRevision<state.revision)await flushLocal();
    if(state.finalizations[s.id]?.ideaId===r.chosenIdeaId&&state.finalizations[s.id].status==='finalized')return;
    const response=await fetch('/api/finalize',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':state.localToken},body:JSON.stringify({sentenceId:s.id,ideaId:r.chosenIdeaId})});
    if(!response.ok)throw new Error('Finalization unavailable');
    const data=await response.json();applyFinalizationResults(data.finalizations,true);
  }catch{state.finalizations[s.id]={sentenceId:s.id,ideaId:r.chosenIdeaId,status:'pending',messageFa:'نظرها حفظ شده‌اند؛ ارتباط برای ذخیرهٔ نهایی برقرار نشد. دوباره تلاش کنید.'};showLocalConnectionProblem();}
  finally{delete state.finalizing[s.id];if(sentence().id===s.id&&$('viewer').open)drawFinalizationActivity();}
}
function record(s=sentence()) {return state.feedback[s.id] ||= {sentenceId:s.id,waveId:state.wave.id,candidateIds:s.ideas.map(i=>i.id),status:'pending',chosenIdeaId:null,ideaNotes:{},note:'',customIdea:'',requestedVariants:null,updatedAt:null};}
const candidateVersion = (i) => i.version||Number(i.id.match(/-v(\d+)$/)?.[1])||1;
const displayedIdea = () => imageHistory.versions.find(i=>i.id===imageHistory.selectedId)||idea();
const viewingPreviousVersion = () => !!state.wave&&displayedIdea().id!==idea().id;
function resetImageHistory(){imageHistory.key=null;imageHistory.versions=[];imageHistory.selectedId=null;imageHistory.loading=false;imageHistory.error=false;imageHistory.serial++;}
function prepareImageHistory(){
  const current=idea(),key=`${state.wave.id}:${current.id}`;
  if(imageHistory.key===key)return;
  resetImageHistory();imageHistory.key=key;imageHistory.selectedId=current.id;imageHistory.versions=[current];
  if(imageHistory.cache.has(key)){imageHistory.versions=imageHistory.cache.get(key);return;}
  void loadImageHistory();
}
async function loadImageHistory(){
  const key=imageHistory.key,current=idea(),serial=++imageHistory.serial;
  imageHistory.loading=true;imageHistory.error=false;drawImageHistory();
  try{
    const response=await fetch(`/api/image-history?ideaId=${encodeURIComponent(current.id)}`,{cache:'no-store'});
    if(!response.ok)throw new Error('Image history unavailable');
    const data=await response.json();
    if(data.currentIdeaId!==current.id||!Array.isArray(data.versions))throw new Error('Invalid image history');
    const ids=new Set(),versions=data.versions.filter(i=>i&&typeof i.id==='string'&&typeof i.image==='string'&&!ids.has(i.id)&&ids.add(i.id)).map(i=>i.id===current.id?current:i);
    if(!ids.has(current.id))versions.push(current);
    if(imageHistory.key!==key||imageHistory.serial!==serial)return;
    imageHistory.versions=versions;imageHistory.cache.set(key,versions);
  }catch{
    if(imageHistory.key!==key||imageHistory.serial!==serial)return;
    imageHistory.error=true;
  }finally{
    if(imageHistory.key===key&&imageHistory.serial===serial){imageHistory.loading=false;drawImageHistory();}
  }
}
function drawImageHistory(){
  if(!state.wave||!imageHistory.key)return;
  const current=idea(),versions=imageHistory.versions,index=Math.max(0,versions.findIndex(i=>i.id===imageHistory.selectedId)),historical=viewingPreviousVersion();
  $('image-history').setAttribute('aria-busy',String(imageHistory.loading));
  $('history-select').innerHTML=versions.map(i=>`<option value="${escapeHTML(i.id)}">نسخهٔ ${faNumber(candidateVersion(i))} · ${i.id===current.id?'فعلی':'پیشین'}</option>`).join('');
  $('history-select').value=imageHistory.selectedId;
  $('history-select').disabled=imageHistory.loading||versions.length<2;
  $('history-previous').disabled=imageHistory.loading||index===0;
  $('history-next').disabled=imageHistory.loading||index===versions.length-1;
  $('history-status').textContent=imageHistory.loading?'در حال دریافت فهرست نسخه‌ها…':imageHistory.error?'فهرست نسخه‌های پیشین دریافت نشد؛ تصویر فعلی در دسترس است.':versions.length>1?`${faNumber(versions.length)} نسخه؛ تصویر هر نسخه با انتخاب شما باز می‌شود.`:'این تصویر هنوز نسخهٔ پیشین ندارد.';
  $('history-retry').hidden=!imageHistory.error;
  $('historical-preview').hidden=!historical;
}
function previewImageVersion(id){
  if(!imageHistory.versions.some(i=>i.id===id))return;
  imageHistory.selectedId=id;drawViewer();
}
function stepImageVersion(delta){
  const index=imageHistory.versions.findIndex(i=>i.id===imageHistory.selectedId),next=imageHistory.versions[index+delta];
  if(next)previewImageVersion(next.id);
}
function revisionStatus(r){return r.status==='revise'&&r.revisionRequest?(['queued','in_progress','failed'].includes(r.revisionProgress?.status)&&r.revisionProgress.requestId===r.revisionRequest.requestId?r.revisionProgress.status:'queued'):null;}
function decisionLabel(r){return revisionStatus(r)?{queued:'در انتظار شروع ویرایش',in_progress:'در حال ویرایش',failed:'ویرایش انجام نشد'}[revisionStatus(r)]:labels[r.status];}
function choiceText(i,r){return r.status==='revise_all'?'✓ ویرایش کلی درخواست شده':r.chosenIdeaId===i.id?(r.status==='approved'?'✓ انتخاب نهایی':decisionLabel(r)):'';}
function resultForRequest(wave,request){return wave.sentences.flatMap(s=>s.ideas).find(i=>i.revisionRequestId===request.requestId&&i.parentIdeaId===request.baseIdeaId&&candidateVersion(i)>request.baseVersion);}
function resultForBatch(wave,request){
  const s=wave.sentences.find(s=>s.id===request.sentenceId),results=s?.ideas.filter(i=>i.batchRequestId===request.requestId)||[];
  if(results.length!==request.requestedVariants)return [];
  if(request.status==='revise_all'&&!request.baseCandidateIds.every(id=>results.some(i=>i.parentIdeaId===id)))return [];
  return results;
}
function drawWaveSummary(){
  $('wave-title').textContent=state.wave.titleFa||state.wave.title;
  $('wave-summary').textContent=state.wave.summaryFa||`${faNumber(state.wave.sentences.length)} جمله · ${faNumber(state.wave.sentences.reduce((n,s)=>n+s.ideas.length,0))} ایده`;
}
function batchMatchesDraft(r){return r.batchRequest?.status===r.status&&r.batchRequest.comment===(r.note||'').trim()&&(r.status!=='custom_idea'||r.batchRequest.customIdea===(r.customIdea||'').trim());}
function drawBatchDraftState(){
  const r=record(),matches=batchMatchesDraft(r);
  if(r.status==='revise_all'){
    $('revise-all').textContent=matches?'✓ ویرایش همهٔ ایده‌ها ثبت شد':'ثبت تغییرات کلی جدید';
    $('overall-feedback-message').textContent=matches?'درخواست ثبت شد؛ برای شروع، در همین چت خبر بدهید. یادداشت‌های جداگانهٔ هر ایده هم حفظ شده‌اند.':'توضیح تازه پیش‌نویس است؛ برای ارسال آن «ثبت تغییرات کلی جدید» را بزنید.';
  }
  if(r.status==='custom_idea'){
    $('submit-custom-idea').textContent=matches?'✓ درخواست ۵ طرح ثبت شد':'ثبت تغییرات جدیدِ ایدهٔ من';
    $('custom-idea-status').textContent=matches?'درخواست ثبت شد: پنج طراحی متفاوت بر پایهٔ ایدهٔ شما. برای شروع، در همین چت خبر بدهید.':'متن تازه پیش‌نویس است؛ برای ارسال، دکمهٔ ثبت تغییرات جدید را بزنید.';
  }
}
function drawRevisionActivity(){
  const r=record(),i=idea(),active=!viewingPreviousVersion()&&r.status==='revise'&&r.chosenIdeaId===i.id&&!!r.revisionRequest,status=active?revisionStatus(r):null;
  $('revision-activity').hidden=!active;$('revision-activity').className='revision-activity '+(status||'');
  $('revision-spinner').hidden=status!=='in_progress';$('edit-hint').hidden=!active||status==='in_progress';
  document.querySelector('.art-pane').classList.toggle('is-processing',status==='in_progress');
  document.querySelector('.art-pane').setAttribute('aria-busy',String(status==='in_progress'));
  if(!active)return;
  const version=faNumber(candidateVersion(i));
  $('revision-activity-title').textContent={queued:`درخواست نسخهٔ ${version} ثبت شد؛ در انتظار شروع`,in_progress:`در حال ویرایش نسخهٔ ${version}`,failed:'ویرایش انجام نشد'}[status];
  $('revision-activity-description').textContent=status==='queued'?'برای شروع، در همین چت خبر بدهید. ویرایش هنوز شروع نشده است.':status==='in_progress'?(r.revisionProgress?.message||'ویرایش شما شروع شده است. پس از آماده‌شدن، تصویر تازه در همین صفحه نمایش داده می‌شود.'):(r.revisionProgress?.message||'این تلاش کامل نشد. توضیحات را بررسی کنید و دوباره درخواست را ثبت کنید.');
}
async function updateRevisionProgress(input){
  if(!['in_progress','failed'].includes(input?.status)||typeof input.requestId!=='string')throw new Error('Invalid progress update');
  if(input.message!==undefined&&(typeof input.message!=='string'||input.message.length>500))throw new Error('Invalid progress message');
  const r=Object.values(state.feedback).find(r=>r.status==='revise'&&r.revisionRequest?.requestId===input.requestId);
  if(!r)throw new Error('Request is no longer active');
  const now=new Date().toISOString(),previous=r.revisionProgress?.requestId===input.requestId?r.revisionProgress:{};
  r.revisionProgress={requestId:input.requestId,status:input.status,message:input.message||'',updatedAt:now,startedAt:previous.startedAt||(input.status==='in_progress'?now:null),finishedAt:input.status==='failed'?now:null};r.updatedAt=now;
  persist();drawSentence();if($('viewer').open)drawEditState();await flushLocal();return {requestId:input.requestId,status:input.status};
}
async function refreshPublishedWave(){
  if(state.refreshingWave||document.visibilityState==='hidden'||!state.wave)return;
  state.refreshingWave=true;
  try{
    const response=await fetch('wave.json',{cache:'no-store'});if(!response.ok)throw new Error('Wave unavailable');
    if(localDisconnected&&LOCAL_ORIGIN){
      const session=await fetch('/api/feedback',{cache:'no-store'});
      if(!session.ok)throw new Error('Local review unavailable');
      const remote=await session.json();
      if(remote.localReview!==true||typeof remote.token!=='string')throw new Error('Local review unavailable');
      state.local=true;state.localToken=remote.token;localDisconnected=false;$('connection-alert').hidden=true;mergeRecords(remote.records,{remote:true});applyFinalizationResults(remote.finalizations,false);updateFeedbackInstructions();drawNavigation();
      await flushLocal();
    }
    const next=await response.json();if(!next.sentences?.length||next.sentences.some(s=>!s.ideas?.length))return;
    if(next.id===state.wave.id){await refreshFinalizationStatus();return;}
    const safeToApply=()=>Object.values(state.feedback).every(r=>{
      const s=next.sentences.find(s=>s.id===r.sentenceId);
      if(r.status==='revise'&&r.revisionRequest)return !!s?.ideas.some(i=>i.id===r.chosenIdeaId)||!!resultForRequest(next,r.revisionRequest);
      if(r.batchRequest&&['revise_all','rejected','custom_idea'].includes(r.status))return !!s&&(JSON.stringify(s.ideas.map(i=>i.id))===JSON.stringify(r.batchRequest.baseCandidateIds)||resultForBatch(next,r.batchRequest).length>0);
      return true;
    });
    if(!safeToApply())return;
    const currentIds=new Set(state.wave.sentences.flatMap(s=>s.ideas.map(i=>i.id)));
    const results=next.sentences.flatMap(s=>s.ideas).filter(i=>!currentIds.has(i.id));
    await Promise.all(results.map(async i=>{const img=new Image();img.src=i.image;await img.decode();}));
    if(!safeToApply())return;
    const selectedSentence=sentence().id,selectedSource=idea().sourceCandidate,saved=structuredClone(Object.values(state.feedback));
    state.wave=next;state.feedback={};mergeRecords(saved);state.sentenceIndex=Math.max(0,next.sentences.findIndex(s=>s.id===selectedSentence));state.ideaIndex=Math.max(0,sentence().ideas.findIndex(i=>i.sourceCandidate===selectedSource));
    persist();drawWaveSummary();drawSentence();if($('viewer').open)drawViewer();await refreshFinalizationStatus();toast('تصاویر تازه آماده‌اند؛ صفحه به‌روز شد.');
  }catch{showLocalConnectionProblem();}finally{state.refreshingWave=false;}
}
function showLocalConnectionProblem(){
  if(!LOCAL_ORIGIN)return;
  localDisconnected=true;$('connection-alert').hidden=false;
  saveStatus('ارتباط با پوشهٔ تصاویر قطع شده است');
}
function updateFeedbackInstructions(){
  $('feedback-instructions').textContent=state.local?'نظرها خودکار در پوشهٔ بررسی ذخیره می‌شوند. انتخاب نهایی، تصویر اصلی را در Images و پرامپت کامل انگلیسی را در ستون D اکسل ثبت می‌کند و دانلود همین نسخه را آغاز می‌کند. برای شروع ویرایش تصویر، در همین چت خبر بدهید. دانلود بازخورد نسخهٔ پشتیبان شماست.':'نظرها در این مرورگر ذخیره می‌شوند. پس از ثبت درخواست، در همین چت خبر بدهید تا آن را از صفحهٔ باز شما بخوانم و ویرایش را شروع کنم. تولید تصویر خودکار نیست؛ دانلود و ارسال بازخورد هم راه جایگزین است.';
}
let toastTimer;
function toast(message){$('toast').textContent=message;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),3600);}
function documentData(){return {format:'excellent-advice-feedback',version:1,waveId:state.wave.id,styleVersion:state.wave.styleVersion||null,exportedAt:new Date().toISOString(),records:Object.values(state.feedback),sentences:state.wave.sentences.map(s=>({id:s.id,english:s.english,persian:s.persian,ideas:s.ideas.map(i=>({id:i.id,title:i.title,titleFa:i.titleFa,image:i.image,version:candidateVersion(i),parentIdeaId:i.parentIdeaId||null,revisionRequestId:i.revisionRequestId||null,batchRequestId:i.batchRequestId||null}))}))};}
function saveStatus(message){$('save-state').textContent=message;}
function persist(){
  const r=record();r.updatedAt=new Date().toISOString();state.revision++;
  try {localStorage.setItem(STORAGE_KEY,JSON.stringify({version:1,records:Object.values(state.feedback)}));state.storage=true;} catch {state.storage=false;}
  if(state.local){saveStatus('در حال ذخیرهٔ نظرها…');clearTimeout(state.saveTimer);state.saveTimer=setTimeout(flushLocal,450);}
  else saveStatus(state.storage?'در این مرورگر ذخیره شد':'برای نگه‌داشتن نظرها، بازخورد را دانلود کنید');
}
async function flushLocal(){
  clearTimeout(state.saveTimer);
  if(!state.local)return;
  const payload=documentData(), revision=state.revision;
  state.saveChain=state.saveChain.catch(()=>{}).then(async()=>{
    const approved=payload.records.filter(r=>r.status==='approved');
    for(const r of approved)state.finalizing[r.sentenceId]=true;
    if($('viewer').open)drawFinalizationActivity();
    try{
      const response=await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':state.localToken},body:JSON.stringify(payload)});
      if(!response.ok)throw new Error('Could not save');
      const result=await response.json();applyFinalizationResults(result.finalizations,true);state.syncedRevision=Math.max(state.syncedRevision,revision);
      saveStatus(state.syncedRevision===state.revision?'در پوشهٔ بررسی ذخیره شد':'در حال ذخیرهٔ نظرها…');
    }catch{showLocalConnectionProblem();saveStatus(state.storage?'ارتباط قطع شد؛ نظرها در مرورگر ذخیره‌اند':'ارتباط قطع شد؛ بازخورد را دانلود کنید');}
    finally{for(const r of approved)delete state.finalizing[r.sentenceId];if($('viewer').open)drawFinalizationActivity();}
  });return state.saveChain;
}
function drawNavigation(){
  $('sentence-nav').innerHTML=state.wave.sentences.map((s,n)=>`<button class="sentence-item ${n===state.sentenceIndex?'active':''}" data-sentence="${n}" ${n===state.sentenceIndex?'aria-current="true"':''}><span class="number">${faNumber(s.id)}</span><span><strong>${escapeHTML(s.shortTitleFa||s.shortTitle||s.persian)}</strong><small>${decisionLabel(record(s))}</small></span></button>`).join('');
  $('sentence-nav').querySelectorAll('[data-sentence]').forEach(b=>b.addEventListener('click',()=>switchSentence(Number(b.dataset.sentence))));
}
function drawSentence(){
  const s=sentence(),r=record();
  $('sentence-number').textContent=`جملهٔ ${faNumber(s.id)} از ${faNumber(state.wave.totalSentences)}`;
  $('sentence-en').textContent=s.english;$('sentence-fa').textContent=s.persian;
  $('decision-badge').textContent=decisionLabel(r);$('decision-badge').className='badge '+r.status;
  $('sentence-note').value=r.note||'';
  $('revise-all').textContent=r.status==='revise_all'?(batchMatchesDraft(r)?'✓ ویرایش همهٔ ایده‌ها ثبت شد':'ثبت تغییرات کلی جدید'):'درخواست ویرایش همهٔ ایده‌ها';
  $('clear-overall-revision').hidden=r.status!=='revise_all';
  $('overall-feedback-message').hidden=r.status!=='revise_all';
  $('overall-feedback-message').textContent=r.status==='revise_all'?(batchMatchesDraft(r)?'درخواست ثبت شد؛ برای شروع، در همین چت خبر بدهید. یادداشت‌های جداگانهٔ هر ایده هم حفظ شده‌اند.':'توضیح تازه پیش‌نویس است؛ برای ارسال آن «ثبت تغییرات کلی جدید» را بزنید.'):'';
  $('custom-idea').value=r.customIdea||'';
  const customOpen=state.customPanels[s.id]??(!!r.customIdea||r.status==='custom_idea');
  $('custom-idea-panel').hidden=!customOpen;$('open-custom-idea').setAttribute('aria-expanded',String(customOpen));
  $('submit-custom-idea').textContent=r.status==='custom_idea'?(batchMatchesDraft(r)?'✓ درخواست ۵ طرح ثبت شد':'ثبت تغییرات جدیدِ ایدهٔ من'):'ثبت درخواست ۵ طرح از ایدهٔ من';
  $('clear-custom-request').hidden=r.status!=='custom_idea';
  $('custom-idea-status').hidden=r.status!=='custom_idea';
  $('custom-idea-status').textContent=r.status==='custom_idea'?(batchMatchesDraft(r)?'درخواست ثبت شد: پنج طراحی متفاوت بر پایهٔ ایدهٔ شما. برای شروع، در همین چت خبر بدهید.':'متن تازه پیش‌نویس است؛ برای ارسال، دکمهٔ ثبت تغییرات جدید را بزنید.'):'';
  document.querySelector('.gallery-heading h2').textContent=`${faNumber(s.ideas.length)} ایده برای این جمله`;
  $('ideas').innerHTML=s.ideas.map((i,n)=>`<article aria-busy="${r.chosenIdeaId===i.id&&revisionStatus(r)==='in_progress'}" class="idea-card ${r.chosenIdeaId===i.id&&revisionStatus(r)==='in_progress'?'is-processing':''} ${r.chosenIdeaId===i.id?'chosen':''} ${r.status==='revise_all'?'revision-requested':''}"><button class="image-button" data-idea="${n}" aria-label="بزرگ‌کردن ایدهٔ ${faNumber(n+1)}: ${escapeHTML(i.titleFa||i.title)}"><img src="${escapeHTML(i.image)}" alt="${escapeHTML(i.storyFa||i.alt||i.story)}" ${n>1?'loading="lazy"':''}><span class="image-label">${faNumber(n+1)}</span></button><div class="card-body">${candidateVersion(i)>1?`<span class="version-tag">نسخهٔ ${faNumber(candidateVersion(i))} · ویرایش‌شده</span>`:''}<h3>${escapeHTML(i.titleFa||i.title)}</h3><p>${escapeHTML(i.summaryFa||i.summary)}</p>${i.meaningFa?`<p class="card-meaning"><strong>پیام ایده:</strong> ${escapeHTML(i.meaningFa)}</p>`:''}<div class="card-footer"><button class="text-button" data-idea="${n}">دیدن تصویر بزرگ</button><button class="button edit-button" data-edit="${n}">درخواست ویرایش</button></div><a class="button secondary download-button card-download" href="${escapeHTML(downloadHref(i))}" download="${escapeHTML(downloadName(i))}" aria-label="دانلود نسخهٔ ${faNumber(candidateVersion(i))} ایدهٔ ${faNumber(n+1)} با کیفیت کامل" title="${escapeHTML(imageDimensions(i))}">دانلود نسخهٔ ${faNumber(candidateVersion(i))} با کیفیت کامل <small dir="ltr">${escapeHTML(imageDimensions(i))}</small></a><span class="choice-mark">${r.chosenIdeaId===i.id&&revisionStatus(r)==='in_progress'?'<span class="progress-spinner" aria-hidden="true"></span>':''}${escapeHTML(choiceText(i,r))}</span></div></article>`).join('');
  $('ideas').querySelectorAll('[data-idea]').forEach(b=>b.addEventListener('click',()=>openIdea(Number(b.dataset.idea))));
  $('ideas').querySelectorAll('[data-edit]').forEach(b=>b.addEventListener('click',()=>requestRevision(Number(b.dataset.edit))));
  drawNavigation();
}
function drawViewer(){
  prepareImageHistory();
  const s=sentence(),i=displayedIdea(),r=record(),historical=viewingPreviousVersion();
  drawImageHistory();
  $('viewer-counter').textContent=`جملهٔ ${faNumber(s.id)} · ایدهٔ ${faNumber(state.ideaIndex+1)} از ${faNumber(s.ideas.length)} · نسخهٔ ${faNumber(candidateVersion(i))}`;
  $('viewer-title').textContent=i.titleFa||i.title;$('viewer-sentence-id').textContent=`جملهٔ ${faNumber(s.id)}`;
  $('viewer-en').textContent=s.english;$('viewer-fa').textContent=s.persian;
  $('viewer-story').textContent=i.storyFa||i.story;$('viewer-meaning').textContent=i.meaningFa||'';
  document.querySelector('.meaning-explanation').hidden=!i.meaningFa;
  $('viewer-prompt').textContent=i.fullGenerationPromptEnglish||i.prompt||'پرامپت کامل در فایل‌های پروژه ذخیره شده است.';
  $('full-image').src=i.image;$('full-image').alt=i.storyFa||i.alt||i.story;
  $('viewer-download').href=downloadHref(i);$('viewer-download').download=downloadName(i);$('viewer-download').title=imageDimensions(i);$('viewer-download').textContent=`دانلود همین نسخه (${faNumber(candidateVersion(i))}) با کیفیت کامل`;
  $('viewer-version-status').hidden=historical||!i.parentIdeaId||(r.status==='revise'&&r.chosenIdeaId===i.id);
  $('viewer-version-status').textContent=i.parentIdeaId?`ویرایش شما آماده است؛ نسخهٔ ${faNumber(candidateVersion(i))}. ${i.revisionSummaryFa||''} می‌توانید بررسی، انتخاب نهایی یا دوباره ویرایش کنید.`:'';
  $('idea-note').value=r.ideaNotes[i.id]||'';
  for(const id of ['approve','revise','submit-revision','idea-note','viewer-reject','clear-decision','retry-finalization'])$(id).disabled=historical;
  $('image-scroll').classList.remove('zoomed');$('zoom').textContent='اندازهٔ واقعی';$('image-scroll').scrollTop=0;$('image-scroll').scrollLeft=0;
  $('approve').textContent=r.status==='approved'&&r.chosenIdeaId===i.id?'✓ انتخاب نهایی ثبت شد':'انتخاب نهایی';
  $('revise').textContent=candidateVersion(i)>1?'ویرایش دوبارهٔ تصویر':'ویرایش تصویر';
  $('edit-error').hidden=true;$('idea-note').removeAttribute('aria-invalid');
  drawEditState();
  $('viewer-decision').textContent=historical?'':r.status==='custom_idea'?'درخواست پنج طراحی متفاوت از ایدهٔ شما ثبت شده است.':r.status==='revise_all'?'ویرایش کلی برای همهٔ ایده‌ها ثبت شده است؛ این تصویر هم بر اساس نظر کلی شما اصلاح می‌شود.':r.chosenIdeaId===i.id?(r.status==='approved'?'این تصویر انتخاب نهایی شماست.':r.status==='revise'?'':''):r.status==='rejected'?'برای این جمله ایده‌های تازه می‌سازیم.':'';
  $('clear-decision').hidden=r.status==='pending';
  drawFinalizationActivity();
}
function openIdea(n){
  resetImageHistory();state.ideaIndex=n;drawViewer();if(!$('viewer').open)$('viewer').showModal();
  $('viewer').scrollTop=0;document.querySelector('.viewer-layout').scrollTop=0;document.querySelector('.review-pane').scrollTop=0;
  $('close-viewer').focus({preventScroll:true});
}
function requestRevision(n=state.ideaIndex){
  if(!$('viewer').open||n!==state.ideaIndex)openIdea(n);
  if(viewingPreviousVersion())return;
  $('idea-note').focus();
  $('idea-feedback').scrollIntoView({block:'nearest'});
}
function drawEditState(){
  if(viewingPreviousVersion()){
    $('submit-revision').textContent='ویرایش نسخهٔ فعلی';$('edit-draft-status').textContent='یادداشت نسخهٔ پیشین فقط برای مشاهده است. برای ثبت نظر به نسخهٔ فعلی برگردید.';drawRevisionActivity();return;
  }
  const r=record(),i=idea(),active=r.status==='revise'&&r.chosenIdeaId===i.id;
  const matches=active&&r.revisionRequest?.baseIdeaId===i.id&&r.revisionRequest.comment===($('idea-note').value||'').trim();
  $('submit-revision').textContent=matches&&revisionStatus(r)==='failed'?'ثبت دوبارهٔ درخواست':matches?'✓ درخواست ویرایش ثبت شد':active?'ثبت تغییرات جدید':'ثبت درخواست ویرایش';
  $('edit-draft-status').textContent=matches?'این تغییرات برای نسخهٔ فعلی ثبت شده‌اند.':active?'این متن پیش‌نویس است؛ برای ثبت تغییرات جدید، دکمهٔ زیر را بزنید.':'یادداشت خودکار ذخیره می‌شود؛ برای درخواست ویرایش، دکمهٔ زیر را بزنید.';
  drawRevisionActivity();
}
function createRevisionRequest(i,comment){return {requestId:crypto.randomUUID(),baseIdeaId:i.id,baseVersion:candidateVersion(i),comment:comment.trim(),submittedAt:new Date().toISOString()};}
function submitImageRevision(){
  if(viewingPreviousVersion())return;
  const r=record(),i=idea(),comment=$('idea-note').value.trim();
  if(!comment){$('edit-error').textContent='ابتدا تغییر مدنظر خود را بنویسید.';$('edit-error').hidden=false;$('idea-note').setAttribute('aria-invalid','true');$('idea-note').focus();return;}
  if(r.status==='revise'&&r.chosenIdeaId===i.id&&r.revisionRequest?.baseIdeaId===i.id&&r.revisionRequest.comment===comment&&revisionStatus(r)!=='failed'){toast(revisionStatus(r)==='in_progress'?'این درخواست در حال انجام است؛ نتیجه پس از آماده‌شدن نمایش داده می‌شود.':'این درخواست قبلاً ثبت شده است؛ برای شروع ویرایش در چت خبر بدهید.');return;}
  r.ideaNotes[i.id]=$('idea-note').value;
  setDecision('revise',i.id,createRevisionRequest(i,comment));
  $('submit-revision').focus({preventScroll:true});$('revision-activity').scrollIntoView({block:'nearest'});
}
function switchSentence(n){if(n<0||n>=state.wave.sentences.length)return;state.sentenceIndex=n;state.ideaIndex=0;drawSentence();if($('viewer').open)drawViewer();}
function stepIdea(delta){const length=sentence().ideas.length;state.ideaIndex=(state.ideaIndex+delta+length)%length;drawViewer();}
function setDecision(status,chosen=null,revisionRequest=null){
  const r=record();
  const overall=['revise_all','custom_idea','rejected'].includes(status);
  if(overall&&r.status===status&&batchMatchesDraft(r)){toast('این درخواست قبلاً ثبت شده است؛ برای شروع، در همین چت خبر بدهید.');return;}
  const newApproval=status==='approved'&&(r.status!=='approved'||r.chosenIdeaId!==chosen);
  if(r.status==='approved'&&(status!=='approved'||r.chosenIdeaId!==chosen))r.history=[...(Array.isArray(r.history)?r.history:[]),{status:r.status,chosenIdeaId:r.chosenIdeaId,updatedAt:r.updatedAt,waveId:r.waveId,ideaNotes:{...r.ideaNotes},note:r.note||''}];
  if(r.chosenIdeaId!==chosen||status!=='approved'){state.approvalDownloads.delete(r.chosenIdeaId);delete state.finalizations[sentence().id];}
  if(newApproval){state.approvalDownloads.add(chosen);state.finalizing[sentence().id]=state.local;}
  if(r.batchRequest)r.history=[...(Array.isArray(r.history)?r.history:[]),{status:r.status,chosenIdeaId:r.chosenIdeaId,batchRequest:r.batchRequest,updatedAt:r.updatedAt}];
  if(r.revisionRequest&&r.revisionRequest.requestId!==revisionRequest?.requestId)r.history=[...(Array.isArray(r.history)?r.history:[]),{status:r.status,chosenIdeaId:r.chosenIdeaId,revisionRequest:r.revisionRequest,revisionProgress:r.revisionProgress||null,updatedAt:r.updatedAt}];
  r.batchRequest=overall?{requestId:crypto.randomUUID(),sentenceId:sentence().id,status,baseCandidateIds:sentence().ideas.map(i=>i.id),comment:(r.note||'').trim(),ideaNotes:{...r.ideaNotes},customIdea:status==='custom_idea'?(r.customIdea||'').trim():'',requestedVariants:status==='custom_idea'?5:sentence().ideas.length,styleVersion:state.wave.styleVersion||null,submittedAt:new Date().toISOString()}:null;
  r.decisionIntent={id:crypto.randomUUID(),status,chosenIdeaId:chosen,submittedAt:new Date().toISOString()};
  r.revisionRequest=status==='revise'?revisionRequest:null;r.revisionProgress=revisionRequest?{requestId:revisionRequest.requestId,status:'queued',updatedAt:new Date().toISOString()}:null;r.status=status;r.chosenIdeaId=chosen;r.requestedVariants=status==='custom_idea'?5:null;persist();drawSentence();if($('viewer').open)drawViewer();
  const messages={approved:state.local?'انتخاب ثبت شد؛ در حال ذخیرهٔ تصویر و پرامپت…':'انتخاب در این مرورگر ثبت شد.',revise:'درخواست ذخیره شد؛ برای شروع ویرایش در چت خبر بدهید.',revise_all:'درخواست ویرایش همهٔ ایده‌های فعلی ذخیره شد.',custom_idea:'ایدهٔ شما و درخواست پنج طراحی متفاوت ذخیره شد.',pending:'انتخاب لغو شد؛ یادداشت‌ها باقی ماندند.',rejected:'همهٔ ایده‌ها رد شدند؛ ایده‌های تازه می‌سازیم.'};
  toast(messages[status]);
}
function submitCustomIdea(){
  const r=record();r.customIdea=$('custom-idea').value;
  if(!r.customIdea.trim()){$('custom-idea-error').textContent='ابتدا ایدهٔ خود را بنویسید.';$('custom-idea-error').hidden=false;$('custom-idea').setAttribute('aria-invalid','true');$('custom-idea').focus();return;}
  $('custom-idea-error').hidden=true;$('custom-idea').removeAttribute('aria-invalid');state.customPanels[sentence().id]=true;setDecision('custom_idea');
}
async function exportFeedback(){
  await flushLocal();const data=JSON.stringify(documentData(),null,2);
  const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`feedback-${state.wave.id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  toast('بازخورد دانلود شد. می‌توانید فایل را در همین چت بفرستید.');
}
function mergeRecords(records,{remote=false}={}){
  for(const raw of records||[]){
    const r=raw&&structuredClone(raw);
    if(!r||!Number.isInteger(r.sentenceId)||!Object.hasOwn(labels,r.status)||typeof r.ideaNotes!=='object'||r.ideaNotes===null||Array.isArray(r.ideaNotes))continue;
    if(r.customIdea!==undefined&&(typeof r.customIdea!=='string'||r.customIdea.length>10000))continue;
    if(r.status==='custom_idea'&&(!(r.batchRequest?.customIdea||r.customIdea)?.trim()||r.requestedVariants!==5||r.chosenIdeaId!==null))continue;
    const s=state.wave.sentences.find(s=>s.id===r.sentenceId);
    const changed=s&&((Array.isArray(r.candidateIds)&&JSON.stringify(r.candidateIds)!==JSON.stringify(s.ideas.map(i=>i.id)))||(r.chosenIdeaId&&!s.ideas.some(i=>i.id===r.chosenIdeaId)));
    const targetStillAvailable=s&&['approved','revise'].includes(r.status)&&s.ideas.some(i=>i.id===r.chosenIdeaId);
    if(changed&&!targetStillAvailable){
      r.history=[...(Array.isArray(r.history)?r.history:[]),{status:r.status,chosenIdeaId:r.chosenIdeaId,revisionRequest:r.revisionRequest||null,revisionProgress:r.revisionProgress||null,batchRequest:r.batchRequest||null,ideaNotes:{...r.ideaNotes},note:r.note,customIdea:r.customIdea||'',requestedVariants:r.requestedVariants||null,updatedAt:r.updatedAt}];
      r.status='pending';r.chosenIdeaId=null;r.revisionRequest=null;r.revisionProgress=null;r.batchRequest=null;r.requestedVariants=null;
      if(r.decisionIntent?.status!=='pending')delete r.decisionIntent;
      r.reviewMigration={automatic:true,appliedAt:new Date().toISOString()};
    }
    if(s){r.waveId=state.wave.id;r.candidateIds=s.ideas.map(i=>i.id);}
    if(s&&['approved','revise'].includes(r.status)&&!r.chosenIdeaId)continue;
    const prev=state.feedback[r.sentenceId];
    const explicitPending=r.status==='pending'&&r.decisionIntent?.status==='pending'&&r.decisionIntent?.chosenIdeaId===null;
    const previousExplicitPending=prev?.status==='pending'&&prev.decisionIntent?.status==='pending'&&prev.decisionIntent?.chosenIdeaId===null;
    const resolvedRevision=prev?.revisionRequest&&r.latestRevisionResult?.revisionRequestId===prev.revisionRequest.requestId;
    if(prev&&prev.status!=='pending'&&r.status==='pending'&&!explicitPending&&!resolvedRevision)continue;
    if(!prev||(remote&&prev.status==='pending'&&!previousExplicitPending)||(r.updatedAt||'')>(prev.updatedAt||''))state.feedback[r.sentenceId]=r;
  }
}
async function init(){
  try{
    const response=await fetch('wave.json',{cache:'no-store'});if(!response.ok)throw new Error('Wave unavailable');state.wave=await response.json();
    if(!state.wave.sentences?.length||state.wave.sentences.some(s=>!s.ideas?.length))throw new Error('Wave has no artwork');
    let browserRecords=[];
    try {const saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}');browserRecords=saved.records||[];}catch{state.storage=false;}
    try{
      const response=await fetch('/api/feedback',{cache:'no-store'});
      if(response.ok&&response.headers.get('Content-Type')?.includes('application/json')){
        const remote=await response.json();if(remote.localReview===true&&typeof remote.token==='string'){state.local=true;state.localToken=remote.token;mergeRecords(remote.records,{remote:true});applyFinalizationResults(remote.finalizations,false);}
      }
    }catch{}
    mergeRecords(browserRecords);
    drawWaveSummary();
    $('book-summary').textContent=`${faNumber(state.wave.totalSentences)} جملهٔ دوزبانه`;
    updateFeedbackInstructions();
    state.sentenceIndex=Math.max(0,state.wave.sentences.findIndex(s=>record(s).status!=='approved'));drawSentence();saveStatus(state.local?'در پوشهٔ بررسی ذخیره شد':state.storage?'در این مرورگر ذخیره شد':'برای نگه‌داشتن نظرها، بازخورد را دانلود کنید');
    if(state.local)await flushLocal();
    registerReviewTools();state.wavePoll=setInterval(refreshPublishedWave,10000);window.addEventListener('pagehide',()=>clearInterval(state.wavePoll),{once:true});
  }catch(error){showLocalConnectionProblem();saveStatus('صفحهٔ بررسی باز نشد');$('ideas').innerHTML='<p>اطلاعات تصاویر بارگذاری نشد. صفحه را تازه کنید یا پیوند بررسی را دوباره باز کنید.</p>';console.error(error);}
}
$('retry-connection').addEventListener('click',()=>location.reload());
$('retry-finalization').addEventListener('click',retryFinalization);
$('close-viewer').addEventListener('click',()=>$('viewer').close());
$('viewer').addEventListener('close',resetImageHistory);
$('history-select').addEventListener('change',e=>previewImageVersion(e.target.value));
$('history-previous').addEventListener('click',()=>stepImageVersion(-1));
$('history-next').addEventListener('click',()=>stepImageVersion(1));
$('history-current').addEventListener('click',()=>previewImageVersion(idea().id));
$('history-retry').addEventListener('click',()=>void loadImageHistory());
$('prev-idea').addEventListener('click',()=>stepIdea(-1));$('next-idea').addEventListener('click',()=>stepIdea(1));
$('zoom').addEventListener('click',()=>{const zoomed=$('image-scroll').classList.toggle('zoomed');$('zoom').textContent=zoomed?'نمای کامل تصویر':'اندازهٔ واقعی';});
$('idea-note').addEventListener('input',()=>{record().ideaNotes[idea().id]=$('idea-note').value;$('edit-error').hidden=true;$('idea-note').removeAttribute('aria-invalid');persist();drawEditState();});
$('sentence-note').addEventListener('input',()=>{record().note=$('sentence-note').value;persist();drawBatchDraftState();});
$('approve').addEventListener('click',()=>setDecision('approved',idea().id));$('revise').addEventListener('click',()=>requestRevision());
$('submit-revision').addEventListener('click',submitImageRevision);$('export-revisions').addEventListener('click',exportFeedback);
$('revise-all').addEventListener('click',()=>{setDecision('revise_all');if(!record().note.trim())$('sentence-note').focus();});
$('clear-overall-revision').addEventListener('click',()=>setDecision('pending'));
$('open-custom-idea').addEventListener('click',()=>{const open=$('custom-idea-panel').hidden;state.customPanels[sentence().id]=open;$('custom-idea-panel').hidden=!open;$('open-custom-idea').setAttribute('aria-expanded',String(open));if(open)$('custom-idea').focus();});
$('custom-idea').addEventListener('input',()=>{const r=record();r.customIdea=$('custom-idea').value;$('custom-idea-error').hidden=true;$('custom-idea').removeAttribute('aria-invalid');persist();drawBatchDraftState();});
$('submit-custom-idea').addEventListener('click',submitCustomIdea);
$('clear-custom-request').addEventListener('click',()=>setDecision('pending'));
$('reject-all').addEventListener('click',()=>setDecision('rejected'));$('viewer-reject').addEventListener('click',()=>setDecision('rejected'));
$('clear-decision').addEventListener('click',()=>setDecision('pending'));
$('export').addEventListener('click',exportFeedback);$('shortcuts').addEventListener('click',()=>$('help').showModal());$('close-help').addEventListener('click',()=>$('help').close());
document.addEventListener('keydown',e=>{
  if(!state.wave||$('help').open||e.ctrlKey||e.altKey||e.metaKey)return;
  if(/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)||e.target.isContentEditable)return;
  const digit='۱۲۳۴۵'.includes(e.key)?'۱۲۳۴۵'.indexOf(e.key)+1:Number(e.key);
  if(!$('viewer').open){if(digit>=1&&digit<=Math.min(5,sentence().ideas.length)){e.preventDefault();openIdea(digit-1);}return;}
  if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();stepIdea(e.key==='ArrowRight'?1:-1);}
  else if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();switchSentence(state.sentenceIndex+(e.key==='ArrowDown'?1:-1));}
  else if(digit>=1&&digit<=Math.min(5,sentence().ideas.length)){e.preventDefault();openIdea(digit-1);}
  else if(e.key==='['||e.key===']'||e.code==='BracketLeft'||e.code==='BracketRight'){e.preventDefault();stepImageVersion(e.key===']'||e.code==='BracketRight'?1:-1);}
  else if(e.key.toLowerCase()==='f'&&!viewingPreviousVersion()){e.preventDefault();$('idea-note').focus();}
});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'&&state.local)flushLocal();});
window.addEventListener('storage',e=>{if(e.key!==STORAGE_KEY||!e.newValue||!state.wave)return;try{const saved=JSON.parse(e.newValue);mergeRecords(saved.records);drawSentence();if($('viewer').open)drawViewer();}catch{}});
function registerReviewTools(){
  const context=document.modelContext;if(!context?.registerTool)return;
  const lifecycle=new AbortController();window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
  const toolDefinitions=[
    {name:'update_illustration_revision_progress',title:'Update real illustration edit progress',description:'Report progress for an already submitted active request. Call in_progress only immediately before actually starting the image edit, or to report a real working stage; this tool does not generate an image. Call failed if the attempt fails. Completion is detected from a published new image carrying the matching revisionRequestId and parentIdeaId.',inputSchema:{type:'object',properties:{requestId:{type:'string'},status:{type:'string',enum:['in_progress','failed']},message:{type:'string',maxLength:500}},required:['requestId','status'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:true},execute:updateRevisionProgress},
    {name:'read_illustration_review',title:'Read illustration review',description:'Read sentences, available ideas, and saved review decisions for this wave.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:true},execute:()=>documentData()},
    {name:'record_illustration_review',title:'Record illustration review',description:'Save a review decision and optional feedback. revise_all edits current ideas; rejected requests new ideas; custom_idea requests exactly five variants of the supplied customIdea.',inputSchema:{type:'object',properties:{sentenceId:{type:'integer'},status:{type:'string',enum:['approved','revise','revise_all','custom_idea','rejected']},ideaId:{type:'string'},comment:{type:'string',maxLength:10000},customIdea:{type:'string',maxLength:10000}},required:['sentenceId','status'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:true},execute:async input=>{
      const n=state.wave.sentences.findIndex(s=>s.id===input?.sentenceId);if(n<0)throw new Error('Sentence is not in this wave');
      if(!['approved','revise','revise_all','custom_idea','rejected'].includes(input.status))throw new Error('Invalid review status');
      const s=state.wave.sentences[n],overall=['revise_all','custom_idea','rejected'].includes(input.status);if(!overall&&!s.ideas.some(i=>i.id===input.ideaId))throw new Error('A valid idea is required');
      if(input.comment!==undefined&&(typeof input.comment!=='string'||input.comment.length>10000))throw new Error('Invalid feedback');
      if(input.customIdea!==undefined&&(typeof input.customIdea!=='string'||input.customIdea.length>10000))throw new Error('Invalid custom idea');
      const customIdea=input.customIdea??record(s).customIdea;if(input.status==='custom_idea'&&(typeof customIdea!=='string'||!customIdea.trim()))throw new Error('A custom idea is required');
      const selected=s.ideas.find(i=>i.id===input.ideaId),revisionComment=input.comment??record(s).ideaNotes[input.ideaId];
      if(input.status==='revise'&&(typeof revisionComment!=='string'||!revisionComment.trim()))throw new Error('An edit description is required');
      switchSentence(n);if(input.comment!==undefined){if(overall)record().note=input.comment;else record().ideaNotes[input.ideaId]=input.comment;}
      if(input.customIdea!==undefined)record().customIdea=input.customIdea;if(input.status==='custom_idea')state.customPanels[s.id]=true;
      setDecision(input.status,overall?null:input.ideaId,input.status==='revise'?createRevisionRequest(selected,revisionComment):null);await flushLocal();return {sentenceId:s.id,status:input.status,chosenIdeaId:record().chosenIdeaId};
    }}
  ];
  for(const tool of toolDefinitions){try{Promise.resolve(context.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{});}catch{}}
}
init();
