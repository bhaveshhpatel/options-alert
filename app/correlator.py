from collections import defaultdict
from datetime import timedelta

def correlate(signals,window_minutes=360):
    groups=defaultdict(list)
    for s in signals: groups[s.ticker].append(s)
    results=[]
    window=timedelta(minutes=window_minutes)
    for ticker,items in groups.items():
        items.sort(key=lambda x:x.social.created_at)
        for i,lead in enumerate(items):
            matches=[]
            for other in items[i+1:]:
                if other.social.created_at-lead.social.created_at>window: break
                if other.social.author.lower()==lead.social.author.lower(): continue
                matches.append(other)
            if matches:
                results.append({'ticker':ticker,'lead':lead,'matches':matches,'independent_sources':len({m.social.author.lower() for m in matches}),'first_match_minutes':round((matches[0].social.created_at-lead.social.created_at).total_seconds()/60,1)})
    return results
