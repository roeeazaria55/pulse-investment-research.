import type {ReportIntakeSnapshot} from '../data/reportIntake';
import type {ThesisMetric} from './thesisMonitoring';
import {metricComparison} from './thesisMonitoring';
import {reportComparison} from './reportComparison';

export type ReportComparisonStatus = 'comparable'|'period'|'definition'|'qualitative'|'missing'|'unsupported'|'conflict'|'review';
export interface ReportComparisonSummary {
 total:number;
 comparable:number;
 needsReview:number;
 waiting:number;
 entries:{metricId:string;status:ReportComparisonStatus;label:string;difference:number|null;percent:number|null}[];
}
/** Candidate-only scoreboard: compares only source-mapped, same-period, same-definition numbers. */
export function summarizeReportComparisons(
 data:ReportIntakeSnapshot,
 companyId:string,
 metrics:readonly ThesisMetric[],
):ReportComparisonSummary {
 const entries=metrics.map(metric=>{
  const intake=reportComparison(data,companyId,metric);
  if(intake.status!=='mapped')return {
   metricId:metric.id,
   status:intake.status as ReportComparisonStatus,
   label:intake.label,
   difference:null,
   percent:null,
  };
  const comparison=metricComparison(intake.observation!.point,metric.target);
  return {
   metricId:metric.id,
   status:comparison.status as ReportComparisonStatus,
   label:comparison.label,
   difference:comparison.status==='comparable'?comparison.difference:null,
   percent:comparison.status==='comparable'?comparison.percent:null,
  };
 });
 return {
  total:entries.length,
  comparable:entries.filter(e=>e.status==='comparable').length,
  needsReview:entries.filter(e=>e.status==='conflict'||e.status==='review').length,
  waiting:entries.filter(e=>e.status!=='comparable'&&e.status!=='conflict'&&e.status!=='review').length,
  entries,
 };
}
