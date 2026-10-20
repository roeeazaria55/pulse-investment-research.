import raw from './suppliedResearch.json';
export interface ResearchTable {type:'table';columns:string[];rows:string[][]}
export interface ResearchParagraph {type:'paragraph';text:string}
export interface SuppliedSection {number:number;title:string;blocks:(ResearchTable|ResearchParagraph)[]}
export interface SuppliedScenario {id:string;label:string;weight:number;multiple:number;revenue?:number;netDebt?:number;shares?:number;eps?:number;netIncome?:number;statedValue?:number}
export interface SuppliedResearch {companyId:string;ticker:string;date:string;reference:number;filename:string;horizonLabel:string;summary:string;method:'ev-sales'|'eps'|'earnings'|'stated';earningsPeriod?:string;referenceDate?:string|null;horizonDate?:string;horizonNote?:string;reportedWeighted?:number;arithmeticNote?:string;unitNote?:string;unitSource?:string;instrumentLabel?:string;secondaryFrom?:number;scenarios:SuppliedScenario[];notice:string;sources:string[];sections:SuppliedSection[];pages:number;sha256:string;sourceDescription?:string}
export const suppliedResearch=raw as SuppliedResearch[];
export function suppliedScenarioValue(report:SuppliedResearch,scenario:SuppliedScenario){return report.method==='stated'?scenario.statedValue!:report.method==='earnings'?scenario.netIncome!/scenario.shares!*scenario.multiple:report.method==='eps'?scenario.eps!*scenario.multiple:(scenario.revenue!*scenario.multiple-scenario.netDebt!)/scenario.shares!;}
export function suppliedValue(report:SuppliedResearch){return report.scenarios.reduce((sum,s)=>sum+suppliedScenarioValue(report,s)*s.weight/100,0);}
for(const r of suppliedResearch){
 if(r.scenarios.length!==3||r.scenarios.reduce((sum,s)=>sum+s.weight,0)!==100||!Number.isFinite(suppliedValue(r))||r.sections.some((s,i)=>s.number!==i+1)||r.sections.some(s=>s.blocks.some(b=>b.type==='table'&&b.rows.some(row=>row.length!==b.columns.length))))throw Error('Invalid supplied research: '+r.ticker);
}
export const suppliedFor=(id:string)=>suppliedResearch.find(r=>r.companyId===id);
export const suppliedPdfUrl=(report:SuppliedResearch)=>`${import.meta.env.BASE_URL}research/${report.filename}`;
