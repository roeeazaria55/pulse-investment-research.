import {it,expect,vi} from 'vitest';
import {readDocument,MAX_FILE_BYTES} from '../src/research/readDocument';
const fake=(name:string,text:string,size=text.length)=>({name,size,text:async()=>text} as File);
it('reads provided TXT text and rejects oversized and unsupported files',async()=>{
 expect(await readDocument(fake('report.txt','USER TEXT'))).toMatchObject({text:'USER TEXT',scope:'קובץ טקסט מלא'});
 await expect(readDocument(fake('large.pdf','',MAX_FILE_BYTES+1))).rejects.toThrow('8MB');
 await expect(readDocument(fake('script.html','<script>'))).rejects.toThrow('PDF');
 await expect(readDocument(fake('report.pdf',''),0,1)).rejects.toThrow('עמוד התחלה');
 await expect(readDocument(fake('report.pdf',''),1,21)).rejects.toThrow('עמוד התחלה');
});
