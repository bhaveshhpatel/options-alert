"""Optional WhatsApp Cloud API notification adapter.

Uses the Meta WhatsApp Cloud API. Credentials are supplied through environment
variables and are never logged.
"""

import logging
import os
from typing import Iterable

import requests

log = logging.getLogger("flow-agent.whatsapp")


def _api_url(phone_number_id: str) -> str:
    explicit = os.getenv("WHATSAPP_API_URL", "").strip()
    if explicit:
        return explicit
    version = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v23.0").strip()
    return f"https://graph.facebook.com/{version}/{phone_number_id}/messages"


def send_whatsapp_text(
    access_token: str,
    phone_number_id: str,
    recipients: Iterable[str],
    text: str,
) -> None:
    """Send a text message to each configured WhatsApp recipient."""
    if not access_token or not phone_number_id:
        return

    body = text[:4096]
    url = _api_url(phone_number_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    for recipient in recipients:
        recipient = recipient.strip()
        if not recipient:
            continue
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": True, "body": body},
        }
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        log.info("WhatsApp alert delivered to configured recipient.")
