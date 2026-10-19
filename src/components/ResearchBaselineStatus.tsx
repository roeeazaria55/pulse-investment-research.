import {useEffect,useState} from 'react';
import {parseOfficialSnapshot,officialTitle,type OfficialSnapshot} from '../data/official';
import {pendingResearchSources,researchAge} from '../data/publishedResearch';
import type {AnalysisImport} from '../research/exchange';
export function ResearchBaselineStatus({pack}:{pack:AnalysisImport}){
 const [snapshot,setSnapshot]=useState<OfficialSnapshot|null>(null),[failed,setFailed]=useState(false);
 useEffect(()=>{
  const controller=new AbortController();setFailed(false);setSnapshot(null);
  fetch(`${import.meta.env.BASE_URL}data/official-sources.json`,{cache:'no-cache',signal:controller.signal})
   .then(r=>{if(!r.ok)throw Error('Sources unavailable');return r.json();})
   .then(parseOfficialSnapshot).then(s=>{if(!controller.signal.aborted)setSnapshot(s);})
   .catch(()=>{if(!controller.signal.aborted)setFailed(true);});
  return ()=>controller.abort();
 },[pack.companyId]);
 const age=researchAge(pack.asOf),pending=snapshot?pendingResearchSources(pack,snapshot.items):[];
 return <div aria-label="עדכניות המחקר">
  {age!==null&&age>=90&&<p role="status">המחקר בן {age} ימים — יש לעדכן אותו לפני הסתמכות על הנתונים.</p>}
  <p>מחקר מתוארך; מקורות שמתפרסמים או נאספים בהמשך אינם משנים אותו אוטומטית.</p>
  {failed?<p role="status">מצב הפרסומים אינו זמין. אין להסיק שאין עדכונים; המחקר השמור עדיין זמין לקריאה.</p>:!snapshot?<small>בודק פרסומים שנאספו…</small>:<>
   <small>מאגר מקורות שנבדק: {snapshot.generatedAt?new Date(snapshot.generatedAt).toLocaleString('he-IL'):'מועד לא זמין'}. האיסוף עשוי להיות חלקי.</small>
   {pending.length?<details><summary>פרסומים לבדיקה שלא נכללו במחקר ({pending.length})</summary><p>רשימה זו אינה קובעת שהמידע מהותי או שהפרסומים חדשים. לפריט ללא תאריך לא ניתן לקבוע אם פורסם אחרי המחקר.</p>{pending.map(item=><p key={item.id}><a href={item.url} target="_blank" rel="noopener noreferrer">{officialTitle(item)}</a><br/>{item.publishedDate?`תאריך פרסום: ${item.publishedDate} — ${item.publishedDate>pack.asOf?'מאוחר מתאריך המחקר':'לא נכלל במקורות המחקר; עשוי להיות מידע קודם'}`:'תאריך פרסום לא ידוע — עשוי להיות מסמך קודם'}</p>)}</details>:<p>לא נמצאו במאגר זה קישורים נוספים מעבר למקורות המחקר. זו אינה הוכחה לכיסוי מלא או לעדכניות המחקר.</p>}
  </>}
 </div>;
}
