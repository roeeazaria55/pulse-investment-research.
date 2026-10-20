import {SuppliedResearchReading} from './SuppliedResearch';
import {suppliedFor} from '../data/suppliedResearch';
import type {AnalysisImport} from '../research/exchange';
export const hasFullResearch=(companyId:string)=>!!suppliedFor(companyId);
export function FullCompanyResearch({analysis}:{analysis:AnalysisImport}){return <SuppliedResearchReading companyId={analysis.companyId}/>;}
