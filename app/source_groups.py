"""Configurable source/ecosystem grouping for independent corroboration."""
ECOSYSTEMS = {
    "steamroom": {"wallstjesus","wallstwingman","fzn","joeygex","tradewithjoe"},
}
def _key(author,source=""): return (author or source or "").strip().lstrip("@").lower()
def ecosystem(author,source=""):
    key=_key(author,source)
    for name,members in ECOSYSTEMS.items():
        if key in members: return name
    return None
def same_ecosystem(author,source=""): return ecosystem(author,source) is not None
def independent_source_count(signal,all_signals):
    groups=set()
    for other in all_signals:
        if other is signal or other.ticker != signal.ticker: continue
        group=ecosystem(other.social.author,other.social.source)
        groups.add(group if group else _key(other.social.author,other.social.source))
    lead=ecosystem(signal.social.author,signal.social.source)
    if lead in groups: groups.remove(lead)
    return len(groups)
