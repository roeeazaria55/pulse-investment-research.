import {useEffect,useState} from 'react';
import {parseReportIntake,type ReportIntakeSnapshot} from '../data/reportIntake';
/** Each consumer owns an abortable request; no stale company-specific state survives a switch. */
export function useReportIntake(companyId:string){
 const [data,setData]=useState<ReportIntakeSnapshot|null>(null),[failed,setFailed]=useState(false);
 useEffect(()=>{const controller=new AbortController();setData(null);setFailed(false);
  fetch(`${import.meta.env.BASE_URL}data/report-intake.json`,{cache:'no-store',signal:controller.signal}).then(r=>{if(!r.ok)throw Error('unavailable');return r.json();}).then(parseReportIntake).then(x=>{if(!controller.signal.aborted)setData(x);}).catch(()=>{if(!controller.signal.aborted)setFailed(true);});
  return ()=>controller.abort();
 },[companyId]);
 return {data,failed};
}
