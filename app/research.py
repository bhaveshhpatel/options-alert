"""Offline historical research/backtest pipeline."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from .backtest import evaluate_signal, summarize
from .detector import detect
from .models import SocialEvent
from .correlator import correlate
from .source_groups import independent_source_count, same_ecosystem

def load_events(path):
    df = pd.read_csv(path)
    required = {"event_id","source","author","text","created_at"}
    missing = required - set(df.columns)
    if missing: raise ValueError(f"events CSV missing columns: {sorted(missing)}")
    out=[]
    for row in df.itertuples(index=False):
        out.append(SocialEvent(
            source=str(row.source), event_id=str(row.event_id),
            author=str(row.author), text=str(row.text),
            created_at=pd.Timestamp(row.created_at).to_pydatetime(),
            url=getattr(row,"url",None)))
    return out

def load_prices(path):
    df=pd.read_csv(path)
    required={"ticker","date","open","high","low","close"}
    missing=required-set(df.columns)
    if missing: raise ValueError(f"prices CSV missing columns: {sorted(missing)}")
    df["ticker"]=df["ticker"].astype(str).str.upper()
    df["date"]=pd.to_datetime(df["date"],utc=True,errors="coerce")
    if df["date"].isna().any(): raise ValueError("prices CSV contains invalid dates")
    return {t:g.sort_values("date").reset_index(drop=True) for t,g in df.groupby("ticker",sort=False)}

def build_signal_rows(events, prices, horizons=(1,3,5,7)):
    signals=[s for e in events if (s:=detect(e))]
    clusters=correlate(signals)
    rows=[]
    for signal in signals:
        frame=prices.get(signal.ticker)
        if frame is None: continue
        result=evaluate_signal(signal.social.created_at,frame,horizons=horizons)
        if not result: continue
        rows.append({
            "event_id":signal.social.event_id,"ticker":signal.ticker,
            "source":signal.social.source,"author":signal.social.author,
            "signal_type":signal.signal_type,"direction":signal.direction,
            "created_at":signal.social.created_at.isoformat(),
            "same_ecosystem":same_ecosystem(signal.social.author,signal.social.source),
            "independent_sources":independent_source_count(signal,signals),
            "cluster_count":sum(1 for c in clusters if c["lead"].social.event_id==signal.social.event_id),
            **result})
    return rows

def run(events_csv, prices_csv, output_dir="research_output"):
    events=load_events(events_csv)
    prices=load_prices(prices_csv)
    rows=build_signal_rows(events,prices)
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(out/"signal_results.csv",index=False)
    with open(out/"summary.json","w",encoding="utf-8") as f: json.dump(summarize(rows),f,indent=2)
    if rows: pd.DataFrame(rows).query("independent_sources > 0").to_csv(out/"cross_source_signals.csv",index=False)
    return rows,summarize(rows)

def main():
    p=argparse.ArgumentParser(description="Run offline historical flow research.")
    p.add_argument("--events",required=True); p.add_argument("--prices",required=True)
    p.add_argument("--output-dir",default="research_output")
    a=p.parse_args(); rows,summary=run(a.events,a.prices,a.output_dir)
    print(json.dumps({"evaluated":len(rows),"summary":summary,"output_dir":a.output_dir},indent=2))
if __name__=="__main__": main()
