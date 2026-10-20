/** Phase-0 source-level arithmetic checks. Never authorizes valuation publication. */
export type ScenarioQuote = { id: 'bear'|'base'|'bull'; weight: number; price: number };
export type SourceValuationAudit = {
  status: 'consistent'|'discrepancy'|'invalid';
  calculated: number|null;
  declared: number;
  difference: number|null;
  roundingTolerance: number;
};
/** Compare the author's disclosed values without silently adjusting them. */
export function auditSourceValuation(
  scenarios: readonly ScenarioQuote[],
  declared: number,
  roundingTolerance = 0.01,
): SourceValuationAudit {
  const ids = new Set(scenarios.map(s=>s.id));
  const valid = scenarios.length===3 &&
    ids.size===3 && ids.has('bear') && ids.has('base') && ids.has('bull') &&
    scenarios.every(s=>Number.isFinite(s.weight)&&s.weight>=0&&s.weight<=100&&
      Number.isFinite(s.price)&&s.price>=0) &&
    Math.abs(scenarios.reduce((sum,s)=>sum+s.weight,0)-100)<1e-8 &&
    Number.isFinite(declared) && declared>=0 &&
    Number.isFinite(roundingTolerance) && roundingTolerance>=0;
  if(!valid)return {status:'invalid',calculated:null,declared,difference:null,roundingTolerance};
  const calculated=scenarios.reduce((sum,s)=>sum+s.price*s.weight/100,0);
  const difference=calculated-declared;
  return {status:Math.abs(difference)<=roundingTolerance+1e-10?'consistent':'discrepancy',
    calculated,difference,declared,roundingTolerance};
}
