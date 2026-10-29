"""Capture privacy, retention and MQTT-behaviour regression tests; offline only."""

from __future__ import annotations

from dataclasses import asdict
import importlib
import json
import types
import unittest
from unittest.mock import patch

from test_shadow_diagnostics_096 import api, FakeLoop

capture_module = importlib.import_module("powertech_gate.feedback_capture")


def make_client():
    return api.PW200Client(
        endpoint="test.invalid", thing_id="private-thing", source_id="private-source",
        cert_path="private-cert", key_path="private-key", ca_path=None,
        event_loop=FakeLoop(),
    )


def receive(client, topic, payload):
    client._on_message(client._mqtt, None, types.SimpleNamespace(
        topic=topic, payload=payload.encode(), retain=False, dup=False,
    ))


class FeedbackCaptureTests(unittest.TestCase):
    def setUp(self):
        self.client = make_client()
        self.capture = self.client.feedback_capture

    def test_disabled_by_default_and_disabling_clears(self):
        receive(self.client, self.client._topic_position, "45%")
        self.assertEqual(self.capture.snapshot()["events"], [])
        self.capture.set_enabled(True)
        receive(self.client, self.client._topic_position, "45%")
        self.assertEqual(self.capture.snapshot()["events"][0]["position_payload"], 45)
        self.capture.set_enabled(False)
        self.assertEqual(self.capture.snapshot()["events"], [])

    def test_actual_numbers_retained_before_existing_clamp(self):
        self.capture.set_enabled(True)
        for payload, expected in [("0", 0), (" 48% ", 48), ("100", 100), ("101", 101), ("-1", -1)]:
            receive(self.client, self.client._topic_position, payload)
            event = self.capture.snapshot()["events"][-1]
            self.assertEqual(event["position_payload"], expected)
            self.assertEqual(event["position"], max(0, min(100, expected)))
        for payload in ("password=private-secret", "42;src=private-thing", "1.5", "123456789012345"):
            receive(self.client, self.client._topic_position, payload)
            event = self.capture.snapshot()["events"][-1]
            self.assertIsNone(event["position_payload"])
            self.assertNotIn(payload, json.dumps(event))

    def test_shadow_is_allowlisted_and_metadata_kept(self):
        self.capture.set_enabled(True)
        receive(self.client, self.client._topic_shadow_ok, json.dumps({
            "state": {"reported": {"DEV STATUS": "00,00,00,00", "WBT PIN": "SECRET-PIN",
                                   "IP": "PRIVATE-IP", "WiFi MAC": "PRIVATE-MAC",
                                   "DEV INFO": "PRIVATE-IDENTIFIER"}},
            "version": 5, "metadata": {"reported": {"DEV STATUS": {"timestamp": 1234}}},
            "clientToken": "PRIVATE-TOKEN",
        }))
        event = self.capture.snapshot()["events"][-1]
        self.assertEqual(event["status_bytes"], [0, 0, 0, 0])
        self.assertEqual(event["shadow_version"], 5)
        self.assertEqual(event["status_timestamp"], 1234)
        self.assertEqual(event["gate_state"], "closed")
        encoded = json.dumps(self.capture.snapshot())
        for secret in ("PRIVATE", "SECRET-PIN", "private-thing", "private-source", "private-cert"):
            self.assertNotIn(secret, encoded)

    def test_ack_strips_identifiers_and_unknown_messages(self):
        self.capture.set_enabled(True)
        for payload in ("ACK PED OPEN;src=SECRET", "ACK RS:00,00,00,00;src=SECRET",
                        "ACK STATUS:PED CLOSED,0;src=SECRET", "SECRET password=SECRET"):
            receive(self.client, self.client._topic_cmd_tx, payload)
        events = self.capture.snapshot()["events"]
        self.assertEqual(events[0]["ack"], "ACK PED OPEN")
        self.assertEqual(events[1]["status_bytes"], [0, 0, 0, 0])
        self.assertEqual(events[2]["status"], "PED CLOSED")
        self.assertEqual(events[3]["ack"], "unrecognised")
        self.assertNotIn("SECRET", json.dumps(events))

    def test_count_age_and_export_copy_are_bounded(self):
        self.capture.set_enabled(True)
        with patch.object(capture_module.time, "monotonic", return_value=0):
            for _ in range(capture_module.MAX_EVENTS + 3):
                self.capture.record_cover("full", True, False, False)
            result = self.capture.snapshot()
            self.assertEqual(len(result["events"]), capture_module.MAX_EVENTS)
            self.assertEqual(result["dropped"], 3)
            result["events"][0]["state"] = "MUTATED"
            self.assertNotIn("MUTATED", json.dumps(self.capture.snapshot()))
        with patch.object(capture_module.time, "monotonic", return_value=3601):
            self.assertEqual(self.capture.snapshot()["events"], [])

    def test_capture_changes_neither_state_nor_publishes(self):
        control = make_client()
        self.capture.set_enabled(True)
        messages = [
            ("_topic_shadow_ok", '{"state":{"reported":{"DEV STATUS":"00,00,00,00"}}}'),
            ("_topic_cmd_tx", "ACK FULL CLOSE"),
            ("_topic_position", "25"), ("_topic_position", "80"),
            ("_topic_position", "0"), ("_topic_cmd_tx", "ACK PED OPEN"),
            ("_topic_cmd_tx", "ACK STATUS:PED CLOSED,0"),
            ("_topic_shadow_update", '{"state":{"reported":{"DEV STATUS":"00,00,40,80"}}}'),
        ]
        for topic_attr, payload in messages:
            for client in (control, self.client):
                receive(client, getattr(client, topic_attr), payload)
            self.assertEqual(asdict(control.state), asdict(self.client.state))
        self.assertEqual(self.client._mqtt.published, control._mqtt.published)
        self.assertEqual(self.client._mqtt.published, [])

    def test_cover_records_unavailable_instead_of_stale_closed_state(self):
        self.capture.set_enabled(True)
        self.capture.record_cover("full", True, False, False, False)
        self.assertEqual(self.capture.snapshot()["events"][0]["state"], "unavailable")

    def test_malformed_or_unrelated_data_cannot_escape(self):
        self.capture.set_enabled(True)
        for payload in ('null', '[]', '{"state":null}', '{"state":{"reported":[]}}',
                        '{"state":{"reported":{"DEV STATUS":"SECRET"}}}', 'SECRET'):
            receive(self.client, self.client._topic_shadow_ok, payload) if payload not in (
                'null', '[]', '{"state":null}'
            ) else self.capture.record_message("shadow_get", payload, self.client.state, object())
        receive(self.client, "unrelated/SECRET", "SECRET")
        self.assertNotIn("SECRET", json.dumps(self.capture.snapshot()))


if __name__ == "__main__":
    unittest.main()
