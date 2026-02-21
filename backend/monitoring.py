from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple


class MonitoringPayloadError(ValueError):
    pass


def parse_datadog_alert(payload: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], bool]:
    """Parse a Datadog-style webhook payload into internal ticket fields.

    Returns:
        title, description, metadata, force_p1
    """

    title = str(payload.get("title", "")).strip()
    text = str(payload.get("text", "")).strip()

    if not title or not text:
        raise MonitoringPayloadError("Payload must include non-empty 'title' and 'text'.")

    host = payload.get("host")
    monitor_name = payload.get("monitor_name")
    monitor_id = payload.get("monitor_id")

    description_parts = [text]
    if host:
        description_parts.append(f"Host: {host}")
    if monitor_name:
        description_parts.append(f"Monitor: {monitor_name}")

    date_val = payload.get("date")
    if date_val is not None:
        try:
            description_parts.append(f"Alert time: {datetime.utcfromtimestamp(int(date_val)).isoformat()}Z")
        except Exception:
            pass

    description = "\n".join(description_parts).strip()

    metadata: Dict[str, Any] = {
        "alert_type": payload.get("alert_type"),
        "priority": payload.get("priority"),
        "event_type": payload.get("event_type"),
        "monitor_id": monitor_id,
        "monitor_name": monitor_name,
        "host": host,
    }

    alert_type = str(payload.get("alert_type", "")).lower().strip()
    priority = str(payload.get("priority", "")).upper().strip()
    event_type = str(payload.get("event_type", "")).lower().strip()

    force_p1 = alert_type == "error" or priority == "P1" or event_type == "triggered"

    return title, description, metadata, force_p1
