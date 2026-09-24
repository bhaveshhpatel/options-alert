import json
from datetime import datetime,timezone
import requests
from requests.auth import HTTPBasicAuth
from ..models import SocialEvent

class StocktwitsFirestream:
    def __init__(self,username,password,url='https://firestream.stocktwits.com/stream'):
        self.username,self.password,self.url=username,password,url
    def events(self,seconds=180):
        if not self.username or not self.password:return
        with requests.get(self.url,auth=HTTPBasicAuth(self.username,self.password),headers={'Accept':'text/event-stream','Accept-Encoding':'gzip'},stream=True,timeout=(15,seconds+45)) as r:
            r.raise_for_status(); started=datetime.now(timezone.utc)
            for line in r.iter_lines():
                if (datetime.now(timezone.utc)-started).total_seconds()>seconds:break
                if not line:continue
                raw=line.decode('utf-8','replace')
                if raw.startswith('data:'):
                    event=self._parse(raw[5:].strip())
                    if event:yield event
    def _parse(self,payload):
        try:obj=json.loads(payload)
        except Exception:return None
        text=obj.get('body') or obj.get('text') or obj.get('message') or ''
        if not text:return None
        user=obj.get('user') or {}
        author=user.get('username') or user.get('name') or 'unknown'
        eid=str(obj.get('id') or obj.get('seq_id') or hash(payload))
        ts=obj.get('created_at') or obj.get('timestamp')
        try:created=datetime.fromisoformat(str(ts).replace('Z','+00:00')) if ts else datetime.now(timezone.utc)
        except Exception:created=datetime.now(timezone.utc)
        return SocialEvent('stocktwits',eid,author,text,created,obj.get('url'))
