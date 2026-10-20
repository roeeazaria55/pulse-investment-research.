import raw from '../data/thesisMonitoring.json';
import {suppliedFor} from '../data/suppliedResearch';
export interface MetricPoint {value:number;period:string;unit:string;basis:string}
export interface ThesisMetric {id:string;title:string;section:number;targetSection:number;baseline:string;observed:MetricPoint|null;expectation:string;target:MetricPoint|null;why:string;nextCheck:string;thesisRisk:string}
export interface ThesisMonitor {companyId:string;ticker:string;asOf:string;metrics:ThesisMetric[]}
export const thesisMonitors=raw as ThesisMonitor[];
export const thesisMonitorFor=(id:string)=>thesisMonitors.find(m=>m.companyId===id);
/** A numerical gap is meaningful only for the same period, unit and accounting definition. */
export function metricComparison(observed:MetricPoint|null,target:MetricPoint|null){
 if(!target)return {status:'qualitative' as const,label:'מעקב איכותי · ללא סף מספרי'};
 if(!observed)return {status:'missing' as const,label:'חסרה תוצאה בת־השוואה'};
 if(observed.period!==target.period)return {status:'period' as const,label:'ממתין לתקופת התחזית'};
 if(observed.unit!==target.unit||observed.basis!==target.basis)return {status:'definition' as const,label:'נדרש גישור בין ההגדרות'};
 if(!Number.isFinite(observed.value)||!Number.isFinite(target.value))return {status:'missing' as const,label:'חסרה תוצאה בת־השוואה'};
 const difference=observed.value-target.value;
 return {status:'comparable' as const,label:'השוואה באותה תקופה והגדרה',difference,percent:target.value===0?null:difference/Math.abs(target.value)*100};
}
for(const monitor of thesisMonitors){
 const report=suppliedFor(monitor.companyId);
 if(!report||monitor.asOf!==report.date||monitor.metrics.length!==6||new Set(monitor.metrics.map(m=>m.id)).size!==6||monitor.metrics.some(m=>![m.section,m.targetSection].every(n=>report.sections.some(s=>s.number===n))))throw Error('Invalid thesis monitoring: '+monitor.ticker);
}
