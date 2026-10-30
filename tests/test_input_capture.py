"""Broader capture fidelity, limits and isolation; no network or gate commands."""
import importlib
import json
import types
import unittest
from unittest.mock import patch
from test_shadow_diagnostics_096 import api, FakeLoop
module = importlib.import_module('powertech_gate.input_capture')

class InputCaptureTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.capture = module.InputMessageCapture('own-private-source', 'private-controller', clock=lambda: self.now)

    def record(self, payload, kind='command_ack'):
        self.capture.record(kind, payload.encode() if isinstance(payload, str) else payload)

    def test_disabled_expiry_stop_and_new_window(self):
        self.record('unknown message')
        self.assertEqual(self.capture.snapshot()['events'], [])
        self.capture.start(10)
        self.record('unknown message')
        self.now = 10
        self.record('too late')
        self.assertFalse(self.capture.snapshot()['running'])
        self.assertEqual(len(self.capture.snapshot()['events']), 1)
        self.capture.start(10)
        self.assertEqual(self.capture.snapshot()['events'], [])
        self.capture.start(0)
        self.assertFalse(self.capture.snapshot()['running'])
        for value in (-1, 181, True, '10'):
            with self.assertRaises(ValueError): self.capture.start(value)

    def test_unknown_text_and_sources_retained_with_stable_aliases(self):
        self.capture.start()
        for value in ('REMOTE INPUT:2,17;src=remote-A', 'OTHER:9;src=remote-A',
                      'OTHER:9;src=remote-B', 'ACK STATUS:PED CLOSED,0;src=own-private-source'):
            self.record(value)
        events = self.capture.snapshot()['events']
        self.assertTrue(events[0]['content'].startswith('REMOTE INPUT:2,17;src=source_'))
        aliases = [e['content'].split(';src=')[1] for e in events]
        self.assertEqual(aliases[0], aliases[1])
        self.assertNotEqual(aliases[0], aliases[2])
        self.assertEqual(aliases[3], 'home_assistant')
        self.assertNotIn('remote-A', json.dumps(events))

    def test_shadow_extra_fields_preserved_credentials_and_identity_removed(self):
        self.capture.start()
        self.record(json.dumps({'state': {'reported': {'DEV STATUS': '00,00,10,00',
            'UNSEEN INPUT': [1, 0], 'WBT PIN': 'private-pin', 'password': 'private-password',
            'IP': '192.168.1.2', 'source_id': 'remote-A', 'nested': {'access_token': 'private-token'}}},
            'clientToken': 'private-client-token'}), 'shadow_update')
        e = self.capture.snapshot()['events'][0]
        self.assertEqual(e['content']['state']['reported']['UNSEEN INPUT'], [1, 0])
        for secret in ('private-pin', 'private-password', 'private-token', 'private-client-token', '192.168.1.2', 'remote-A'):
            self.assertNotIn(secret, json.dumps(e))

    def test_text_secrets_payload_limit_and_flags(self):
        self.capture.start()
        self.record('UNKNOWN x;PIN:123456;password=secret;src=remote-A')
        self.capture.record('position', b'25', retained=True, duplicate=True)
        self.record(b'x' * (module.MAX_PAYLOAD + 1))
        events = self.capture.snapshot()['events']
        self.assertNotIn('123456', json.dumps(events))
        self.assertNotIn('=secret', json.dumps(events))
        self.assertTrue(events[1]['retained'])
        self.assertTrue(events[1]['duplicate'])
        self.assertEqual(events[2]['encoding'], 'omitted')

    def test_bounded_count_age_and_export_copy(self):
        self.capture.start()
        for _ in range(module.MAX_EVENTS + 2): self.record('INPUT 1')
        result = self.capture.snapshot()
        self.assertEqual(len(result['events']), module.MAX_EVENTS)
        self.assertEqual(result['dropped'], 2)
        result['events'].clear()
        self.assertEqual(len(self.capture.snapshot()['events']), module.MAX_EVENTS)
        self.now = module.MAX_AGE + 1
        self.assertEqual(self.capture.snapshot()['events'], [])

    def test_capture_precedes_handler_without_publish_or_subscribe(self):
        client = api.PW200Client(endpoint='test.invalid', thing_id='private-controller', source_id='own-private-source',
                                cert_path='unused', key_path='unused', ca_path=None, event_loop=FakeLoop())
        client.input_capture.start()
        msg = types.SimpleNamespace(topic=client._topic_cmd_tx, payload=b'UNKNOWN INPUT:2;src=remote-A')
        with patch.object(client, '_handle_message', side_effect=ValueError):
            with self.assertRaises(ValueError): client._on_message(None, None, msg)
        self.assertEqual(len(client.input_capture.snapshot()['events']), 1)
        self.assertEqual(client._mqtt.published, [])
        self.assertEqual(client._mqtt.subscriptions, [])
        with patch.object(client.input_capture, 'record', side_effect=ValueError):
            with patch.object(client, '_handle_message') as handler:
                client._on_message(None, None, msg)
                handler.assert_called_once()
