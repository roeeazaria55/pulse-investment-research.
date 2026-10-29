import {useEffect,useState} from 'react';
import {BrainCircuit,ShieldAlert,ExternalLink} from 'lucide-react';

type Citation={evidenceId:string;kind:string;claim:string;uncertainty:string};
type Insight={observation:string;hypothesis:string;evidenceIds:string[];unknowns:string[]};
type Scenario={id:string;suggestedProbability:number;reason:string;evidenceIds:string[];status:string};
export type AIReviewDraft={id:string;companyId:string;ticker:string;model:string;
 status:'requires-human-review';analysisMode:'model-generated-unverified';
 reviewStatus:'not-approved';publicationStatus:'not-approved';sourcePacketSha256:string;
 evidenceCitations:Citation[];interpretations:Insight[];analystQuestions:string[];
 suggestedScenarioReview:Scenario[];proposedValuationAction:'no-automatic-change';
 approvedTargetPrice:null;approvedScenarios:null;firstRecordedAt:string;immutableSha256:string};
export function validateAIReviewFeed(raw:unknown,companyId:string):AIReviewDraft[]{
 if(!raw||typeof raw!=='object')throw Error('מבנה טיוטות AI אינו תקין');
 const data=raw as {version:number;drafts:AIReviewDraft[]};
 if(data.version!==1||!Array.isArray(data.drafts)||data.drafts.length>250)throw Error('מבנה טיוטות AI אינו תקין');
 const ids=new Set<string>();
 for(const draft of data.drafts){
  if(!draft||typeof draft!=='object'||!/^ai-draft:[a-f0-9]{32}$/.test(draft.id)||
   !/^[a-f0-9]{64}$/.test(draft.sourcePacketSha256)||!/^([a-f0-9]{64})$/.test(draft.immutableSha256)||
   !['gpt-6-luna','gpt-6.1-sol'].includes(draft.model)||ids.has(draft.id)||
   draft.status!=='requires-human-review'||draft.analysisMode!=='model-generated-unverified'||
   draft.reviewStatus!=='not-approved'||draft.publicationStatus!=='not-approved'||
   draft.proposedValuationAction!=='no-automatic-change'||draft.approvedTargetPrice!==null||
   draft.approvedScenarios!==null||!Array.isArray(draft.evidenceCitations)||
   !Array.isArray(draft.interpretations)||!Array.isArray(draft.analystQuestions)||
   !Array.isArray(draft.suggestedScenarioReview)||!Number.isFinite(Date.parse(draft.firstRecordedAt)))
   throw Error('התקבל ניתוח לא מאושר או ללא ייחוס');
  ids.add(draft.id);
  if(draft.evidenceCitations.some(c=>!c||typeof c.claim!=='string'||!c.evidenceId||!c.uncertainty)||
     draft.interpretations.some(x=>!x||!Array.isArray(x.evidenceIds)||!Array.isArray(x.unknowns))||
     draft.suggestedScenarioReview.some(x=>!x||!['bear','base','bull'].includes(x.id)||x.status!=='review-only'||
      !Number.isFinite(x.suggestedProbability)||x.suggestedProbability<0||x.suggestedProbability>100))
    throw Error('נתוני הצעה לא תקינים');
  if(draft.suggestedScenarioReview.length>0&&
    (draft.suggestedScenarioReview.length!==3||
     Math.abs(draft.suggestedScenarioReview.reduce((sum,s)=>sum+s.suggestedProbability,0)-100)>0.001))
    throw Error('משקולות תרחישים אינן תקינות');
 }
 return data.drafts.filter(x=>x.companyId===companyId).sort((a,b)=>b.firstRecordedAt.localeCompare(a.firstRecordedAt));
}
export function AIReviewDraftPanel({companyId}:{companyId:string}){
 const [data,setData]=useState<AIReviewDraft[]|null>(null);
 const [error,setError]=useState(false);
 useEffect(()=>{
  let live=true;setError(false);setData(null);
  fetch(import.meta.env.BASE_URL+'data/ai-research-drafts.json',{cache:'no-store'})
   .then(async r=>{if(!r.ok)throw Error('Not configured');return validateAIReviewFeed(await r.json(),companyId);})
   .then(rows=>{if(live)setData(rows);})
   .catch(()=>{if(live)setError(true);});
  return ()=>{live=false;};
 },[companyId]);
 const draft=data?.[0];
 return <section className="pulse-ai-draft-panel" aria-label="ניתוח בינה מלאכותית לבדיקת אנליסט" dir="rtl">
  <div className="pulse-research-drafts-heading">
   <div><span className="pulse-ai-kicker">PULSE / AI RESEARCH REVIEW</span><h4><BrainCircuit size={19} aria-hidden="true"/> ניתוח AI</h4></div>
   <span className="pulse-ai-pill"><ShieldAlert size={15}/> טיוטה בלבד</span>
  </div>
  {data===null&&!error&&<p role="status">בודק זמינות ניתוח AI…</p>}
  {error&&<p role="status">ניתוח AI עדיין לא הופעל או טרם פורסמה טיוטה. הנתונים הקיימים והמחקר המאושר לא השתנו.</p>}
  {data?.length===0&&<p>אין עדיין ניתוח AI שמור לחברה זו. קליטת הדוחות יכולה להמשיך גם ללא חיבור API.</p>}
  {draft&&<>
   <p className="pulse-ai-meta">מודל: <bdi>{draft.model}</bdi> · תאריך טיוטה: {new Date(draft.firstRecordedAt).toLocaleDateString('he-IL')} · מזהה חבילת מקור: <bdi>{draft.sourcePacketSha256.slice(0,12)}…</bdi></p>
   <div className="pulse-ai-review-warning" role="status">הפלט נוצר במודל אך טרם אומת ואושר. העובדות, הנחות המודל ומחיר היעד המאושרים לא שונו.</div>
   <h5>ממצאים והשלכות לבדיקה</h5>
   {draft.interpretations.length?draft.interpretations.map((x,i)=><article key={i} className="pulse-ai-insight">
    <p><strong>תצפית:</strong> {x.observation}</p><p><strong>השערה לבדיקה:</strong> {x.hypothesis}</p>
    {!!x.unknowns.length&&<p><small>חסר/אי־ודאות: {x.unknowns.join(' · ')}</small></p>}
    <small>מזהי ראיות: {x.evidenceIds.join(', ')}</small>
   </article>):<p>עדיין אין מסקנות מגובות שניתן להציג.</p>}
   {!!draft.suggestedScenarioReview.length&&<div className="pulse-ai-scenario-grid">
    {draft.suggestedScenarioReview.map(s=><div key={s.id}>
     <span>{s.id.toUpperCase()} · טיוטה</span>
     <strong><bdi>{s.suggestedProbability}%</bdi></strong>
     <small>{s.reason}</small>
    </div>)}
   </div>}
   <details><summary>מקורות מצוטטים ושאלות אנליסט</summary>
    <ul>{draft.evidenceCitations.map((c,i)=><li key={i}><strong>{c.kind}:</strong> {c.claim}<p><small>{c.uncertainty} · {c.evidenceId}</small></p></li>)}</ul>
    {!!draft.analystQuestions.length&&<p>שאלות פתוחות: {draft.analystQuestions.join(' · ')}</p>}
   </details>
   <p><small><ExternalLink size={13} aria-hidden="true"/> פרסום מחיר יעד או מחקר רשמי דורש אישור נפרד דרך GitHub.</small></p>
  </>}
 </section>;
}
