"""Opt-in, bounded, allowlisted feedback history; never stores full MQTT payloads."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import threading
import time

MAX_EVENTS = 512
MAX_AGE_SECONDS = 3600
STATES = frozenset({
    "closed", "closing", "open", "opening", "partial_open", "partial_opening",
    "stopped", "unknown", "factory_default",
})


def safe_number(value: object) -> int | None:
    """Accept only small integer payloads; never retain arbitrary text."""
    if type(value) is int:
        return value if -1_000_000 <= value <= 1_000_000 else None
    if isinstance(value, str) and re.fullmatch(r"-?\d{1,6}%?", value.strip(), re.ASCII):
        return int(value.strip().rstrip("%"))
    return None


def safe_status(value: object) -> list[int] | None:
    """Retain only bounded DEV STATUS / RS bytes, never other shadow fields."""
    if not isinstance(value, str) or len(value) > 64:
        return None
    parts = value.split(",")
    if not 4 <= len(parts) <= 16:
        return None
    if not all(re.fullmatch(r"[0-9a-fA-F]{2}", part.strip()) for part in parts):
        return None
    return [int(part, 16) for part in parts]


def safe_ack(value: object) -> dict:
    """Keep known command/status words only, stripping identifiers and other text."""
    if not isinstance(value, str):
        return {}
    token = value.split(";", 1)[0].strip()
    if re.fullmatch(r"ACK (?:FULL OPEN|FULL CLOSE|PED OPEN|PED CLOSE|STOP)", token):
        return {"ack": token}
    if token.startswith("ACK RS:"):
        return {"ack": "ACK RS", "status_bytes": safe_status(token[7:])}
    match = re.fullmatch(r"ACK STATUS:(?P<status>(?:PED |FULL |SINGLE )?(?:CLOSED|OPEN|OPENED|OPENING|CLOSING|CLOSEING|STOPPED)),(?P<position>\d{1,3})", token)
    if match:
        return {"ack": "ACK STATUS", "status": match["status"],
                "status_position": int(match["position"])}
    return {"ack": "unrecognised"}


class FeedbackCapture:
    """Thread-safe in-memory history, cleared on disable and lost on restart."""

    def __init__(self) -> None:
        self._enabled = False
        self._events: deque = deque(maxlen=MAX_EVENTS)
        self._lock = threading.Lock()
        self._sequence = 0
        self._dropped = 0

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            enabled = bool(enabled)
            if enabled != self._enabled:
                self._events.clear()
                self._sequence = 0
                self._dropped = 0
            self._enabled = enabled

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def _prune(self, now: float) -> None:
        while self._events and now - self._events[0][0] > MAX_AGE_SECONDS:
            self._events.popleft()
            self._dropped += 1

    def _append(self, kind: str, fields: dict) -> None:
        with self._lock:
            if not self._enabled:
                return
            now = time.monotonic()
            self._prune(now)
            if len(self._events) == MAX_EVENTS:
                self._dropped += 1
            self._sequence += 1
            self._events.append((now, {
                "sequence": self._sequence,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "kind": kind,
                **fields,
            }))

    def record_message(self, kind: str, payload: str, state: object, msg: object) -> None:
        if not self.enabled:
            return
        fields = {
            "gate_state": state.gate_state if state.gate_state in STATES else "unknown",
            "position": safe_number(state.position),
            "last_ack": safe_ack(state.last_ack),
            "retained": bool(getattr(msg, "retain", False)),
            "duplicate": bool(getattr(msg, "dup", False)),
        }
        if kind == "position":
            fields["position_payload"] = safe_number(payload)
            fields["payload_valid"] = fields["position_payload"] is not None
        elif kind == "command_ack":
            fields.update(safe_ack(payload))
        elif kind in {"shadow_get", "shadow_update"}:
            try:
                data = json.loads(payload)
                reported = data.get("state", {}).get("reported", {})
                if not isinstance(reported, dict):
                    return
                fields["status_bytes"] = safe_status(reported.get("DEV STATUS"))
                version = data.get("version")
                fields["shadow_version"] = version if type(version) is int else None
                timestamp = data.get("metadata", {}).get("reported", {}).get("DEV STATUS", {}).get("timestamp")
                fields["status_timestamp"] = timestamp if type(timestamp) is int else None
            except (ValueError, AttributeError, TypeError):
                fields["payload_valid"] = False
        else:
            return
        self._append(kind, fields)

    def record_cover(self, mode: str, closed: bool | None, opening: bool, closing: bool,
                     available: bool = True) -> None:
        if mode not in {"full", "pedestrian"}:
            return
        state = "opening" if opening else "closing" if closing else (
            "closed" if closed is True else "open" if closed is False else "unknown"
        )
        if not available:
            state = "unavailable"
        self._append("cover", {"mode": mode, "state": state})

    def record_status_request(self, accepted: bool) -> None:
        """Timestamp an explicit RS publish without retaining its payload."""
        self._append("status_request", {"accepted": bool(accepted)})

    def snapshot(self) -> dict:
        with self._lock:
            self._prune(time.monotonic())
            return {"enabled": self._enabled, "capacity": MAX_EVENTS,
                    "max_age_seconds": MAX_AGE_SECONDS, "dropped": self._dropped,
                    "events": deepcopy([event for _, event in self._events])}
