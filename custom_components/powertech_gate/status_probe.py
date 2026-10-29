"""Explicit, bounded read-only RS sampling for PS19001 investigation."""

from __future__ import annotations

import asyncio
import time

INTERVAL_SECONDS = 2.0
RESPONSE_TIMEOUT_SECONDS = 3.0
MAX_DURATION_SECONDS = 90


class SystemStatusProbe:
    """A user-started task; never starts during integration setup."""

    def __init__(self, client, *, clock=time.monotonic, sleep=asyncio.sleep) -> None:
        self.client = client
        self._clock = clock
        self._sleep = sleep
        self.task = None
        self.requests = 0
        self.responses = 0
        self.finish_reason = "not_started"

    @property
    def running(self) -> bool:
        return self.task is not None and not self.task.done()

    def start(self, create_task, executor, duration: int) -> None:
        if self.running:
            raise ValueError("A system-status capture is already running")
        if not self.client.uses_position_feedback:
            raise ValueError("This diagnostic build supports PS19001 status capture only")
        if not self.client.feedback_capture.enabled:
            raise ValueError("Enable feedback capture before requesting system status")
        if not self.client.is_connected:
            raise ValueError("The controller is disconnected")
        if type(duration) is not int or not 1 <= duration <= MAX_DURATION_SECONDS:
            raise ValueError("Duration must be between 1 and 90 seconds")
        self.requests = self.responses = 0
        self.finish_reason = "running"
        self.task = create_task(self._run(executor, duration))

    def cancel(self) -> None:
        if self.running:
            self.finish_reason = "cancelled"
            self.task.cancel()

    def snapshot(self) -> dict:
        return {"running": self.running, "requests": self.requests,
                "responses": self.responses, "finish_reason": self.finish_reason}

    async def _run(self, executor, duration: int) -> None:
        deadline = self._clock() + duration
        try:
            while self._clock() < deadline:
                if not self.client.feedback_capture.enabled or not self.client.is_connected:
                    self.finish_reason = "capture_disabled_or_disconnected"
                    return
                before = self.client.system_status_generation
                sent_at = self._clock()
                if not await executor(self.client.request_fresh_system_status):
                    self.finish_reason = "publish_unavailable"
                    return
                self.requests += 1
                # Stop after one unanswered request; do not keep polling a
                # controller that does not implement RS. A final reply can be
                # awaited briefly after the requested sampling window ends.
                while self.client.system_status_generation == before:
                    if not self.client.feedback_capture.enabled or not self.client.is_connected:
                        self.finish_reason = "capture_disabled_or_disconnected"
                        return
                    if self._clock() - sent_at >= RESPONSE_TIMEOUT_SECONDS:
                        self.finish_reason = "no_response"
                        return
                    await self._sleep(0.1)
                self.responses += self.client.system_status_generation - before
                if self._clock() >= deadline:
                    break
                await self._sleep(min(max(0, INTERVAL_SECONDS - (self._clock() - sent_at)),
                                      max(0, deadline - self._clock())))
            self.finish_reason = "window_complete"
        except asyncio.CancelledError:
            self.finish_reason = "cancelled"
            raise
        except Exception:
            # No response text or credentials are persisted in probe metadata.
            self.finish_reason = "error"
            raise
