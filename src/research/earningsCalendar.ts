import registry from '../../public/data/earnings-registry.json';
import type {EarningsEvent,Intelligence} from '../intelligenceTypes';
export const israelDay=(now=new Date())=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
export function shiftDay(day:string,days:number){const d=new Date(day+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+days);return d.toISOString().slice(0,10);}
export function weekStart(day:string){return shiftDay(day,-new Date(day+'T12:00:00Z').getUTCDay());}
export const dateLabel=(day:string)=>day.split('-').reverse().join('.');
export function earningsEvents(intel?:Intelligence){
 const live=new Map(intel?.calendar.events.map(e=>[e.securityId,e]));
 return registry.companies.map(c=>{const collected=live.get(c.securityId);return collected&&(collected.verifiedAt||'')>=(c.event.verifiedAt||'')?collected:({...c.event,securityId:c.securityId,name:c.name,id:'registry:'+c.securityId,revision:'registry'} as EarningsEvent);});
}
export function nextEarnings(id:string,intel?:Intelligence,today=israelDay()){
 return earningsEvents(intel).find(e=>e.securityId===id&&e.status!=='unannounced'&&e.date&&e.date>=today);
}
export function eventsInWeek(events:EarningsEvent[],start:string){return events.filter(e=>e.status!=='unannounced'&&e.date&&e.date>=start&&e.date<=shiftDay(start,6)).sort((a,b)=>a.date!.localeCompare(b.date!)||a.name.localeCompare(b.name));}
