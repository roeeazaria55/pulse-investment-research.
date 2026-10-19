// USD millions and millions of shares. Every capital input is at the scenario horizon.
export type ValuationInputs = { revenue:number; multiple:number; cash:number; debt:number; shares:number; discount:number; years:number };
export function valueScenario(x:ValuationInputs) {
 if(Object.values(x).some(v=>!Number.isFinite(v)||v<0)||x.shares<=0||x.revenue>1e9||x.multiple>1000||x.cash>1e9||x.debt>1e9||x.shares>1e9||x.discount>100||x.years>100)return null;
 const enterprise=x.revenue*x.multiple;
 const equity=enterprise+x.cash-x.debt;
 const terminal=Math.max(0,equity)/x.shares;
 const present=terminal/Math.pow(1+x.discount/100,x.years);
 return {enterprise,equity,terminal,present};
}
