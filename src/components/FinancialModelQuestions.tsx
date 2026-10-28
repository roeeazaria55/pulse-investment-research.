import {companyModelFor} from '../data/companyModels';
import {fieldLabels} from '../research/scenarioModel';
import type {ResearchMetric} from './LatestResearchUpdate';

const paths:Record<string,string[]>={
 revenue:['driver','revenue'],aiRevenue:['revenue'],tpv:['driver'],grossProfit:['margin','ebitdaMargin'],operatingIncome:['margin','corporate','depreciation'],
 netIncome:['margin','netFinance','tax'],commonNetIncome:['preferred','shares'],
 operatingCash:['operatingCash','netAdvances'],capex:['capex','knownFunding','facilityDebt'],
 cash:['minimumCash','knownFunding'],debt:['facilityDebt','repayment','netFinance'],inventory:['operatingCash'],accountsReceivable:['operatingCash'],
 grossLossRatio:['margin'],adjustedEbitda:['ebitdaMargin','margin'],grossEarnedPremium:['revenue'],inForcePremium:['revenue'],
};
export function FinancialModelQuestions({companyId,metrics}:{companyId:string;metrics:ResearchMetric[]}){
 const model=companyModelFor(companyId);
 const base=model?.scenarios.find(s=>s.id==='base');
 if(!metrics.length)return null;
 return <section aria-label="השפעה אפשרית על הנחות המודל">
  <h5>השפעה אפשרית על הנחות המודל</h5>
  <p>קשרים לבדיקה בלבד. אין התאמת תחזית, מחיר יעד או הסתברות; השוואה שנתית אינה Beat/Miss.</p>
  {model&&base?<>
   <p>מודל קיים: {model.ticker} · {model.analysisDate} · {model.earningsPeriod}</p>
   <ul>{metrics.map(m=>{
    const keys=(paths[m.id]||[]).filter(k=>Number.isFinite(base.inputs[k]));
    return <li key={m.id}><strong>{m.label}:</strong> {keys.length?
     <>יש לבדוק את {keys.map(k=>`${fieldLabels[k]||k}: ${base.inputs[k].toLocaleString('en-US')}`).join(' · ')}. האם השינוי המדווח רלוונטי לתקופה, להגדרה ולמטבע של ההנחה?</>:
     <>אין שדה כמותי תואם במודל הקיים; נדרש בירור אנליסט לפני יצירת קשר מספרי.</>}
     {['grossProfit','adjustedEbitda'].includes(m.id)&&<small> רווח גולמי, EBITDA ורווח תפעולי הם הגדרות שונות; הקשר לבדיקה אינו שקילות חשבונאית.</small>}
    </li>;
   })}</ul>
   <p><small>הנחות כספיות במיליוני {model.reportCurrency}; אחוזים ומניות מסומנים בשם השדה. מקור: מודל התרחישים הקיים של {model.ticker}. ייתכן שמחקר שסופק מציג הערכת שווי אחרת.</small></p>
  </>:<p>לא נמצא מודל כמותי תואם. יש להשוות ידנית למחקר הקיים; לא נוצרה הנחה חדשה.</p>}
 </section>;
}
