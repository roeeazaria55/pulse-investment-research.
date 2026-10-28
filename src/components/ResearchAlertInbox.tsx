import type {News} from '../types';
import {unreadResearchAlerts} from '../research/alertPolicy';
interface Props {items:readonly News[];readIds:readonly string[];groups?:readonly {id:string;itemIds:string[]}[];onRead:(id:string)=>void;}
export function ResearchAlertInbox({items,readIds,groups=[],onRead}:Props){
 const alerts=unreadResearchAlerts(items,readIds,5,groups);
 if(!alerts.length)return null;
 return <details className="panel" aria-label="התראות מחקר חדשות" data-testid="research-alert-inbox">
  <summary>אירועים למחקר · {alerts.length} התראות שלא נקראו</summary>
  <p><small>דירוג על פי מטא־נתונים ומקור, ללא קביעה על מחיר מניה. אירוע ברמה קריטית אינו נקבע אוטומטית.</small></p>
  <ul>{alerts.map(({item,severity,reason})=><li key={item.id}>
   <strong>{severity==='high'?'חשיבות גבוהה':'חשיבות בינונית'} · {item.company}</strong>
   <p><a href={item.sourceUrl} target="_blank" rel="noopener noreferrer">{item.originalTitle||item.headline}</a></p>
   <small>{reason} · פרסום: {item.publishedAt?new Date(item.publishedAt).toLocaleDateString('he-IL'):'תאריך פרסום לא זמין'}</small>
   <div><button type="button" className="text-button" onClick={()=>onRead(item.id)}>סימון כנקרא</button></div>
  </li>)}</ul>
 </details>;
}
