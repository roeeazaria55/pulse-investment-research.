import {IrenFinancialResults} from './IrenFinancialResults';
import {FinancialResults} from './FinancialResults';
import {smciFy26,smciPulseForecasts} from '../research/smciFy26';
import source from '../../public/data/smci-fy26-source.json';
import {nbisQ22026,nbisPulseForecasts} from '../research/nbisQ22026';
import {dloQ22026,dloPulseForecasts} from '../research/dloQ22026';
export function CompanyFinancialResults({companyId}:{companyId:string}){
 if(companyId==='candidate-iren')return <IrenFinancialResults companyId={companyId}/>;
 if(companyId==='candidate-nebius')return <FinancialResults ticker="NBIS" period="Q2 2026" testIdPrefix="nbis-q2-2026" result={nbisQ22026} forecasts={nbisPulseForecasts()} metadataLinkLabel="הודעת תוצאות המנפיק">
  <p>תוצאות מאוחדות לרבעון אפריל–יוני 2026 מתוך נספח 99.1 להגשת SEC, עמודים 7–8. זו תמצית מקור שמורה וממתינה לבדיקת אנליסט, ולא קליטה אוטומטית של דוח חדש.</p>
  <p>התזרים התפעולי כולל השפעת מקדמות לקוחות; ההשקעות המוצגות הן תשלומי רכוש קבוע ונכסים בלתי מוחשיים בלבד. אין להסיק מהם תזרים מנורמל או EBITDA מתואם.</p>
  <p>התוצאות פורסמו ב־12.08.2026, לפני מחקר PULSE. לכן לא תוצג הפתעה בדיעבד או השוואה בין תקופות שונות.</p>
 </FinancialResults>;
 if(companyId==='us-dlo-nasdaq-a')return <FinancialResults ticker="DLO" period="Q2 2026" testIdPrefix="dlo-q2-2026" result={dloQ22026} forecasts={dloPulseForecasts()} metadataLinkLabel="הודעת המנפיק">
  <p>תוצאות הרבעון שהסתיים ב־30.06.2026 מהודעת החברה מ־13.08.2026. מדדי ההכנסות והרווח מעוגלים לעשירית מיליון דולר; ה־CAPEX חושב מאלפי דולר לפי גישור ה־Adjusted FCF של המנפיק. כל המדדים ממתינים לבדיקת אנליסט.</p>
  <p>תזרים תפעולי IFRS לא ממופה כאן, משום שהוא אינו זהה ל־Adjusted Free Cash Flow. לא מבוצעת השלמת נתונים או השוואה בדיעבד.</p>
 </FinancialResults>;
 if(companyId!=='us-smci-nasdaq-common')return null;
 return <FinancialResults ticker="SMCI" period="FY2026" testIdPrefix="smci-fy26" result={smciFy26} forecasts={smciPulseForecasts()} metadataLinkLabel="פרטי הגשת SEC">
  <p>דוח 10-K רשמי לשנה 01.07.2025–30.06.2026, שהוגש ל־SEC ב־31.08.2026. ערכי המקור נבדקו בדוחות המאוחדים בעמודים 59 ו־63 ובנתוני XBRL שנקלטו. זו תמצית מקור שמורה, לא קריאה חיה או עותק מלא; ממתינה לבדיקת אנליסט.</p>
  <p><strong>הדוח קדם למחקר PULSE. אלה נתוני בסיס; אינם הפתעה מול תחזית שנכתבה לאחר פרסומם.</strong> תחזית ההכנסות הקיימת מתייחסת ל־FY2027, ביחידות מיליארדי דולר. לא הוגדרה תחזית מספרית תואמת לרווח התפעולי או לתזרים FY2026. התחזיות והמחירים נשמרים ללא שינוי.</p>
  <p>התוצאות פורסמו כבר ב־11.08.2026 בהודעת המנפיק, לפני הגשת ה־10-K. חסימת השוואות בדיעבד משתמשת במועד המוקדם. <a href={source.resultsSourceUrl} target="_blank" rel="noopener noreferrer">פרסום התוצאות המקורי ↗</a></p>
  <p>הדוח מציג אלפי USD; התצוגה במיליוני USD מחלקת את ערכי המקור ב־1,000 ושומרת את סימן התזרים.</p>
 </FinancialResults>;
}
