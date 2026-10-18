import {researchFields,type Research,type ResearchField} from '../types';
export interface AnalysisImport {
 version:1;companyId:string;asOf:string;fields:Record<ResearchField,string>;sourceUrls:string[];missing:string[];
}
export const safeSource=(x:unknown):x is string=>{try{if(typeof x!=='string'||x.length>2000)return false;const u=new URL(x);return u.protocol==='https:'&&!u.username&&!u.password&&!u.port;}catch{return false;}};
export const validDate=(x:unknown):x is string=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
export function analysisContract(companyId:string){
 const example={version:1,companyId,asOf:'YYYY-MM-DD',fields:Object.fromEntries(researchFields.map(k=>[k,''])),sourceUrls:[],missing:[]};
 return `\n\nבסוף הניתוח החזר אובייקט JSON יחיד לייבוא ל־PULSE, ללא הערות קוד, בהתאם לדוגמה. מלא asOf בתאריך המחקר בפורמט YYYY-MM-DD. כל ערכי fields הם טקסט בעברית; שדה שאין לו בסיס נשאר מחרוזת ריקה והפער מצוין ב־missing. כלול ב־sourceUrls רק כתובות HTTPS של מקורות שבהם השתמשת בפועל, והבחן מקורות שלא הצלחת לפתוח. הנתונים אינם מאומתים רק משום שהפורמט תקין. אל תשנה את companyId.\n${JSON.stringify(example,null,2)}`;
}
export function parseAnalysis(text:string,expectedCompanyId:string):AnalysisImport{
 if(text.length>150000)throw Error('הניתוח גדול מדי. הגבול הוא 150,000 תווים.');
 let x:AnalysisImport;
 try{x=JSON.parse(text.trim().replace(/^```(?:json)?\s*\n?/i,'').replace(/\n?```$/,''));}catch{throw Error('לא נמצא JSON תקין. העתק את אובייקט הייבוא בלבד.');}
 if(!x||typeof x!=='object'||Array.isArray(x)||x.version!==1||x.companyId!==expectedCompanyId)throw Error('הניתוח אינו מתאים לחברה שנבחרה או שגרסת הייבוא אינה נתמכת.');
 if(!validDate(x.asOf)||!x.fields||typeof x.fields!=='object'||Array.isArray(x.fields)||Object.keys(x.fields).length!==researchFields.length||!researchFields.every(k=>typeof x.fields[k]==='string'&&x.fields[k].length<=5000)||Object.keys(x.fields).some(k=>!researchFields.includes(k as ResearchField)))throw Error('בדוק תאריך מחקר ואת כל שדות המחקר. שדה מוגבל ל־5,000 תווים.');
 if(!Array.isArray(x.sourceUrls)||x.sourceUrls.length>30||!x.sourceUrls.every(safeSource)||!Array.isArray(x.missing)||x.missing.length>30||!x.missing.every(s=>typeof s==='string'&&s.length<=1000))throw Error('רשימת המקורות או המידע החסר אינה תקינה. יש להשתמש בקישורי HTTPS.');
 return {version:1,companyId:x.companyId,asOf:x.asOf,fields:Object.fromEntries(researchFields.map(k=>[k,x.fields[k]])) as AnalysisImport['fields'],sourceUrls:[...new Set(x.sourceUrls)],missing:[...x.missing]};
}
export function applyAnalysis(current:Research,pack:AnalysisImport,selected:ResearchField[],now=new Date().toISOString()):Research{
 const keys=researchFields.filter(k=>selected.includes(k)&&pack.fields[k].trim());
 if(!keys.length)throw Error('בחר לפחות שדה אחד שאינו ריק.');
 const fields=Object.fromEntries(researchFields.map(k=>[k,current[k]])) as Record<ResearchField,string>;
 return {...current,...Object.fromEntries(keys.map(k=>[k,pack.fields[k]])),
  importInfo:{companyId:pack.companyId,asOf:pack.asOf,importedAt:now,sourceUrls:pack.sourceUrls,missing:pack.missing,kind:'user-imported',appliedFields:keys},
  versions:[{id:crypto.randomUUID(),savedAt:now,fields,importInfo:current.importInfo},...(current.versions||[])].slice(0,3)};
}
