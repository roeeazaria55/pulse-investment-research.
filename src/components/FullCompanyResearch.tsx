import {useRef} from 'react';
import narratives from '../data/originalNarratives.json';
import type {AnalysisImport} from '../research/exchange';
import {labels} from '../research/prompt';
import type {ResearchField} from '../types';
const chapters=['ההסבר מהשיחות','העסק והיתרון','המספרים והתזרים','התרחישים והתמחור','הסיכונים והמעקב','מקורות ומידע חסר'];
export const hasFullResearch=(companyId:string)=>narratives.some(n=>n.companyId===companyId);
export function FullCompanyResearch({analysis}:{analysis:AnalysisImport}){
 const root=useRef<HTMLDivElement>(null),narrative=narratives.find(n=>n.companyId===analysis.companyId);
 if(!narrative)return null;
 const fields=(keys:ResearchField[])=>keys.map(key=><div className="research-reading-field" key={key}><h5>{labels[key]}</h5><p>{analysis.fields[key]}</p></div>);
 const heading=(index:number)=><h4 id={`${analysis.companyId}-chapter-${index}`} tabIndex={-1}>{index+1}. {chapters[index]}</h4>;
 const go=(index:number)=>{const target=root.current?.querySelector<HTMLElement>(`#${analysis.companyId}-chapter-${index}`);target?.focus({preventScroll:true});target?.scrollIntoView({behavior:'auto',block:'start'});};
 return <div className="full-company-research" ref={root} aria-label={`הניתוח העסקי של ${narrative.label}`}>
  <p className="research-reading-intro">העסק, ההיגיון מאחורי התזה, הנתונים, התרחישים והסיכונים — ברצף קריאה אחד.</p>
  <p className="research-coverage-note">{narrative.coverage}</p>
  <nav className="research-chapters" aria-label={`פרקי הניתוח של ${narrative.label}`}>{chapters.map((title,index)=><button type="button" key={title} onClick={()=>go(index)}>{title}</button>)}</nav>
  <section className="research-reading-chapter">{heading(0)}<p>סיכום החלקים ששוחזרו מהשיחות; אינו תמליל מלא ואינו סקירת שוק חדשה.</p>{narrative.original.map((part,i)=><div className="original-research-passage" key={i}><small>מהשיחה · {part.date.split('-').reverse().join('.')}</small><h5>{part.heading}</h5><p>{part.text}</p></div>)}<details><summary>היסטוריית גרסאות ותיקונים ביחס לשיחות</summary><p>{narrative.history}</p>{narrative.corrections.map((text,i)=><p key={i}>{text}</p>)}</details></section>
  <section className="research-reading-chapter">{heading(1)}<small>מחקר מתועד והסבר משלים · עודכן {analysis.asOf}</small><p>{narrative.bridge}</p>{fields(['thesis','advantages'])}</section>
  <section className="research-reading-chapter">{heading(2)}<small>נתוני הדוחות והפרשנות שמלווים אותם; לכל נתון תקופת דיווח משלו.</small>{fields(['revenue','profitability','cashFlow'])}</section>
  <section className="research-reading-chapter">{heading(3)}<p>יעדי השיחות נשמרו עם מועדיהם. היגיון איכותי מוצג רק כשהוא שוחזר; הנחות מספריות חסרות אינן מושלמות מתוך מחיר היעד.</p>{fields(['valuation','bear','base','bull'])}</section>
  <section className="research-reading-chapter">{heading(4)}{fields(['risks','catalysts'])}<h5>מה יחליש את התזה או יחייב בדיקה מחדש</h5><small>מסגרת מעקב משלימה שנכתבה לאתר; אינה שחזור של ניסוח או ספי בדיקה מקוריים.</small><ul>{narrative.monitoring.map((text,i)=><li key={i}>{text}</li>)}</ul></section>
  <section className="research-reading-chapter">{heading(5)}<p>{narrative.coverage}</p><details><summary>מקורות שנקראו ({analysis.sourceUrls.length})</summary>{analysis.sourceUrls.map((url,i)=><p key={url}><a href={url} target="_blank" rel="noopener noreferrer">מקור {i+1}: {new URL(url).hostname} ↗</a></p>)}</details><h5>מידע חסר ומגבלות</h5><ul>{analysis.missing.map((text,i)=><li key={i}>{text}</li>)}</ul></section>
  <button type="button" className="text-button" onClick={()=>go(0)}>חזרה לתחילת הניתוח ↑</button>
 </div>;
}
