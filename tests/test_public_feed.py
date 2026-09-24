from app.providers.public_feed import PublicFeed


def test_public_rss_feed_parses_item(monkeypatch):
    class Response:
        content = b"""<?xml version='1.0'?><rss><channel><title>Example Feed</title><item><guid>abc</guid><title>$P REPEAT SWEEPER BUYING</title><description>test</description><link>https://example.com/post/abc</link><pubDate>Wed, 23 Sep 2026 12:00:00 GMT</pubDate></item></channel></rss>"""
        def raise_for_status(self):
            pass

    monkeypatch.setattr("app.providers.public_feed.requests.get", lambda *args, **kwargs: Response())
    events = PublicFeed("https://example.com/feed.xml").events()

    assert len(events) == 1
    assert events[0].source == "feed:Example Feed"
    assert events[0].event_id == "abc"
    assert events[0].author == "feed"
    assert "$P REPEAT SWEEPER BUYING" in events[0].text
    assert events[0].url == "https://example.com/post/abc"
