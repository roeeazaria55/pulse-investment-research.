export interface Rating {
  version:string;eventKind:string;eventLabel:string;eventScore:number;potentialMateriality:number;
  level:'high'|'medium'|'low';sourceAuthority:string;sourceReliability:string;
  companyRelevance:'direct'|'context'|'rejected';confidence:'high'|'medium'|'low';basis:'headline-only'|'official-metadata';
  verifiedOfficial:boolean;independentConfirmations:number;why:string;evidenceUrls:string[];
}
export interface IndustryItem {id:string;industryId:string;headline:string;publisher:string;sourceUrl:string;linkKind:string;publishedAt:string|null;collectedAt:string}
export interface PublicSource {securityId?:string;industryId?:string;provider?:string;queryUrl?:string;url?:string|null;lastAttemptAt:string;lastSuccessfulAt:string|null;status:string;count?:number;error:string|null}
export interface EarningsEvent {id:string;revision:string;securityId:string;name:string;period:string|null;date:string|null;time:string|null;timeZone:string|null;timing:string|null;sourceUrl:string|null;status:'confirmed'|'estimated'|'unannounced';eventKind:'results-date'|'earnings-call'|'unknown';verifiedAt:string|null;verificationMethod:string;changedAt?:string;call?:{time:string;timeZone:string}|null}
export interface DailyCompany {securityId:string;name:string;searchStatus:string;facts:{eventId:string;itemId:string;textHe:string;originalTitle:string;sourceUrl:string;publishedAt:string;basis:string;publisher:string}[];undatedItemIds:string[];industryItemIds:string[];industryConnection:string;researchInterpretation:string;missing:string[]}
export interface DailyBriefing {id:string;date:string;startAt:string;endAt:string;timezone:string;scheduledLocalTime:string;generatedAt:string;kind:string;ratingVersion:string;companies:DailyCompany[];companySearchesSuccessful:number;industrySearchesSuccessful:number;summaryStatus:string;notice:string}
export interface Intelligence {
  version:1;generatedAt:string;ratingVersion:string;ratings:Record<string,Rating>;
  eventGroups:{id:string;securityId:string;eventKind:string;publicationDay:string;itemIds:string[];independentConfirmations:number;groupingBasis:string}[];
  industries:{items:IndustryItem[];sources:PublicSource[];config:{industries:{id:string;name:string;query:string;terms:string[]}[];companyIndustries:Record<string,string[]>}};
  calendar:{events:EarningsEvent[];sources:PublicSource[];lastAttemptAt:string;releases:{id:string;kind:string;securityId:string;name:string;period:string;sourceUrl:string;headline:string;publishedAt:string|null;firstDetectedAt:string;verifiedOfficial:boolean}[]};
  summary:{status:string;model:string;reason:string;proofRun:string};dailyBriefings:DailyBriefing[];notificationNotice:string;
}
