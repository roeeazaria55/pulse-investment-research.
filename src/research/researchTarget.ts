import {suppliedFor,suppliedValue} from '../data/suppliedResearch';
import {companyModelFor} from '../data/companyModels';
import {modelValue} from './scenarioModel';
interface ResearchTarget {target:number;currency:string;horizon:string;label:string;note:string;approximate:boolean;weights:string;caption?:string;horizonLabel?:string}
export function researchTarget(id:string):ResearchTarget|null{
 const report=suppliedFor(id);
 if(report)return {target:suppliedValue(report),currency:'USD',horizon:report.method==='ev-sales'?'2027-10-20':'',horizonLabel:report.method==='eps'?'רווחי FY2028 · ללא מועד יעד קשיח':'מודל ל־12 חודשים מ־20.10.2026',label:'הניתוח החדש · PDF מ־20.10.2026',caption:'שווי משוקלל לפי הנחות המסמך',note:report.method==='eps'?'הערכת שווי על רווחי FY2028, לא מחיר יעד קשיח ל־12 חודשים':'מודל מכפילים ראשוני; חוב נטו ומניות הם הנחות פשטניות',approximate:true,weights:'דוב 20% · בסיס 50% · שור 30%'};
 const m=companyModelFor(id);if(!m)return null;
 return {target:modelValue(m)!.weighted,currency:m.quoteCurrency,horizon:m.horizonDate,label:'מודל מחושב ראשוני',note:'מותנה בהנחות המחקר',approximate:false,weights:'20% / 50% / 30%'};
}
