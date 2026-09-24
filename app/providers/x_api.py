import requests
from datetime import datetime,timezone
from ..models import SocialEvent

class XRecentSearch:
    URL='https://api.x.com/2/tweets/search/recent'
    def __init__(self,bearer_token,query):self.token,self.query=bearer_token,query
    def events(self,max_results=100):
        if not self.token:return []
        params={'query':self.query,'max_results':max(10,min(max_results,100)),'tweet.fields':'created_at,author_id','expansions':'author_id','user.fields':'username'}
        r=requests.get(self.URL,headers={'Authorization':f'Bearer {self.token}'},params=params,timeout=30);r.raise_for_status();body=r.json()
        users={u['id']:u for u in body.get('includes',{}).get('users',[])};out=[]
        for p in body.get('data',[]):
            ts=p.get('created_at');created=datetime.fromisoformat(ts.replace('Z','+00:00')) if ts else datetime.now(timezone.utc);u=users.get(p.get('author_id'),{})
            out.append(SocialEvent('x',p['id'],u.get('username','unknown'),p['text'],created,f"https://x.com/i/web/status/{p['id']}"))
        return out
