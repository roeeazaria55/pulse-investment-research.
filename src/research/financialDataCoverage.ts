import {metricsWithSemanticMapping} from './financialMetricMappings';
import {thesisMonitors} from './thesisMonitoring';

/**
 * Phase 1 source coverage is an audit of implemented semantic mappings,
 * NOT a claim that issuer facts have been retrieved or verified.
 */
export type CompanyCoverage = {
 companyId:string;ticker:string;tracked:number;mapped:number;unmapped:string[];
 status:'mapping-partial'|'mapping-missing';
};
export function financialDataCoverage():CompanyCoverage[]{
 return thesisMonitors.map(company=>{
  const supported=metricsWithSemanticMapping(company.companyId);
  const ids=company.metrics.map(metric=>metric.id);
  const mapped=ids.filter(id=>supported.has(id)).length;
  return {
   companyId:company.companyId,ticker:company.ticker,tracked:ids.length,mapped,
   unmapped:ids.filter(id=>!supported.has(id)),
   status:mapped>0?'mapping-partial':'mapping-missing',
  };
 });
}
export function financialCoverageTotals(){
 const companies=financialDataCoverage();
 return {
  companies:companies.length,
  monitoredMetrics:companies.reduce((sum,c)=>sum+c.tracked,0),
  mappedMetrics:companies.reduce((sum,c)=>sum+c.mapped,0),
  companiesWithMapping:companies.filter(c=>c.mapped>0).length,
  issuerVerifiedMetrics:0, // Validation requires separately reviewed source evidence.
 };
}
