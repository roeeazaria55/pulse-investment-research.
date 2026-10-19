import {modelValue,validDate,type CompanyModel} from '../research/scenarioModel';
import {officialRegistry} from './official';
const files=import.meta.glob('./models/*.json',{eager:true,import:'default'}) as Record<string,CompanyModel>;
export const companyModels=Object.values(files);
for(const m of companyModels){
 const end=new Date(m.analysisDate);end.setUTCFullYear(end.getUTCFullYear()+1);
 if(m.version!==1||!officialRegistry.companies.some(c=>c.id===m.companyId)||!validDate(m.analysisDate)||!validDate(m.horizonDate)||end.toISOString().slice(0,10)!==m.horizonDate||!modelValue(m)||!m.facts.length)throw Error('Invalid company valuation: '+m.ticker);
}
if(new Set(companyModels.map(m=>m.companyId)).size!==companyModels.length)throw Error('Duplicate company valuation');
export const companyModelFor=(id:string)=>companyModels.find(m=>m.companyId===id);
export const modelMoney=(n:number,currency:string)=>`${currency==='ILS'?'₪':'$'}${n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}`;
