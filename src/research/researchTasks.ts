import type {ModelReviewSignal} from './modelReviewSignals';
export type ResearchTaskKind='model'|'source'|'ai'|'event';
export type ResearchDestination='valuation'|'ai'|'sources'|'overview';
export interface ResearchTask {id:string;kind:ResearchTaskKind;companyId:string;ticker:string;title:string;reason:string;date:string;destination:ResearchDestination;sourceUrl?:string}
export function reviewSignalTask(signal:ModelReviewSignal):ResearchTask{return {...signal,kind:'model',title:`בחינת מודל ${signal.ticker}`,destination:'valuation'};}
export function prioritizeTasks(tasks:readonly ResearchTask[],done:Readonly<Record<string,string>>):ResearchTask[]{
 const weight:Record<ResearchTaskKind,number>={model:4,source:3,ai:2,event:1};
 return [...new Map(tasks.map(t=>[t.id,t])).values()].filter(t=>done[t.id]!=='done').sort((a,b)=>weight[b.kind]-weight[a.kind]||b.date.localeCompare(a.date));
}
