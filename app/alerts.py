import requests

def send_webhook(url,payload):
    if not url:return
    r=requests.post(url,json=payload,timeout=15);r.raise_for_status()

def format_alert(cluster):
    lead=cluster['lead']
    return {'type':'flow_cluster','ticker':cluster['ticker'],'signal':lead.signal_type,'direction':lead.direction,'lead_source':lead.social.source,'lead_author':lead.social.author,'lead_text':lead.social.text,'lead_time':lead.social.created_at.isoformat(),'independent_sources':cluster['independent_sources'],'first_match_minutes':cluster['first_match_minutes'],'corroborations':[{'source':m.social.source,'author':m.social.author,'text':m.social.text,'time':m.social.created_at.isoformat()} for m in cluster['matches']],'disclaimer':'Research alert only; not a trade instruction.'}
