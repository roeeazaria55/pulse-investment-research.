import type {ReactNode} from 'react';
import {compareFinancialForecast,type FinancialForecast,type FinancialResult} from '../research/financialResults';
const money=(value:number,unit:string)=>unit==='USD million'||unit==='USD billion'?`$${value.toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:unit==='USD million'?3:6})}${unit==='USD million'?'M':'B'}`:`${value.toLocaleString('en-US')} ${unit}`;
export function FinancialResults({ticker,period,testIdPrefix,result,forecasts,children,metadataLinkLabel}:{ticker:string;period:string;testIdPrefix:string;result:FinancialResult;forecasts:Partial<Record<string,FinancialForecast>>;children:ReactNode;metadataLinkLabel:string}){
 return <section className="thesis-monitor financial-results" dir="rtl" aria-label={`נתוני בסיס ${ticker} ${period} מהדוח הרשמי`}>
  <h4>{ticker} · נתוני בסיס {period} מהדוח הרשמי</h4>
  {children}
  <div className="thesis-metrics">{result.observations.map(observation=>{
   const forecast=forecasts[observation.id],comparison=compareFinancialForecast(observation,forecast);
   return <article className="thesis-metric" key={observation.id} data-testid={`${testIdPrefix}-${observation.id}`}>
    <h5>{observation.title}</h5>
    <dl className="thesis-metric-points"><div><dt>תוצאה מהדוח · נתון בסיס</dt><dd><bdi>{money(observation.point.value,observation.point.unit)}</bdi></dd><small>{observation.periodText} · {observation.point.unit}</small></div><div><dt>{forecast?(forecast.asOf>=observation.resultsPublishedDate?'הנחת מודל קיימת · נכתבה ביום פרסום התוצאה או לאחריו':'תחזית PULSE קיימת'):'תחזית מספרית'}</dt><dd>{forecast?<bdi>{money(forecast.point.value,forecast.point.unit)}</bdi>:'לא הוגדרה תחזית מספרית תואמת'}</dd>{forecast&&<small>{forecast.description} · מודל מתאריך {forecast.asOf}</small>}</div></dl>
    <p>{observation.definition}</p>
    {observation.verification==='derived-source-checked-pending-review'&&<p>חישוב: <bdi>{observation.sourceValues.map(v=>Math.abs(v.value).toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})).join(' + ')} = {observation.point.value.toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})} {observation.point.unit}</bdi>. שני סעיפי המקור נרשמו כתזרימי מזומן שליליים.</p>}
    {comparison.result.status==='comparable'?<p>פער מול התחזית · ממתין לאימות: <bdi>{money(comparison.result.difference,observation.point.unit)}{comparison.result.percent===null?'':` (${comparison.result.percent.toFixed(1)}%)`}</bdi></p>:<div><p><strong>אין השוואה מספרית תקפה</strong></p><ul>{comparison.reasons.map(reason=><li key={reason}>{reason}</li>)}</ul></div>}
    <p>מצב אימות: {observation.verification==='derived-source-checked-pending-review'?'סכום מחושב מערכי מקור שנבדקו':'ערך שנבדק מול המקור'} · ממתין לבדיקת אנליסט · נבדק {observation.checkedDate} · פורסם {observation.publishedDate}.</p>
    <p><a href={observation.locationUrl} target="_blank" rel="noopener noreferrer">מקור רשמי · {observation.locationLabel} ↗</a> · <a href={observation.sourceUrl} target="_blank" rel="noopener noreferrer">{metadataLinkLabel} ↗</a></p>
    <details><summary>ערכי המקור והגדרת התחזית</summary><ul>{observation.sourceValues.map(v=><li key={v.label}><bdi>{v.label}: {v.raw} {observation.sourceUnit}</bdi></li>)}</ul><p>תקופת הנתון: <bdi>{observation.periodStart} – {observation.periodEnd}</bdi> · {observation.point.period}. יחידת המקור: {observation.sourceUnit}; יחידת התצוגה: {observation.point.unit}.</p>{forecast&&<p>{forecast.definition}</p>}</details>
   </article>;
  })}</div>
  {result.issues.map(issue=><p role="status" key={issue.id}>נתון לא זמין ({issue.id}): {issue.reason}</p>)}
 </section>;
}
