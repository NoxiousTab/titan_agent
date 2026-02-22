"""n8n ESB Integration — V2 Architecture.

In V2, Python acts as the Intelligence Core and delegates ALL
orchestration (Jira, Slack, HITL) to n8n via a single webhook.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


def dispatch_to_esb(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send the full enriched ticket payload to the n8n ESB webhook.

    Args:
        payload: Enriched ticket dict including severity, is_duplicate,
                 duplicate_ticket_id, ai_reasoning, suggested_fixes,
                 assigned_team, reporter, department, etc.

    Returns:
        Dict with ``ok`` (bool) and optionally ``status_code`` / ``error``.
    """
    url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not url:
        logger.warning("N8N_WEBHOOK_URL not set — ESB dispatch skipped")
        return {"ok": False, "error": "N8N_WEBHOOK_URL not configured"}

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code < 300:
            logger.info("ESB dispatch OK → %s (status %d)", url, resp.status_code)
            return {"ok": True, "status_code": resp.status_code}
        else:
            logger.error("ESB dispatch failed: HTTP %d", resp.status_code)
            return {"ok": False, "status_code": resp.status_code}
    except requests.RequestException as exc:
        logger.error("ESB dispatch error: %s", exc)
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Legacy compat — kept so any old code importing trigger_n8n still works
# ---------------------------------------------------------------------------
def trigger_n8n(payload: Dict[str, Any]) -> bool:
    """DEPRECATED: Use dispatch_to_esb() instead."""
    result = dispatch_to_esb(payload)
    return result.get("ok", False)
