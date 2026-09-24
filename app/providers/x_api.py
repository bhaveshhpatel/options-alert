import requests
from datetime import datetime, timezone

from ..models import SocialEvent


class XRecentSearch:
    URL = "https://api.x.com/2/tweets/search/recent"

    def __init__(self, bearer_token, query):
        self.token = bearer_token
        self.query = query

    def events(self, max_results=100):
        if not self.token:
            return []

        params = {
            "query": self.query,
            "max_results": max(10, min(max_results, 100)),
            "tweet.fields": "created_at,author_id",
            "expansions": "author_id",
            "user.fields": "username",
        }
        response = requests.get(
            self.URL,
            headers={"Authorization": f"Bearer {self.token}"},
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        users = {
            user["id"]: user
            for user in body.get("includes", {}).get("users", [])
        }

        events = []
        for post in body.get("data", []):
            timestamp = post.get("created_at")
            created = (
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if timestamp
                else datetime.now(timezone.utc)
            )
            user = users.get(post.get("author_id"), {})
            events.append(
                SocialEvent(
                    "x",
                    post["id"],
                    user.get("username", "unknown"),
                    post["text"],
                    created,
                    f"https://x.com/i/web/status/{post['id']}",
                )
            )
        return events
