import sandisk from '../data/sandisk-original.json';
import historical from '../data/nbis-12-month-model.json';
import {companyModelFor} from '../data/companyModels';
import {modelValue} from './scenarioModel';
export function researchTarget(id:string){
 if(id===sandisk.companyId)return {target:sandisk.reportedWeightedTarget,currency:'USD',horizon:sandisk.inferredHorizonDate,label:'הניתוח המקורי שלנו · 7.10.2026',note:'יעד מקורב כפי שנרשם בשיחה; המשקולות לא שוחזרו. סוף האופק נגזר ממועד השיחה',approximate:true,weights:'משקולות לא שוחזרו'};
 if(id===historical.companyId)return {target:historical.scenarios.reduce((sum,s)=>sum+s.target*s.probability/100,0),currency:'USD',horizon:historical.horizonDate,label:'המודל המקורי שלנו · 15.10.2026',note:'יעדים משוחזרים מהשיחה; לא אומתו מחדש',approximate:false,weights:'20% / 50% / 30%'};
 const m=companyModelFor(id);if(!m)return null;
 return {target:modelValue(m)!.weighted,currency:m.quoteCurrency,horizon:m.horizonDate,label:'מודל מחושב ראשוני',note:'מותנה בהנחות המחקר',approximate:false,weights:'20% / 50% / 30%'};
}
