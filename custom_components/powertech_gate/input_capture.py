"""Explicit, bounded received-message capture for input/source investigation.

No publish, subscription, settings, credential-file or filesystem access.
Diagnostics remain private: redaction is not a license to publish unknown data.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
import secrets
import threading
import time

MAX_SECONDS = 180
MAX_EVENTS = 512
MAX_PAYLOAD = 16384
MAX_AGE = 3600
_SECRET = re.compile(r"pin|password|passphrase|token|secret|private.?key|certificate|credential", re.I)
_IDENTITY = re.compile(r"^(?:src|source|source.?id|thing.?id|uid|uuid|owner|username|user|email|ssid|ip(?:.?address)?|(?:wi.?fi.?)?mac)$", re.I)
_INLINE_SECRET = re.compile(
    r"((?:WBT[ _]?)?PIN|PASSWORD|PASSPHRASE|TOKEN|SECRET|PRIVATE[ _]?KEY|CERTIFICATE)"
    r"\s*[:=]\s*[^;\r\n]+", re.I,
)
_SOURCE = re.compile(r"(?P<label>\b(?:src|source)\s*=\s*)(?P<value>[^;\r\n]+)", re.I)


class InputMessageCapture:
    """Capture every message kind on the client's existing subscriptions."""

    def __init__(self, own_source: str, thing_id: str, *, clock=time.monotonic):
        self.clock = clock
        self._own_source, self._thing_id = own_source, thing_id
        self._lock = threading.Lock()
        self._events = deque(maxlen=MAX_EVENTS)
        self._deadline = self._started = None
        self._salt = secrets.token_bytes(16)
        self._dropped = self._sequence = 0

    def start(self, duration: int = MAX_SECONDS):
        if type(duration) is not int or not 0 <= duration <= MAX_SECONDS:
            raise ValueError("Capture duration must be 0–180 seconds")
        with self._lock:
            if duration == 0:
                self._deadline = None
                return
            self._events.clear()
            self._dropped = self._sequence = 0
            self._salt = secrets.token_bytes(16)
            self._started = self.clock()
            self._deadline = self._started + duration

    def _alias(self, value):
        value = str(value)
        if value == self._own_source:
            return "home_assistant"
        if value == self._thing_id:
            return "controller"
        return "source_" + hashlib.sha256(self._salt + value.encode()).hexdigest()[:12]

    def _text(self, text):
        text = re.sub(r"-----BEGIN[^-]+-----.*?-----END[^-]+-----", "[credential redacted]", text, flags=re.S)
        text = _INLINE_SECRET.sub(lambda m: m[1] + "=[redacted]", text)
        text = _SOURCE.sub(lambda m: m['label'] + self._alias(m['value']), text)
        for value, replacement in ((self._thing_id, "[controller]"), (self._own_source, "[home_assistant]")):
            if value:
                text = text.replace(value, replacement)
        text = re.sub(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b", "[mac redacted]", text)
        text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[ip redacted]", text)
        return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email redacted]", text)

    def _json(self, value, depth=0):
        if depth > 12:
            return "[depth limit]"
        if isinstance(value, dict):
            return {self._text(str(k)): (
                "[redacted]" if _SECRET.search(str(k)) else
                self._alias(v) if _IDENTITY.fullmatch(str(k)) else
                self._json(v, depth + 1)
            ) for k, v in value.items()}
        if isinstance(value, list):
            return [self._json(v, depth + 1) for v in value]
        return self._text(value) if isinstance(value, str) else value

    def record(self, kind: str, payload: bytes, *, retained=False, duplicate=False):
        with self._lock:
            now = self.clock()
            if self._deadline is None or now >= self._deadline:
                return
            # Bound parser/redaction work as well as retained memory. Oversize
            # payloads are counted, not partially exported with broken redaction.
            if len(payload) > MAX_PAYLOAD:
                content = "[payload exceeds capture limit]"
                encoding = "omitted"
            else:
                text = payload.decode("utf-8", errors="replace")
                try:
                    content = self._json(json.loads(text))
                    encoding = "json"
                except (ValueError, RecursionError):
                    content = self._text(text)
                    encoding = "text"
            if len(self._events) == MAX_EVENTS:
                self._dropped += 1
            self._sequence += 1
            self._events.append({
                "sequence": self._sequence,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "topic_kind": kind, "payload_bytes": len(payload),
                "retained": bool(retained), "duplicate": bool(duplicate),
                "encoding": encoding, "content": content,
            })

    def snapshot(self):
        with self._lock:
            now = self.clock()
            if self._started is not None and now - self._started > MAX_AGE:
                self._events.clear()
                self._deadline = self._started = None
            return {
                "running": self._deadline is not None and now < self._deadline,
                "remaining_seconds": max(0, round(self._deadline - now, 1)) if self._deadline else 0,
                "capacity": MAX_EVENTS, "max_payload_bytes": MAX_PAYLOAD,
                "dropped": self._dropped, "events": deepcopy(list(self._events)),
            }
