from __future__ import annotations

import os
from typing import Any, Dict

import requests


def trigger_n8n(payload: Dict[str, Any]) -> bool:
    url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not url:
        return False

    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code < 300
    except Exception:
        return False
