import {irenFy26,irenPulseForecasts} from '../research/irenFy26';
import {FinancialResults} from './FinancialResults';
export function IrenFinancialResults({companyId}:{companyId:string}){
 if(companyId!=='candidate-iren')return null;
 return <FinancialResults ticker="IREN" period="FY2026" testIdPrefix="iren-fy26" result={irenFy26} forecasts={irenPulseForecasts()} metadataLinkLabel="הודעת המנפיק">
  <p>נתונים מדוח המנפיק מ־27.08.2026. ערכי המקור נבדקו מול טבלאות הדוח וה־PDF; ממתינים לבדיקת אנליסט. זו תמצית מקור שמורה, לא קריאה חיה ולא עותק מלא של הקובץ.</p>
  <p><strong>FY2026 פורסם לפני מחקר PULSE מ־20.10.2026. הנתונים מוכיחים קליטה מהמקור; אינם הפתעה ואינם בדיקת איכות התחזית.</strong> תחזיות FY2027 והרבעונים העתידיים נשמרות להשוואה לתוצאות שיפורסמו לאחר מועד התחזית.</p>
  <p><a href={`${import.meta.env.BASE_URL}research/PULSE_IREN_Full_Research_HE_PreQ1FY27.pdf`} target="_blank" rel="noopener noreferrer">מחקר PULSE לקראת Q1 FY2027 · ללא שינוי ↗</a></p>
 </FinancialResults>;
}
