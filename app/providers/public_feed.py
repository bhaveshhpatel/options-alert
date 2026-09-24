from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import requests

from ..models import SocialEvent


class PublicFeed:
    """Poll a public RSS/Atom feed without scraping a site's HTML."""

    def __init__(self, url, timeout=20):
        self.url = url
        self.timeout = timeout

    def events(self):
        response = requests.get(
            self.url,
            headers={"User-Agent": "options-alert-research/1.0"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
        source = self._source_name(root)
        events = []
        for item in root.findall(".//item"):
            event = self._item_event(item, source)
            if event:
                events.append(event)
        atom_entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        for entry in atom_entries:
            event = self._atom_event(entry, source)
            if event:
                events.append(event)
        return events

    def _source_name(self, root):
        title = root.findtext("./channel/title")
        if title:
            return f"feed:{title.strip()}"
        atom_title = root.findtext("{http://www.w3.org/2005/Atom}title")
        if atom_title:
            return f"feed:{atom_title.strip()}"
        return f"feed:{urlparse(self.url).netloc}"

    def _item_event(self, item, source):
        title = item.findtext("title") or ""
        description = item.findtext("description") or ""
        text = title if not description else f"{title} — {description}"
        link = item.findtext("link") or self.url
        event_id = item.findtext("guid") or link or text
        ts = item.findtext("pubDate") or item.findtext("date")
        created = self._parse_time(ts)
        if not text.strip():
            return None
        return SocialEvent(source, str(event_id), "feed", text.strip(), created, link)

    def _atom_event(self, entry, source):
        ns = "{http://www.w3.org/2005/Atom}"
        title = entry.findtext(f"{ns}title") or ""
        summary = entry.findtext(f"{ns}summary") or entry.findtext(f"{ns}content") or ""
        text = title if not summary else f"{title} — {summary}"
        link = self.url
        for link_node in entry.findall(f"{ns}link"):
            href = link_node.attrib.get("href")
            if href:
                link = href
                break
        event_id = entry.findtext(f"{ns}id") or link or text
        ts = entry.findtext(f"{ns}published") or entry.findtext(f"{ns}updated")
        created = self._parse_time(ts)
        if not text.strip():
            return None
        return SocialEvent(source, str(event_id), "feed", text.strip(), created, link)

    @staticmethod
    def _parse_time(value):
        if not value:
            return datetime.now(timezone.utc)
        try:
            return parsedate_to_datetime(value).astimezone(timezone.utc)
        except (TypeError, ValueError):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except (TypeError, ValueError):
                return datetime.now(timezone.utc)
