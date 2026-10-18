export const MAX_FILE_BYTES=8*1024*1024;
export const MAX_EXTRACTED_CHARS=100000;
export async function readDocument(file:File,startPage=1,pageCount=10){
 if(file.size>MAX_FILE_BYTES)throw Error('הקובץ גדול מ־8MB. בחר מסמך קטן יותר או הדבק קטע נבחר.');
 if(/\.txt$/i.test(file.name)){
  const text=await file.text();if(text.length>MAX_EXTRACTED_CHARS)throw Error('הטקסט ארוך מדי. בחר קטע של עד 100,000 תווים.');
  return {text,scope:'קובץ טקסט מלא',pages:null};
 }
 if(!/\.pdf$/i.test(file.name))throw Error('נתמכים קובצי PDF ו־TXT בלבד.');
 if(!Number.isInteger(startPage)||startPage<1||!Number.isInteger(pageCount)||pageCount<1||pageCount>20)throw Error('בחר עמוד התחלה חיובי ועד 20 עמודים בכל חילוץ.');
 const pdf=await import('pdfjs-dist');
 const worker=await import('pdfjs-dist/build/pdf.worker.min.mjs?url');
 pdf.GlobalWorkerOptions.workerSrc=worker.default;
 const task=pdf.getDocument({data:new Uint8Array(await file.arrayBuffer()),useSystemFonts:true});
 const timer=setTimeout(()=>{void task.destroy();},45000);
 try{
  const doc=await task.promise;
  if(startPage>doc.numPages)throw Error('עמוד ההתחלה אינו קיים במסמך.');
  const end=Math.min(doc.numPages,startPage+pageCount-1);let text='';
  for(let p=startPage;p<=end;p++){
   const page=await doc.getPage(p);const content=await page.getTextContent();
   text+=`\n[עמוד ${p}]\n`+content.items.map(item=>'str' in item?item.str+('hasEOL' in item&&item.hasEOL?'\n':' '):'').join('');
   page.cleanup();if(text.length>MAX_EXTRACTED_CHARS)throw Error('הטקסט שחולץ ארוך מדי. בחר טווח עמודים קטן יותר.');
  }
  if(text.replace(/\[עמוד \d+\]/g,'').trim().length<20)throw Error('לא נמצא טקסט קריא. ייתכן שזה PDF סרוק; חילוץ OCR אינו זמין.');
  return {text,scope:`עמודים ${startPage}–${end} מתוך ${doc.numPages}; עמודים אחרים לא נקראו`,pages:doc.numPages};
 }finally{clearTimeout(timer);await task.destroy();}
}
