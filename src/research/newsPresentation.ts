import type {News} from '../types';
// Remove a repeated attribution only when it exactly matches the named publisher.
// The original title remains available in the source details.
export function readableHeadline(headline:string,publisher?:string){
 const suffix=publisher?` - ${publisher}`:'';
 return suffix&&headline.endsWith(suffix)&&headline.length>suffix.length?headline.slice(0,-suffix.length):headline;
}

export function compareNews(a:News,b:News,sort:string){
 const score=(n:News)=>n.rating?.eventScore??({high:3,medium:2,low:1}[n.importance]);
 return sort==='important'?score(b)-score(a):Date.parse(b.publishedAt||b.collectedAt)-Date.parse(a.publishedAt||a.collectedAt);
}
