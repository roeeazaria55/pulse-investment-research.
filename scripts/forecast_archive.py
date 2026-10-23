"""Immutable forecast archive anchored to its first observed repository snapshot.

A self-stated research 'asOf' date is not a verified historical creation
timestamp. Prospective comparison must use firstRecordedAt instead.
"""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

VERSION=1

def valid_day(day):
    if not isinstance(day,str):return False
    try:return dt.date.fromisoformat(day).isoformat()==day
    except ValueError:return False

def valid_instant(value):
    if not isinstance(value,str) or len(value)>80:return False
    try:return bool(value and dt.datetime.fromisoformat(value.replace("Z","+00:00")).tzinfo)
    except (ValueError,AttributeError):return False

CHRONOLOGY = "research-asof-unverified; firstRecordedAt is verified archive boundary"

def forecast_identity(body):
    """Content-address a forecast's full definition; never its claimed timestamp."""
    encoded=json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False)
    return "forecast:"+hashlib.sha256(encoded.encode()).hexdigest()[:32]

def validated_history(previous,now):
    """Fail closed on malformed persisted pulse-data instead of silently copying it.

    The checksum is an integrity/consistency check, NOT proof that an attacker
    could not re-hash a forged record. The data branch is not an approval source.
    """
    if not isinstance(previous,dict) or previous.get("version",VERSION)!=VERSION:
        raise ValueError("Unsupported forecast archive version")
    rows=previous.get("forecasts",[])
    if not isinstance(rows,list):
        raise ValueError("Malformed persisted forecast archive")
    result={}
    upper=dt.datetime.fromisoformat(now.replace("Z","+00:00"))
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get("point"),dict):
            raise ValueError("Malformed persisted forecast record")
        point=row["point"]
        if (set(point)!={"value","period","unit","basis"}
            or isinstance(point["value"],bool)
            or not isinstance(point["value"],(int,float))
            or not math.isfinite(point["value"])
            or any(not isinstance(point[k],str) or not point[k] or len(point[k])>200
                   for k in ("period","unit","basis"))
            or any(not isinstance(row.get(k),str) or not row[k] or len(row[k])>120
                   for k in ("companyId","metricId"))
            or (row.get("researchAsOf") is not None and not valid_day(row["researchAsOf"]))):
            raise ValueError("Invalid persisted forecast definition")
        body={k:row[k] for k in ("companyId","metricId","point","researchAsOf")}
        expected=forecast_identity(body)
        if row.get("id")!=expected or expected in result:
            raise ValueError("Forecast archive identity mismatch or duplicate")
        stamp=row.get("firstRecordedAt")
        if not valid_instant(stamp) or dt.datetime.fromisoformat(stamp.replace("Z","+00:00"))>upper:
            raise ValueError("Forecast first-recorded timestamp is invalid or future-dated")
        if (row.get("canBeUsedForHistoricalBacktest") is not False
            or row.get("chronologyStatus")!=CHRONOLOGY
            or not isinstance(row.get("firstRecordedCommit"),str)
            or not 1<=len(row["firstRecordedCommit"])<=80):
            raise ValueError("Persisted forecast contains unsupported provenance or approval claims")
        result[expected]=row
    return result

def snapshot(monitors,previous,now,source_commit):
    if not valid_instant(now) or not isinstance(monitors,list) or not isinstance(previous,dict):
        raise ValueError("Invalid input snapshot")
    entries=validated_history(previous,now);new_count=0
    for monitor in monitors:
        if (not isinstance(monitor,dict) or not isinstance(monitor.get("metrics"),list)
            or not isinstance(monitor.get("companyId"),str)
            or not 1<=len(monitor["companyId"])<=120):
            continue
        seen=set()
        for m in monitor["metrics"]:
            if not isinstance(m,dict):
                continue
            metric_id=m.get("id")
            if not isinstance(metric_id,str) or not 1<=len(metric_id)<=120 or metric_id in seen:
                continue
            seen.add(metric_id)
            target=m.get("target")
            if not isinstance(target,dict) or any(k not in target for k in ("value","period","unit","basis")):
                continue
            if isinstance(target["value"],bool) or not isinstance(target["value"],(float,int)) or not math.isfinite(target["value"]):
                continue
            if any(not isinstance(target[k],str) or not 1<=len(target[k])<=200 for k in ("period","unit","basis")):
                continue
            # Only these four evidence fields are part of a forecast definition.
            # Never persist arbitrary metadata (including forged approval claims)
            # from monitor targets: it would fail next-run history validation.
            point={k:target[k] for k in ("value","period","unit","basis")}
            body={"companyId":monitor["companyId"],"metricId":metric_id,"point":point,
                  "researchAsOf":monitor.get("asOf") if valid_day(monitor.get("asOf")) else None}
            ident=forecast_identity(body)
            if ident in entries:
                continue
            entries[ident]={**body,"id":ident,"ticker":monitor.get("ticker"),"firstRecordedAt":now,
                "firstRecordedCommit":source_commit,
                "chronologyStatus":CHRONOLOGY,
                "canBeUsedForHistoricalBacktest":False,
                "notice":"Never claim the supplied research asOf is independently proven by this archive."}
            new_count+=1
    return {"version":VERSION,"updatedAt":now,"forecasts":sorted(entries.values(),key=lambda x:x["id"]),
            "newVersionCount":new_count,
            "notice":"Append-only forecast history. Comparisons require published results after firstRecordedAt, exact period/units/definition and approved actual source evidence."}

def main():
    project=Path(".")
    monitors=json.loads((project/"src/data/thesisMonitoring.json").read_text())
    output=project/"public/data/forecast-archive.json"
    old=json.loads(output.read_text()) if output.exists() else {}
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    # The commit supplied by Actions anchors *collection of the baseline*, not
    # the unverified original authorship of the forecast.
    import os
    commit=os.getenv("GITHUB_SHA") or "local-unverified"
    data=snapshot(monitors,old,now,commit)
    temp=output.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    temp.replace(output)
    print(json.dumps({"archived":len(data["forecasts"]),"new":data["newVersionCount"]}))

if __name__=="__main__":
    main()
