import {useState} from 'react';
import {validateResearchCandidate,previewResearchCandidate,type ResearchCandidate} from '../research/researchCandidate';
import {auditSourceValuation} from '../research/sourceValuationAudit';

/** Preview only: never changes a personal draft or public valuation. */
export function ResearchCandidatePreview({companyId}:{companyId:string}){
 const [raw,setRaw]=useState('');
 const [candidate,setCandidate]=useState<ResearchCandidate|null>(null);
 const [error,setError]=useState('');
 const inspect=()=>{
  try {
   if(raw.length>100000)throw Error('הקובץ גדול מדי');
   setCandidate(validateResearchCandidate(JSON.parse(raw),companyId));
   setError('');
  } catch(e){setCandidate(null);setError(e instanceof Error?e.message:'נתונים לא תקינים');}
 };
 const a=candidate&&candidate.valuation.declaredWeighted!==null?
  auditSourceValuation(candidate.valuation.scenarios.map(s=>({id:s.id,weight:s.probability,price:s.statedPrice})),candidate.valuation.declaredWeighted):null;
 return <details className="research-import-info">
  <summary>בדיקת מודל שווי מועמד (JSON) — ללא שמירה</summary>
  <p>בדיקה מבנית בלבד. ה־SHA-256 וקישורי המקור לא אומתו. המידע לא נשמר, לא מחליף מחקר ולא משפיע על התיק.</p>
  <label className="field">JSON מחקר מועמד<textarea aria-label="JSON מחקר מועמד" dir="ltr" rows={6} maxLength={100000} value={raw} onChange={e=>{setRaw(e.target.value);setCandidate(null);setError('');}}/></label>
  <button type="button" onClick={inspect}>בדיקת מחקר מועמד</button>
  {error&&<p role="alert">{error}</p>}
  {candidate&&<div className="analysis-preview">
   <p>חברה: {candidate.companyId} · מחקר: {candidate.source.asOf} · קובץ: {candidate.source.filename}</p>
   <p>מטבע: {candidate.valuation.currency} · יחידה: {candidate.valuation.shareUnit} · אופק שווי: {candidate.valuation.horizon.date} · תקופת בסיס: {candidate.valuation.horizon.earningsPeriod}</p>
   <p>הסתברויות: {candidate.valuation.scenarios.map(s=>s.id+': '+s.probability+'%').join(' · ')}</p>
   {a?<p role={a.status==='discrepancy'?'alert':undefined}>שווי משוקלל מחושב: {a.calculated?.toFixed(3)} · מקור: {a.declared} · {a.status==='discrepancy'?'קיים פער שיש לבדוק':'תואם בתחום סבילות העיגול'}</p>:<p>שווי משוקלל מוצהר חסר</p>}
   <p>השוואה למחקר פעיל תתווסף לאחר מיפוי שני המודלים לאותו פורמט. כעת מוצג ההיקף המלא של המועמד בלבד.</p>
   <details><summary>שדות המועמד שייבדקו בעת האיחוד</summary><ul>{previewResearchCandidate(null,candidate).map((d,i)=><li key={i}>{d.path}</li>)}</ul></details>
  </div>}
 </details>;
}
