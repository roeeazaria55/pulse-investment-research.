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
    try:return bool(value and dt.datetime.fromisoformat(value.replace("Z","+00:00")).tzinfo)
    except (ValueError,AttributeError):return False

def snapshot(monitors,previous,now,source_commit):
    if not valid_instant(now) or not isinstance(monitors,list) or not isinstance(previous,dict):
        raise ValueError("Invalid input snapshot")
    old={entry["id"]:entry for entry in previous.get("forecasts",[]) if isinstance(entry,dict) and isinstance(entry.get("id"),str)}
    entries=dict(old);new_count=0
    for monitor in monitors:
        if not isinstance(monitor,dict) or not isinstance(monitor.get("metrics"),list) or not monitor.get("companyId"):
            continue
        seen=set()
        for m in monitor["metrics"]:
            if not isinstance(m,dict) or not m.get("id") or m["id"] in seen:
                continue
            seen.add(m["id"])
            target=m.get("target")
            if not isinstance(target,dict) or any(k not in target for k in ("value","period","unit","basis")):
                continue
            if isinstance(target["value"],bool) or not isinstance(target["value"],(float,int)) or not math.isfinite(target["value"]):
                continue
            if any(not isinstance(target[k],str) or not target[k] for k in ("period","unit","basis")):
                continue
            body={"companyId":monitor["companyId"],"metricId":m["id"],"point":target,
                  "researchAsOf":monitor.get("asOf") if valid_day(monitor.get("asOf")) else None}
            encoded=json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(",",":"))
            ident="forecast:"+hashlib.sha256(encoded.encode()).hexdigest()[:32]
            if ident in entries:
                continue
            entries[ident]={**body,"id":ident,"ticker":monitor.get("ticker"),"firstRecordedAt":now,
                "firstRecordedCommit":source_commit,
                "chronologyStatus":"research-asof-unverified; firstRecordedAt is verified archive boundary",
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
