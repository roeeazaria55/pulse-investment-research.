export type ContentKind='approved'|'ai-draft'|'source-pending'|'baseline';
const labels:Record<ContentKind,string>={approved:'מחקר מאושר','ai-draft':'טיוטת AI','source-pending':'נתון ממתין לאימות',baseline:'מחקר שמור · לא מאומת'};
export function ContentBadge({kind}:{kind:ContentKind}){return <span className={`content-badge content-badge-${kind}`}>{labels[kind]}</span>;}
