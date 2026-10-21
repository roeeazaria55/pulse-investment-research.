import {compareIrenForecast,irenFy26,irenPulseForecasts} from '../research/irenFy26';
const money=(value:number)=>`$${value.toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})}M`;
export function IrenFinancialResults({companyId}:{companyId:string}){
 if(companyId!=='candidate-iren')return null;
 const forecasts=irenPulseForecasts();
 return <section className="thesis-monitor iren-financial-results" dir="rtl" aria-label="נתוני בסיס IREN FY2026 מהדוח הרשמי">
  <h4>IREN · נתוני בסיס FY2026 מהדוח הרשמי</h4>
  <p>נתונים מדוח המנפיק מ־27.08.2026. ערכי המקור נבדקו מול טבלאות הדוח וה־PDF; ממתינים לבדיקת אנליסט. זו תמצית מקור שמורה, לא קריאה חיה ולא עותק מלא של הקובץ.</p>
  <p><strong>FY2026 פורסם לפני מחקר PULSE מ־20.10.2026. הנתונים מוכיחים קליטה מהמקור; אינם הפתעה ואינם בדיקת איכות התחזית.</strong> תחזיות FY2027 והרבעונים העתידיים נשמרות להשוואה לתוצאות שיפורסמו לאחר מועד התחזית.</p>
  <p><a href={`${import.meta.env.BASE_URL}research/PULSE_IREN_Full_Research_HE_PreQ1FY27.pdf`} target="_blank" rel="noopener noreferrer">מחקר PULSE לקראת Q1 FY2027 · ללא שינוי ↗</a></p>
  <div className="thesis-metrics">{irenFy26.observations.map(observation=>{
   const forecast=forecasts[observation.id],comparison=compareIrenForecast(observation,forecast);
   return <article className="thesis-metric" key={observation.id} data-testid={`iren-fy26-${observation.id}`}>
    <h5>{observation.title}</h5>
    <dl className="thesis-metric-points"><div><dt>תוצאה מהדוח · נתון בסיס</dt><dd><bdi>{money(observation.point.value)}</bdi></dd><small>{observation.periodText} · מיליוני USD</small></div><div><dt>הנחת מודל קיימת · נכתבה לאחר הדוח</dt><dd><bdi>{money(forecast.point.value)}</bdi></dd><small>{forecast.description} · מודל מתאריך {forecast.asOf}</small></div></dl>
    <p>{observation.definition}</p>
    {observation.id==='capex'&&<p>חישוב: <bdi>{observation.sourceValues.map(v=>Math.abs(v.value).toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})).join(' + ')} = {observation.point.value.toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})} USD million</bdi>. שני סעיפי המקור נרשמו כתזרימי מזומן שליליים.</p>}
    {comparison.result.status==='comparable'?<p>פער מול התחזית · ממתין לאימות: <bdi>{money(comparison.result.difference)}{comparison.result.percent===null?'':` (${comparison.result.percent.toFixed(1)}%)`}</bdi></p>:<div><p><strong>אין השוואה מספרית תקפה</strong></p><ul>{comparison.reasons.map(reason=><li key={reason}>{reason}</li>)}</ul></div>}
    <p>מצב אימות: {observation.verification==='derived-source-checked-pending-review'?'סכום מחושב מערכי מקור שנבדקו':'ערך שנבדק מול המקור'} · ממתין לבדיקת אנליסט · נבדק {observation.checkedDate}.</p>
    <p><a href={observation.pdfUrl+`#page=${observation.pdfPage}`} target="_blank" rel="noopener noreferrer">מקור רשמי · PDF עמוד {observation.pdfPage} ↗</a> · <a href={observation.sourceUrl} target="_blank" rel="noopener noreferrer">הודעת המנפיק ↗</a></p>
    <details><summary>ערכי המקור והגדרת התחזית</summary><ul>{observation.sourceValues.map(v=><li key={v.label}><bdi>{v.label}: {v.raw} US$m</bdi></li>)}</ul><p>{forecast.definition}</p></details>
   </article>;
  })}</div>
  {irenFy26.issues.map(issue=><p role="status" key={issue.id}>נתון לא זמין ({issue.id}): {issue.reason}</p>)}
 </section>;
}
