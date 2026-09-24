"""Normalize authorized historical social exports into the research schema.

Supports CSV, JSON array, and JSONL. It does not scrape or bypass authentication.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
import pandas as pd

REQUIRED = ["event_id","source","author","ticker","text","created_at","url"]

def _ticker(text):
    m = re.search(r"\$([A-Z][A-Z0-9]{0,5})\b", str(text).upper())
    return m.group(1) if m else ""

def _read(path):
    p = Path(path)
    if p.suffix.lower() == ".csv": return pd.read_csv(p)
    if p.suffix.lower() in {".jsonl",".ndjson"}: return pd.read_json(p, lines=True)
    if p.suffix.lower() == ".json":
        obj = json.loads(p.read_text(encoding="utf-8"))
        return pd.DataFrame(obj if isinstance(obj,list) else obj.get("data",obj.get("messages",[])))
    raise ValueError("Use CSV, JSON, or JSONL input")

def normalize(path, source, output):
    df = _read(path)
    aliases = {"id":"event_id","message_id":"event_id","body":"text","message":"text","username":"author","user":"author","timestamp":"created_at","created":"created_at","symbol":"ticker","link":"url"}
    df = df.rename(columns={c:aliases.get(c,c) for c in df.columns})
    if "text" not in df.columns: raise ValueError("Input needs text/body/message")
    if "event_id" not in df.columns:
        df["event_id"] = [hashlib.sha256(f"{source}|{a}|{t}|{d}".encode()).hexdigest()[:24] for a,t,d in zip(df.get("author",""),df["text"],df.get("created_at",""))]
    if "source" not in df.columns: df["source"] = source
    if "author" not in df.columns: df["author"] = "unknown"
    if "ticker" not in df.columns: df["ticker"] = ""
    df["ticker"] = df["ticker"].fillna("").astype(str).str.upper()
    df.loc[df["ticker"].eq(""),"ticker"] = df.loc[df["ticker"].eq(""),"text"].map(_ticker)
    if "created_at" not in df.columns: raise ValueError("Input needs created_at/timestamp")
    df["created_at"] = pd.to_datetime(df["created_at"],utc=True,errors="coerce")
    df = df[df["created_at"].notna()].copy()
    if "url" not in df.columns: df["url"] = ""
    df["text"] = df["text"].fillna("").astype(str)
    df["author"] = df["author"].fillna("unknown").astype(str)
    df = df[df["text"].str.len()>0].copy()
    df["_norm"] = df["text"].str.lower().str.replace(r"\s+"," ",regex=True).str.strip()
    df = df.drop_duplicates(subset=["source","author","_norm","created_at"])
    df["_fingerprint"] = df.apply(lambda r: hashlib.sha256(f"{r.source}|{r.author.lower()}|{r._norm}".encode()).hexdigest(),axis=1)
    df = df.sort_values("created_at").drop_duplicates("_fingerprint",keep="first")
    df[REQUIRED].sort_values("created_at").to_csv(output,index=False)
    return len(df)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--source",required=True); p.add_argument("--output",default="data/normalized_events.csv")
    a=p.parse_args(); print(f"normalized_events={normalize(a.input,a.source,a.output)} output={a.output}")

if __name__=="__main__": main()