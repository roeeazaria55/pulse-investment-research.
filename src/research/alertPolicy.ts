import type {News} from '../types';
export type AlertSeverity='critical'|'high'|'medium'|'low';
export interface ResearchAlert {item:News;severity:AlertSeverity;reason:string;verified:boolean;}
/** Headline metadata is never enough for a critical alert or a thesis update. */
export function classifyResearchAlert(item:News):ResearchAlert|null {
 if(item.demo||!item.rating||item.rating.companyRelevance!=='direct'||!item.sourceUrl.startsWith('https://'))return null;
 const r=item.rating;
 const official=r.verifiedOfficial===true&&r.basis==='official-metadata';
 const significant=official&&r.level==='high'&&r.eventScore>=75;
 const medium=official&&r.eventScore>=40;
 const severity:AlertSeverity=significant?'high':medium?'medium':'low';
 const reason=official?
  'אירוע ממקור רשמי, אך תוכן המסמך והשפעתו הכלכלית דורשים בדיקה.':
  'כותרת ומטא־נתונים בלבד; האירוע וההשפעה טרם אומתו.';
 return {item,severity,reason,verified:official};
}
export function unreadResearchAlerts(items:readonly News[],readIds:readonly string[],limit=5):ResearchAlert[]{
 const read=new Set(readIds),seen=new Set<string>();
 const candidates:ResearchAlert[]=[];
 for(const item of items){
  if(read.has(item.id)||seen.has(item.id))continue;
  const alert=classifyResearchAlert(item);
  if(!alert||alert.severity==='low')continue;
  seen.add(item.id);candidates.push(alert);
 }
 const level=(s:AlertSeverity)=>({critical:4,high:3,medium:2,low:1})[s];
 return candidates.sort((a,b)=>level(b.severity)-level(a.severity)||
  Date.parse(b.item.publishedAt||b.item.collectedAt)-Date.parse(a.item.publishedAt||a.item.collectedAt)).slice(0,limit);
}
