"""Fixed RS-only publishes, bounded cadence, cancellation and failure handling."""

import asyncio
import importlib
import types
import unittest

from test_feedback_capture import make_client, receive

probe_module = importlib.import_module("powertech_gate.status_probe")


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []
    def __call__(self):
        return self.now
    async def sleep(self, duration):
        self.sleeps.append(duration)
        self.now += duration
        await asyncio.sleep(0)


class StatusProbeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = make_client()
        self.client.device_type = "PS19001"
        self.client._connected.set()
        self.client._shadow_subscription_status["command_ack"] = True
        self.client.feedback_capture.set_enabled(True)
        self.clock = Clock()
        self.probe = probe_module.SystemStatusProbe(
            self.client, clock=self.clock, sleep=self.clock.sleep,
        )
        self.publish_times = []

    async def executor(self, method):
        return method()

    def respond_to_reads(self):
        original = self.client._mqtt.publish
        def publish(topic, payload, qos=0):
            self.publish_times.append(self.clock())
            result = original(topic, payload, qos)
            receive(self.client, self.client._topic_cmd_tx,
                    "ACK RS:00,00,20,1A,00,00,00,00,00;src=PRIVATE")
            return result
        self.client._mqtt.publish = publish

    async def test_requests_are_only_rs_and_never_more_than_once_per_two_seconds(self):
        self.respond_to_reads()
        self.probe.start(asyncio.create_task, self.executor, 90)
        with self.assertRaisesRegex(ValueError, "already running"):
            self.probe.start(asyncio.create_task, self.executor, 90)
        await self.probe.task
        self.assertEqual(self.probe.requests, 45)
        self.assertEqual(self.probe.responses, 45)
        self.assertEqual(self.probe.finish_reason, "window_complete")
        self.assertTrue(all(b-a >= 2 for a,b in zip(self.publish_times,self.publish_times[1:])))
        self.assertEqual(set(self.client._mqtt.published), {
            (self.client._topic_cmd_rx, "c=RS;src=private-source", 0),
        })
        events = self.client.feedback_capture.snapshot()["events"]
        self.assertEqual(sum(e["kind"] == "status_request" for e in events), 45)
        self.assertNotIn("PRIVATE", str(events))
        self.assertIsNone(self.client.state.position)

    async def test_no_reply_stops_after_one_request(self):
        self.probe.start(asyncio.create_task, self.executor, 60)
        await self.probe.task
        self.assertEqual(self.probe.requests, 1)
        self.assertEqual(self.probe.responses, 0)
        self.assertEqual(self.probe.finish_reason, "no_response")
        self.assertLess(self.clock(), 3.2)

    async def test_invalid_ack_does_not_count_as_status_response(self):
        for text in ("ACK FULL OPEN", "ACK RS:not-a-status", "ACK RS:00,00,00"):
            receive(self.client, self.client._topic_cmd_tx, text)
        self.assertEqual(self.client.system_status_generation, 0)

    async def test_legacy_uart_reads_status_and_records_mode_and_position(self):
        self.client.state.uart_version = 1
        original = self.client._mqtt.publish
        def publish(topic, payload, qos=0):
            result = original(topic, payload, qos)
            receive(self.client, self.client._topic_cmd_tx, "ACK STATUS:PED OPENED,40;src=PRIVATE")
            return result
        self.client._mqtt.publish = publish
        self.probe.start(asyncio.create_task, self.executor, 1)
        await self.probe.task
        self.assertEqual(self.client._mqtt.published, [
            (self.client._topic_cmd_rx, "c=READ STATUS;src=private-source", 0),
        ])
        self.assertEqual(self.probe.responses, 1)
        self.assertEqual(self.probe.finish_reason, "window_complete")
        reply = self.client.feedback_capture.snapshot()["events"][0]
        self.assertEqual(reply["status"], "PED OPENED")
        self.assertEqual(reply["status_position"], 40)
        self.assertNotIn("PRIVATE", str(reply))
        self.assertIsNone(self.client.state.position)

    async def test_unready_subscription_or_failed_publish_stops(self):
        for ready in (False, True):
            self.client._shadow_subscription_status["command_ack"] = ready
            self.client._mqtt.publish_rc = 4
            self.probe.start(asyncio.create_task, self.executor, 60)
            await self.probe.task
            self.assertEqual(self.probe.finish_reason, "publish_unavailable")
            self.assertEqual(self.probe.requests, 0)

    async def test_capture_disable_and_disconnect_stop_without_further_requests(self):
        for disconnected in (False, True):
            self.setUp()
            self.respond_to_reads()
            async def sleep(duration):
                if disconnected:
                    self.client._connected.clear()
                else:
                    self.client.feedback_capture.set_enabled(False)
                await self.clock.sleep(duration)
            self.probe._sleep = sleep
            self.probe.start(asyncio.create_task, self.executor, 60)
            await self.probe.task
            self.assertEqual(self.probe.requests, 1)
            self.assertEqual(self.probe.finish_reason, "capture_disabled_or_disconnected")

    async def test_can_cancel_waiting_probe(self):
        self.probe.start(asyncio.create_task, self.executor, 60)
        await asyncio.sleep(0)
        self.probe.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await self.probe.task
        self.assertEqual(self.probe.finish_reason, "cancelled")
        self.assertFalse(self.probe.running)

    async def test_requires_explicit_supported_target_capture_connection_and_duration(self):
        for duration in (0, 91, -1, 1.5, True):
            with self.assertRaises(ValueError):
                self.probe.start(asyncio.create_task, self.executor, duration)
        self.client.device_type = "OTHER"
        with self.assertRaises(ValueError):
            self.probe.start(asyncio.create_task, self.executor, 60)
        self.client.device_type = "PS19001"
        self.client.feedback_capture.set_enabled(False)
        with self.assertRaises(ValueError):
            self.probe.start(asyncio.create_task, self.executor, 60)
        self.client.feedback_capture.set_enabled(True)
        self.client._connected.clear()
        with self.assertRaises(ValueError):
            self.probe.start(asyncio.create_task, self.executor, 60)
        self.assertEqual(self.client._mqtt.published, [])


if __name__ == "__main__":
    unittest.main()
