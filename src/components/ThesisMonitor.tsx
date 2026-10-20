import {suppliedFor,suppliedPdfUrl} from '../data/suppliedResearch';
import {thesisMonitorFor,metricComparison} from '../research/thesisMonitoring';
function openChapter(companyId:string,number:number){
 const heading=document.getElementById(`${companyId}-pdf-section-${number}`);
 const reading=heading?.closest('details');if(reading)reading.open=true;
 heading?.focus({preventScroll:true});heading?.scrollIntoView({block:'start'});
}
export function ThesisMonitor({companyId}:{companyId:string}){
 const monitor=thesisMonitorFor(companyId),report=suppliedFor(companyId);if(!monitor||!report)return null;
 return <section className="thesis-monitor" aria-label={`מעקב התזה של ${monitor.ticker}`}>
  <div className="thesis-monitor-head"><h4>האם העסק מתקדם לפי הניתוח?</h4><small>6 מדדי מעקב · בסיס המחקר {monitor.asOf.split('-').reverse().join('.')}</small></div>
  <p>נקודת הפתיחה היא הנתונים שבמחקר שסופק. טרם הוחל כאן עדכון של דוח נוסף. דוחות שנקראו אוטומטית מוצגים בנפרד בקליטת הדוחות. פער מחושב רק לאותה תקופה, יחידה והגדרה חשבונאית.</p>
  <div className="thesis-metrics">{monitor.metrics.map(metric=>{
   const result=metricComparison(metric.observed,metric.target);
   return <details className="thesis-metric" key={metric.id}>
    <summary><span>{metric.title}</span><small>{result.label}</small></summary>
    <dl className="thesis-metric-points"><div><dt>נקודת הפתיחה במחקר</dt><dd>{metric.baseline}</dd></div><div><dt>מה הניתוח מניח קדימה</dt><dd>{metric.expectation}</dd></div></dl>
    {result.status==='period'&&<p className="muted">אין פער מספרי: {metric.observed!.period} ו־{metric.target!.period} הן תקופות שונות.</p>}
    {result.status==='definition'&&<p className="muted">אין פער מספרי: נדרשת התאמה בין הגדרות המדד.</p>}
    {result.status==='comparable'&&<p>פער מההנחה: <bdi>{result.difference.toLocaleString('en-US',{maximumFractionDigits:2})}{result.percent!==null?` (${result.percent.toFixed(1)}%)`:''}</bdi>. הפער לבדו אינו קובע אם התזה התחזקה או נחלשה.</p>}
    <p><b>למה זה משנה לשווי:</b> {metric.why}</p><p><b>מה לבדוק בדוח הבא:</b> {metric.nextCheck}</p><p><b>מה ידרוש בחינה מחדש:</b> {metric.thesisRisk}</p>
    <div className="thesis-source-actions"><button type="button" className="text-button" onClick={()=>openChapter(companyId,metric.section)}>לנתוני המקור · פרק {metric.section}</button>{metric.targetSection!==metric.section&&<button type="button" className="text-button" onClick={()=>openChapter(companyId,metric.targetSection)}>להנחות · פרק {metric.targetSection}</button>}</div>
   </details>;
  })}</div>
  <small>ההנחות הן תרחישי מחקר; תחזית הנהלה מסומנת בנפרד. מידע שלא כומת אינו מקבל ציון עמידה בתזה.</small>
  <a className="text-button" href={suppliedPdfUrl(report)} target="_blank" rel="noopener noreferrer">מקור מדדי המעקב · PDF {monitor.ticker} ↗</a>
 </section>;
}
export function ValuationContext({companyId}:{companyId:string}){
 const report=suppliedFor(companyId);if(!report)return null;
 const nbis=report.ticker==='NBIS',sndk=report.ticker==='SNDK';
 return <section className="valuation-context" aria-label={`אופק והנחות השווי של ${report.ticker}`}>
  <dl className="valuation-context-grid"><div><dt>מחיר המניה שמופיע במחקר</dt><dd><bdi>${report.reference.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}</bdi> · {report.referenceDate===null?'תאריך לא צוין במסמך':(report.referenceDate||report.date).split('-').reverse().join('.')}</dd><small>מחיר ייחוס מתוך המסמך, אינו שער חי.</small></div><div><dt>למה מתייחס השווי?</dt><dd>{nbis?'יעד ל־20.10.2027 · 12 חודשים מתאריך הניתוח':sndk?'שווי על בסיס רווחי FY2028 · אין מועד יעד קשיח':report.horizonLabel}</dd><small>{nbis?'בסיס החישוב: הכנסות שנת 2027.':sndk?'השנה הפיסקלית היא תקופת הרווח; אינה תאריך מימוש של השווי.':report.horizonNote}</small></div></dl>
  <details><summary>ההנחות שמניעות את השווי{sndk?' ומה חסר ליעד של 12 חודשים':''}</summary>
   {nbis?<><p>הכנסות 2027: $5.5B / $8.5B / $12B; מכפילי EV/Sales: ‏4 / 6 / 8, בתרחישי דוב / בסיס / שור בהתאמה. בכל התרחישים: חוב נטו $4B ומניות 300M.</p><p>חוב ומניות הם הנחות פשטניות. לפני עדכון יעד יש להשלים גשר למזומן, למימון ולדילול, ולבדוק את המכפילים מחדש.</p></>:sndk?<><p>EPS מנורמל FY2028: ‏$65 / $145 / $220; מכפילים: ‏8 / 11 / 13, בתרחישי דוב / בסיס / שור בהתאמה.</p><p>יעד ל־20.10.2027 טרם נבנה. נדרש לקבוע איזה רווח מנורמל יתומחר במועד זה, מכפיל מתאים, גשר למספר המניות, והאם נדרש היוון מפורש מהשווי העתידי. אין להחיל היוון אוטומטי נוסף על מכפיל שכבר משקף את מועד היעד.</p></>:<><p>{report.summary}</p><p>{report.arithmeticNote||report.horizonNote}</p>{report.unitNote&&<p>{report.unitNote}</p>}</>}
   <p>המשקולות: דוב 20%, בסיס 50%, שור 30%. אלה הנחות שיפוטיות. השווי הפעיל נשאר לפי המסמך עד לפרסום ניתוח מתוקן; בדיקות משניות והארכיון אינם מחליפים אותו.</p>
  </details>
 </section>;
}
