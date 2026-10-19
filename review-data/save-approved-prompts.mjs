import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const workbookPath=path.join(root,'Excellent-Advice-460-FA.xlsx');
const dataDir=path.join(root,'review-data');
const lockPath=path.join(dataDir,'.approved-prompts.lock');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const parse=b=>JSON.parse(String(b).replace(/^\uFEFF/,''));
const requireValue=(ok,message)=>{if(!ok)throw new Error(message);};
let locked=false,tempPath,saveSucceeded=false;
try {
  const argv=process.argv.slice(2);
  requireValue(argv.length===2&&argv[0]==='--input','Usage: save-approved-prompts.mjs --input <JSON file>');
  const input=parse(await fs.readFile(path.resolve(argv[1]),'utf8'));
  const jobs=input.jobs||input.items;
  requireValue(Array.isArray(jobs)&&jobs.length>0,'No approved prompt jobs');
  const feedback=parse(await fs.readFile(path.join(dataDir,'feedback.json'),'utf8'));
  const records=Array.isArray(feedback.records)?feedback.records:Object.values(feedback.records||{});
  const seen=new Set();
  for(const job of jobs){
    requireValue(Number.isInteger(job.sentenceId)&&!seen.has(job.sentenceId),'Invalid or duplicate sentence ID');seen.add(job.sentenceId);
    const record=records.find(r=>Number(r.sentenceId??r.id)===job.sentenceId);
    requireValue(record?.status==='approved'&&record.chosenIdeaId===job.ideaId,`Sentence ${job.sentenceId} has not approved this exact image`);
    if(!job.prompt&&job.promptPath)job.prompt=await fs.readFile(path.resolve(root,job.promptPath),'utf8');
    requireValue(typeof job.prompt==='string'&&job.prompt.trim().length>200,'Full English generation prompt is missing');
    requireValue(job.prompt.length<=32767,'Prompt exceeds Excel cell capacity');
    requireValue(!/^\s*(edit|modify)\b/i.test(job.prompt),'An edit instruction cannot replace a complete generation prompt');
  }
  const lock=await fs.open(lockPath,'wx');locked=true;await lock.writeFile(JSON.stringify({pid:process.pid,startedAt:new Date().toISOString()}));await lock.close();
  const originalBytes=await fs.readFile(workbookPath),originalHash=digest(originalBytes);
  const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
  const sh=wb.worksheets.getItem('ترجمه‌ها');
  const before=sh.getRange('A1:D461').values;
  const oldSchema=before[0][2]==='ترجمه‌ی فارسی'&&!before[0][3];
  const newSchema=before[0][2]==='ترجمه‌ی فارسی'&&before[0][3]==='پرامپت کامل انگلیسی تصویر';
  requireValue(oldSchema||newSchema,'Unexpected workbook columns; preserve the workbook and review its schema');
  requireValue(before[0][0]==='شماره'&&before[0][1]==='متن انگلیسی','Unexpected sentence columns');
  const originals=before.slice(1).map((row,index)=>({id:Number(row[0]),english:row[1],persian:row[2],row:index+2}));
  requireValue(originals.length===460&&new Set(originals.map(r=>r.id)).size===460,'Workbook sentence rows changed');
  const planned=jobs.map(job=>({...job,row:originals.find(r=>r.id===job.sentenceId)?.row,storedPrompt:job.prompt.trim().replace(/\s*\r?\n\s*/g,' ').replace(/[ \t]{2,}/g,' ')}));
  requireValue(planned.every(j=>j.row),'A selected sentence is missing');
  const changed=oldSchema||planned.some(j=>sh.getRange(`D${j.row}`).values[0][0]!==j.storedPrompt);
  const resultJobs=planned.map(j=>({sentenceId:j.sentenceId,ideaId:j.ideaId,row:j.row,column:'D',workbookPath,promptSha256:digest(j.storedPrompt),sourcePromptSha256:digest(j.prompt),characters:j.storedPrompt.length}));
  if(changed){
    const backups=path.join(dataDir,'finalization-backups');await fs.mkdir(backups,{recursive:true});
    const backup=path.join(backups,`workbook-${originalHash}.xlsx`);
    try{await fs.writeFile(backup,originalBytes,{flag:'wx'});}catch(e){if(e.code!=='EEXIST')throw e;requireValue(digest(await fs.readFile(backup))===originalHash,'Workbook backup mismatch');}
    if(oldSchema){
      const width=sh.getRange('C1').format.columnWidth;
      sh.getRange('D1:D461').copyFrom(sh.getRange('C1:C461'),'all');
      sh.getRange('D1').format.columnWidth=width;
      sh.getRange('D1:D461').clear({applyTo:'contents'});
      sh.getRange('D1').values=[['پرامپت کامل انگلیسی تصویر']];
      const tables=sh.tables.items;
      requireValue(tables.length===1&&tables[0].name==='Translations','Unexpected native tables');
      const priorTable=tables[0],style=priorTable.style,showHeaders=priorTable.showHeaders,showTotals=priorTable.showTotals;
      const contents=sh.getRange('A1:D461').values;
      priorTable.delete();
      sh.getRange('A1:D461').values=contents;
      const table=sh.tables.add('A1:D461',true,'Translations');table.style=style;table.showHeaders=showHeaders;table.showTotals=showTotals;table.showBandedColumns=false;table.showFilterButton=true;
      sh.getRange('D1').format.columnWidth=255;
      sh.getRange('D2:D461').format.wrapText=true;
      sh.getRange('D2:D461').format.horizontalAlignment='left';
      sh.getRange('D2:D461').format.verticalAlignment='top';
      sh.getRange('D2:D461').format.font={name:'Arial',size:11};
    }
    for(const job of planned){sh.getRange(`D${job.row}`).values=[[job.storedPrompt]];sh.getRange(`D${job.row}`).format.rowHeight=409;}
    wb.recalculate();
    const after=sh.getRange('A1:D461').values;
    requireValue(originals.every((r,i)=>after[i+1][0]===before[i+1][0]&&after[i+1][1]===r.english&&after[i+1][2]===r.persian),'Original sentence or translation changed');
    requireValue(planned.every(j=>after[j.row-1][3]===j.storedPrompt),'Full prompt cell mismatch');
    const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?',options:{useRegex:true,maxResults:10},maxChars:1200});
    requireValue(!/"kind":"match"/.test(errors.ndjson),'Unexpected formula error in edited workbook');
    tempPath=path.join(backups,`staged-${process.pid}-${Date.now()}.xlsx`);
    await (await SpreadsheetFile.exportXlsx(wb)).save(tempPath);
    const displayRestore=spawnSync(process.env.CODEX_PYTHON || (process.platform==='win32'?'python':'python3'), ['-X','utf8',path.join(dataDir,'preserve-workbook-display.py'),'--source',workbookPath,'--target',tempPath], {encoding:'utf8',windowsHide:true,timeout:20000});
    requireValue(displayRestore.status===0,`Workbook display restoration failed: ${displayRestore.stderr}`);
    requireValue(parse(displayRestore.stdout).cellContentsUnchanged===true,'Display restoration changed cell contents');
    const reread=await SpreadsheetFile.importXlsx(await FileBlob.load(tempPath));
    const saved=reread.worksheets.getItem('ترجمه‌ها').getRange('A1:D461').values;
    requireValue(JSON.stringify(saved)===JSON.stringify(after),'Export did not preserve workbook data');
    const headers=reread.worksheets.getItem('ترجمه‌ها').tables.items[0].getHeaderRowRange().values[0];
    requireValue(headers.length===4&&headers[2]==='ترجمه‌ی فارسی'&&headers[3]==='پرامپت کامل انگلیسی تصویر','Native table header mismatch');
    const previewDir=path.join(dataDir,'finalization-2026-10-10');await fs.mkdir(previewDir,{recursive:true});
    const preview=await wb.render({sheetName:'ترجمه‌ها',range:`A${planned[0].row}:D${planned[0].row}`,scale:1,format:'png'});
    await fs.writeFile(path.join(previewDir,'workbook-after.png'),new Uint8Array(await preview.arrayBuffer()));
    requireValue(digest(await fs.readFile(workbookPath))===originalHash,'Workbook changed while preparing prompts; retry with the latest file');
    await fs.rename(tempPath,workbookPath);tempPath=null;
  }
  const finalHash=digest(await fs.readFile(workbookPath));
  const cachePath=path.join(dataDir,'sentences.json');
  const cache=parse(await fs.readFile(cachePath,'utf8'));
  requireValue(cache.sentences.length===460&&originals.every(r=>{const x=cache.sentences.find(c=>c.id===r.id);return x&&x.english===r.english&&x.persian===r.persian;}),'Sentence cache no longer matches the workbook');
  cache.sourceSha256=finalHash;cache.columns={id:'A',english:'B',promptEnglish:'D',persian:'C'};
  for(const job of planned)cache.sentences.find(r=>r.id===job.sentenceId).promptEnglish=job.storedPrompt;
  const cacheTemp=cachePath+`.${process.pid}.tmp`;await fs.writeFile(cacheTemp,JSON.stringify(cache,null,2)+'\n');await fs.rename(cacheTemp,cachePath);
  const report={saved:true,changed,jobs:resultJobs,workbookPath,workbookSha256:finalHash,translationColumn:'C',translationsPreserved:460,storedPromptLayout:'Complete English content; paragraph whitespace compacted to fit the cell.'};
  await fs.writeFile(path.join(dataDir,'finalization-2026-10-10','workbook-save-status.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));saveSucceeded=true;
}catch(error){console.error(JSON.stringify({saved:false,error:error.message,code:error.code||null,workbookPath}));process.exitCode=1;
}finally{if(locked)await fs.unlink(lockPath).catch(()=>{});}
process.exit(saveSucceeded?0:1);
