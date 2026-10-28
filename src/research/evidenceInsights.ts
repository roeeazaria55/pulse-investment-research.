/** Source-bound arithmetic only. No AI, analyst approval, or valuation mutation. */
export interface EvidenceMetric {
 id:string; label:string; value:number; previousValue:number|null;
 periodStart:string; periodEnd:string; previousPeriodStart?:string|null; previousPeriodEnd?:string|null;
 unit:string; reviewStatus:string; sourceUrl:string;
}
export interface EvidenceInsight {
 metricId:string; label:string; current:number; previous:number;
 difference:number; changePercent:number|null; unit:string; comparisonLabel:string;
 sourceUrl:string; reviewStatus:'pending-review'; kind:'calculation';
 hypothesis:string; thesisStatus:'requires-analyst-review';
}
const questions:Record<string,string>={
 revenue:'האם השינוי בהכנסות נובע מביקוש, תמחור, תמהיל או שינוי חד־פעמי?',
 grossProfit:'האם העלויות והתמהיל שינו את הרווחיות באופן מתמשך?',
 operatingIncome:'האם השינוי משקף מנוף תפעולי או הוצאה חד־פעמית?',
 netIncome:'האם שינויי מס, מימון או רכיבים חד־פעמיים השפיעו על הרווח?',
 operatingCash:'האם תזמון גבייה, מקדמות או הון חוזר מסבירים את התזרים?',
 capex:'האם ההשקעה צפויה להגדיל קיבולת או לפגוע בתזרים החופשי?',
 cash:'האם יתרת המזומנים משקפת גיוס, פעילות שוטפת או השקעות?',
 debt:'האם הגידול בחוב משנה את סיכון המימון?',
 aiRevenue:'האם הכנסות ה־AI משקפות פעילות חוזרת ולא רק הכנסות חד־פעמיות?',
 tpv:'האם שינוי נפח התשלומים תואם לשינוי ברווח גולמי ובתמחור?',
};
const day=(value:string|null|undefined)=>{
 if(!value||!/^\d{4}-\d{2}-\d{2}$/.test(value))return null;
 const stamp=Date.parse(value+'T00:00:00Z');
 return Number.isFinite(stamp)&&new Date(stamp).toISOString().slice(0,10)===value?stamp:null;
};
function periodsComparable(m:EvidenceMetric){
 const a=day(m.periodStart),b=day(m.periodEnd),c=day(m.previousPeriodStart),d=day(m.previousPeriodEnd);
 if(a===null||b===null||c===null||d===null||a>b||c>d||d>=b)return false;
 // Balance-sheet values compare as-of dates; flows require equal duration.
 return a===b?c===d:a!==b&&c!==d&&b-a===d-c;
}
export function buildEvidenceInsights(metrics:readonly EvidenceMetric[],reportStatus:string):EvidenceInsight[]{
 if(reportStatus==='needs-reconciliation'||reportStatus==='insufficient-evidence')return [];
 const result:EvidenceInsight[]=[];
 for(const m of metrics){
  if(m.reviewStatus!=='pending-review'||!questions[m.id]||m.previousValue===null||
   !Number.isFinite(m.value)||!Number.isFinite(m.previousValue)||!periodsComparable(m)||
   !/^https:\/\//.test(m.sourceUrl))continue;
  const prev=m.previousValue;
  const difference=m.value-prev;
  if(!Number.isFinite(difference))continue;
  const isPercent=m.unit==='percent';
  // Negative, zero or sign-crossing baselines have no meaningful percentage growth.
  const percent=!isPercent&&prev>0&&m.value>=0&&Number.isFinite(difference/prev*100)?
   Math.round(difference/prev*10000)/100:null;
  result.push({
   metricId:m.id,label:m.label,current:m.value,previous:prev,
   difference:Number(difference.toFixed(6)),changePercent:percent,unit:m.unit,
   comparisonLabel:m.periodStart===m.periodEnd?'השוואת שתי נקודות מאזן':'תקופות דיווח באורך תואם',
   sourceUrl:m.sourceUrl,reviewStatus:'pending-review',kind:'calculation',
   hypothesis:questions[m.id],thesisStatus:'requires-analyst-review'
  });
 }
 return result;
}
