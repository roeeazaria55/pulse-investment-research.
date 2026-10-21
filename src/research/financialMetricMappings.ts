export interface Mapping {companyId:string;metricId:string;concepts:string[];basis:string;divisor:number;unit:string;fiscalJune?:boolean}
// Explicit semantic mappings only. No inferred PDF columns, company extensions, adjusted or normalized measures.
export const mappings:readonly Mapping[]=[
 {companyId:'us-smci-nasdaq-common',metricId:'revenue',concepts:['us-gaap:revenues','us-gaap:revenuefromcontractwithcustomerexcludingassessedtax'],basis:'revenue',divisor:1e9,unit:'USD billion',fiscalJune:true},
 {companyId:'us-smci-nasdaq-common',metricId:'cashflow',concepts:['us-gaap:netcashprovidedbyusedinoperatingactivities'],basis:'operating cash flow',divisor:1e9,unit:'USD billion',fiscalJune:true},
 {companyId:'candidate-brainsway',metricId:'revenue',concepts:['us-gaap:revenues','us-gaap:revenuefromcontractwithcustomerexcludingassessedtax'],basis:'revenue',divisor:1e6,unit:'USD million'},
 {companyId:'candidate-brainsway',metricId:'profit',concepts:['us-gaap:operatingincomeloss'],basis:'operating income',divisor:1e6,unit:'USD million'},
];

export const metricsWithSemanticMapping=(companyId:string)=>new Set(mappings.filter(m=>m.companyId===companyId).map(m=>m.metricId));
