export type Inputs=Record<string,number>;
export type Scenario={id:string;label:string;probability:number;inputs:Inputs;rationale:string};
export type Capital={cash:number;shares:number;seniorDebt:number;notes:{id:string;original:number;claim:number;rate:number}[];warrants:{shares:number;strike:number}[]};
export type CompanyModel={version:number;companyId:string;ticker:string;analysisDate:string;horizonDate:string;earningsPeriod:string;quoteCurrency:'USD'|'ILS';reportCurrency:'USD'|'ILS';method:'earnings'|'sales'|'funded-ev';driverLabel:string;methodNote:string;facts:{text:string;url:string}[];checks:string[];limitations:string[];reference:null|{price:number;date:string;url:string;label:string};scenarios:Scenario[];capital?:Capital};
export const fieldLabels:Record<string,string>={driver:'בסיס פעילות שנתי',margin:'שיעור רווח תפעולי (%)',corporate:'עלויות מטה והתאמות שנתיות',depreciation:'פחת והפחתות שנתיים',netFinance:'הכנסות מימון נטו (הוצאה במינוס)',tax:'שיעור מס (%)',minority:'רווח לבעלי זכויות מיעוט',preferred:'דיבידנד בכורה',shares:'מניות מדוללות צפויות (מיליונים)',multiple:'מכפיל במועד היעד',fx:'שקלים לדולר בהמרה',revenue:'הכנסות שנתיות',ebitdaMargin:'שיעור EBITDA מתואם (%)',knownFunding:'מימון מתוכנן/ידוע נטו מאז המאזן',facilityDebt:'תוספת חוב ממסגרות מאז המאזן',releasedCash:'שחרור מזומן מוגבל להשקעה',operatingCash:'תזרים מצטבר אחרי ריבית ומס, ללא מקדמות',netAdvances:'שינוי נטו במקדמות לקוחות',capex:'השקעות מצטברות מאז המאזן',acquisition:'מזומן לרכישות מאז המאזן',repayment:'פירעון קרן חוב בכיר וחכירות',minimumCash:'רזרבת מזומן בסוף התקופה',debtShare:'שיעור חוב במימון החסר (%)',issuePrice:'מחיר הנפקה עתידית למניה',newAwards:'מניות נוספות מעבר לבסיס (מיליונים)',fees:'עלות גיוס (%)',noncore:'שווי החזקות מחוץ לפעילות',accretion:'חלק מתוספת פירעון אג״ח מלאה (%)'};
export function inputKeys(method:CompanyModel['method']){return method==='earnings'?['driver','margin','corporate','depreciation','netFinance','tax','minority','preferred','shares','multiple','fx']:method==='sales'?['revenue','shares','multiple','fx']:['revenue','ebitdaMargin','multiple','knownFunding','facilityDebt','releasedCash','operatingCash','netAdvances','capex','acquisition','repayment','minimumCash','debtShare','issuePrice','newAwards','fees','noncore','accretion','fx'];}
export type ModelResult={target:number;equity:number;earnings:number|null;eps:number|null;enterprise:number|null;cash:number|null;gap:number;newDebt:number;newEquity:number;fundingShares:number;shares:number;debt:number|null;converted:string[]};
export function scenarioValue(model:CompanyModel,x:Inputs):ModelResult|null{
 const keys=inputKeys(model.method),signed=['netFinance','operatingCash','netAdvances'];
 if(keys.some(k=>!Number.isFinite(x[k])||Math.abs(x[k])>1e8||(!signed.includes(k)&&x[k]<0))||x.fx<=0||x.fx>1000||x.multiple>1000)return null;
 if(['margin','tax','ebitdaMargin','debtShare','accretion'].some(k=>keys.includes(k)&&x[k]>100)||keys.includes('fees')&&x.fees>=100)return null;
 if(model.method!=='funded-ev'){
  if(x.shares<.000001)return null;
  const pre=model.method==='earnings'?x.driver*x.margin/100-x.corporate-x.depreciation+x.netFinance:0;
  // No automatic tax credit on losses; minority and preferred claims remain explicit.
  const earnings=model.method==='earnings'?pre-Math.max(0,pre)*x.tax/100-x.minority-x.preferred:null;
  const equity=Math.max(0,model.method==='earnings'?earnings!*x.multiple:x.revenue*x.multiple);
  return {target:equity/x.shares*x.fx,equity,earnings,eps:earnings===null?null:earnings/x.shares,enterprise:null,cash:null,gap:0,newDebt:0,newEquity:0,fundingShares:0,shares:x.shares,debt:null,converted:[]};
 }
 const c=model.capital;
 if(!c||x.issuePrice<.000001||c.shares<=0||x.repayment>c.seniorDebt+x.facilityDebt)return null;
 const before=c.cash+x.knownFunding+x.releasedCash+x.operatingCash+x.netAdvances-x.capex-x.acquisition-x.repayment;
 const gap=Math.max(0,x.minimumCash-before),net=1-x.fees/100;
 const newDebt=gap*x.debtShare/100/net,newEquity=gap*(1-x.debtShare/100)/net;
 const fundingShares=newEquity/x.issuePrice,shares=c.shares+x.newAwards+fundingShares;
 const cash=before+(newDebt+newEquity)*net,senior=c.seniorDebt+x.facilityDebt+newDebt-x.repayment;
 const enterprise=x.revenue*x.ebitdaMargin/100*x.multiple,assets=enterprise+cash+x.noncore;
 const notes=c.notes.map(n=>({...n,claim:n.original+(n.claim-n.original)*x.accretion/100,shares:n.original*n.rate/1000}));
 const claims=(p:number)=>p*shares+senior+notes.reduce((s,n)=>s+Math.max(n.claim,p*n.shares),0)+c.warrants.reduce((s,w)=>s+Math.max(0,p-w.strike)*w.shares,0);
 let lo=0,hi=Math.max(0,assets/shares);
 for(let i=0;i<100;i++){const mid=(lo+hi)/2;if(claims(mid)>assets)hi=mid;else lo=mid;}
 const price=claims(0)>=assets?0:(lo+hi)/2,converted=notes.filter(n=>price*n.shares>n.claim).map(n=>n.id);
 const extra=notes.filter(n=>converted.includes(n.id)).reduce((s,n)=>s+n.shares,0)+c.warrants.filter(w=>price>w.strike).reduce((s,w)=>s+w.shares,0);
 return {target:price*x.fx,equity:price*(shares+extra),earnings:null,eps:null,enterprise,cash:cash+c.warrants.filter(w=>price>w.strike).reduce((s,w)=>s+w.strike*w.shares,0),gap,newDebt,newEquity,fundingShares,shares:shares+extra,debt:senior+notes.filter(n=>!converted.includes(n.id)).reduce((s,n)=>s+n.claim,0),converted};
}
export function modelValue(model:CompanyModel,scenarios=model.scenarios){
 if(scenarios.length!==3||new Set(scenarios.map(s=>s.id)).size!==3||scenarios.some(s=>!Number.isFinite(s.probability)||s.probability<0||s.probability>100)||Math.abs(scenarios.reduce((sum,s)=>sum+s.probability,0)-100)>1e-6)return null;
 const results=scenarios.map(s=>scenarioValue(model,s.inputs));if(results.some(r=>!r))return null;
 return {results:results as ModelResult[],weighted:results.reduce((sum,r,i)=>sum+r!.target*scenarios[i].probability/100,0)};
}
export function validDate(raw:string){return /^\d{4}-\d{2}-\d{2}$/.test(raw)&&Number.isFinite(Date.parse(raw))&&new Date(raw).toISOString().slice(0,10)===raw;}
