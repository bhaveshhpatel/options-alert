import pandas as pd
from app.backtest import evaluate_signal, summarize

def test_evaluate_signal_uses_forward_trading_rows():
    prices=pd.DataFrame([
      {"date":"2026-01-02","open":100,"high":101,"low":99,"close":100},
      {"date":"2026-01-05","open":100,"high":106,"low":98,"close":105},
      {"date":"2026-01-06","open":105,"high":108,"low":104,"close":107},
      {"date":"2026-01-07","open":107,"high":109,"low":106,"close":108},
    ])
    r=evaluate_signal("2026-01-02T15:00:00Z",prices,horizons=(1,3))
    assert r["entry"]==100
    assert round(r["returns"][1],6)==0.05
    assert round(r["returns"][3],6)==0.08
    assert r["max_favorable"]==0.09
    assert r["max_adverse"]==-0.02

def test_summarize():
    rows=[{"returns":{1:0.10,3:0.20}},{"returns":{1:-0.05,3:0.10}}]
    r=summarize(rows)
    assert r[1]["n"]==2 and r[1]["hit_rate"]==0.5
    assert round(r[1]["mean"],6)==0.025
