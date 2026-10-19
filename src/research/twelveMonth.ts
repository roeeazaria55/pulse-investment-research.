export type TargetScenario={target:number;probability:number};
export function weightedTarget(scenarios:TargetScenario[],reference:number){
 if(scenarios.length!==3||!Number.isFinite(reference)||reference<0.000001||reference>1e6||scenarios.some(x=>!Number.isFinite(x.target)||x.target<0||x.target>1e6||!Number.isFinite(x.probability)||x.probability<0||x.probability>100))return null;
 const probability=scenarios.reduce((s,x)=>s+x.probability,0);
 if(Math.abs(probability-100)>0.000001)return null;
 const target=scenarios.reduce((s,x)=>s+x.target*x.probability/100,0);
 return {target,upside:(target/reference-1)*100};
}
