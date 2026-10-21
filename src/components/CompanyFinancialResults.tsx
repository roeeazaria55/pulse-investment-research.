import {IrenFinancialResults} from './IrenFinancialResults';
import {FinancialResults} from './FinancialResults';
import {smciFy26,smciPulseForecasts} from '../research/smciFy26';
import source from '../../public/data/smci-fy26-source.json';
export function CompanyFinancialResults({companyId}:{companyId:string}){
 if(companyId==='candidate-iren')return <IrenFinancialResults companyId={companyId}/>;
 if(companyId!=='us-smci-nasdaq-common')return null;
 return <FinancialResults ticker="SMCI" period="FY2026" testIdPrefix="smci-fy26" result={smciFy26} forecasts={smciPulseForecasts()} metadataLinkLabel="פרטי הגשת SEC">
  <p>דוח 10-K רשמי לשנה 01.07.2025–30.06.2026, שהוגש ל־SEC ב־31.08.2026. ערכי המקור נבדקו בדוחות המאוחדים בעמודים 59 ו־63 ובנתוני XBRL שנקלטו. זו תמצית מקור שמורה, לא קריאה חיה או עותק מלא; ממתינה לבדיקת אנליסט.</p>
  <p><strong>הדוח קדם למחקר PULSE. אלה נתוני בסיס; אינם הפתעה מול תחזית שנכתבה לאחר פרסומם.</strong> תחזית ההכנסות הקיימת מתייחסת ל־FY2027, ביחידות מיליארדי דולר. לא הוגדרה תחזית מספרית תואמת לרווח התפעולי או לתזרים FY2026. התחזיות והמחירים נשמרים ללא שינוי.</p>
  <p>התוצאות פורסמו כבר ב־11.08.2026 בהודעת המנפיק, לפני הגשת ה־10-K. חסימת השוואות בדיעבד משתמשת במועד המוקדם. <a href={source.resultsSourceUrl} target="_blank" rel="noopener noreferrer">פרסום התוצאות המקורי ↗</a></p>
  <p>הדוח מציג אלפי USD; התצוגה במיליוני USD מחלקת את ערכי המקור ב־1,000 ושומרת את סימן התזרים.</p>
 </FinancialResults>;
}
