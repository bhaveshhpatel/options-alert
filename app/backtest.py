import pandas as pd


def evaluate_signal(signal_time, prices, horizons=(1, 3, 5, 7)):
    """Evaluate forward trading-day performance from the signal day's open.

    The signal timestamp is mapped to the first trading row on/after the
    signal timestamp. Entry is that row's open; horizon returns use closes
    of the next h trading rows. This avoids accidentally using the signal
    day's close when the signal occurs intraday.
    """
    p = prices.copy()
    p["date"] = pd.to_datetime(p["date"]).dt.tz_localize(None)
    p = p.sort_values("date").reset_index(drop=True)

    t = pd.Timestamp(signal_time)
    t = t.tz_localize(None) if t.tzinfo else t
    # Price data is daily, so an intraday signal timestamp maps to its
    # calendar day's trading row.
    signal_date = t.normalize()

    base = p[p["date"] >= signal_date]
    if base.empty:
        return {}

    entry_row = base.iloc[0]
    entry = float(entry_row["open"])
    future = base.iloc[1:]
    returns = {}

    for h in horizons:
        if len(future) >= h:
            returns[h] = float(future.iloc[h - 1]["close"] / entry - 1)

    w = future.head(max(horizons))
    mfe = (
        float((w["high"] / entry - 1).max())
        if "high" in w.columns and len(w)
        else None
    )
    mae = (
        float((w["low"] / entry - 1).min())
        if "low" in w.columns and len(w)
        else None
    )

    return {
        "entry": entry,
        "returns": returns,
        "max_favorable": mfe,
        "max_adverse": mae,
    }


def summarize(rows):
    out = {}
    for h in (1, 3, 5, 7):
        v = [r["returns"][h] for r in rows if h in r.get("returns", {})]
        out[h] = {
            "n": len(v),
            "mean": sum(v) / len(v) if v else None,
            "median": float(pd.Series(v).median()) if v else None,
            "hit_rate": sum(x > 0 for x in v) / len(v) if v else None,
        }
    return out
