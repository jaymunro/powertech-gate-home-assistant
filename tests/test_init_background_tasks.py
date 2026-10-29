"""Regression tests for config-entry-owned background refresh tasks.

These tests use local Home Assistant stand-ins and never contact a gate or MQTT.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]


def _load_integration():
    """Load __init__ with only the Home Assistant surface it needs."""
    for name in tuple(sys.modules):
        if name == "powertech_gate" or name.startswith(("powertech_gate.", "homeassistant")):
            sys.modules.pop(name)

    package = types.ModuleType("powertech_gate")
    package.__path__ = [str(ROOT / "custom_components" / "powertech_gate")]
    sys.modules["powertech_gate"] = package

    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = object
    core.callback = lambda func: func
    sys.modules["homeassistant"] = types.ModuleType("homeassistant")
    sys.modules["homeassistant.core"] = core

    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = object
    sys.modules["homeassistant.config_entries"] = config_entries

    const = types.ModuleType("homeassistant.const")
    const.Platform = types.SimpleNamespace(COVER="cover", SENSOR="sensor")
    sys.modules["homeassistant.const"] = const

    exceptions = types.ModuleType("homeassistant.exceptions")
    exceptions.ConfigEntryError = RuntimeError
    exceptions.ConfigEntryNotReady = RuntimeError
    exceptions.ServiceValidationError = RuntimeError
    sys.modules["homeassistant.exceptions"] = exceptions

    helpers = types.ModuleType("homeassistant.helpers")
    device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    device_registry.CONNECTION_NETWORK_MAC = "mac"
    device_registry.async_get = lambda hass: hass.device_registry
    helpers.device_registry = device_registry
    helpers.config_validation = types.SimpleNamespace(config_entry_only_config_schema=lambda domain: object())
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.device_registry"] = device_registry

    component_const = types.ModuleType("powertech_gate.const")
    for name, value in {
        "CONF_CA_PATH": "ca_path", "CONF_CERT_PATH": "cert_path",
        "CONF_DEVICE_LABEL": "device_label", "CONF_DEVICE_TYPE": "device_type",
        "CONF_ENDPOINT": "endpoint", "CONF_KEY_PATH": "key_path",
        "CONF_REFRESH_INTERVAL": "refresh_interval", "CONF_SOURCE_ID": "source_id",
        "CONF_THING_ID": "thing_id", "DEFAULT_REFRESH_INTERVAL": 300,
        "CONF_CAPTURE_FEEDBACK": "capture_feedback",
        "DEFAULT_SOURCE_ID": "source", "DOMAIN": "powertech_gate",
    }.items():
        setattr(component_const, name, value)
    sys.modules["powertech_gate.const"] = component_const

    api = types.ModuleType("powertech_gate.api")
    api.PW200Client = object
    sys.modules["powertech_gate.api"] = api
    device = types.ModuleType("powertech_gate.device")
    device.format_mac = lambda value: value
    sys.modules["powertech_gate.device"] = device

    spec = importlib.util.spec_from_file_location(
        "powertech_gate", ROOT / "custom_components" / "powertech_gate" / "__init__.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeClient:
    thing_id = "test-thing"
    display_model = "PS20088D"
    state = types.SimpleNamespace(wbt_version="V02", wifi_mac=None)
    is_connected = False

    def __init__(self):
        self.started = self.stopped = self.listener_removed = False
        self.capture_settings = []
        self.feedback_capture = types.SimpleNamespace(set_enabled=self.capture_settings.append)

    def start(self): self.started = True
    def stop(self): self.stopped = True
    def add_listener(self, _listener):
        return lambda: setattr(self, "listener_removed", True)
    def request_shadow(self):
        raise AssertionError("The periodic coroutine must not run during setup")


class FakeEntry:
    entry_id = "entry-id"
    title = "Test gate"
    options = {}
    data = {"endpoint": "test.invalid", "thing_id": "test-thing", "cert_path": "/not-used", "key_path": "/not-used"}

    def __init__(self): self.background_tasks = []
    def add_update_listener(self, listener):
        self.update_listener = listener
        return lambda: None
    def async_on_unload(self, cleanup): pass
    def async_create_background_task(self, hass, coroutine, name):
        self.background_tasks.append((hass, coroutine, name))
        coroutine.close()
        return object()


class FakeConfigEntries:
    def __init__(self, unload_ok=True): self.unload_ok = unload_ok
    async def async_forward_entry_setups(self, entry, platforms): self.forwarded = (entry, platforms)
    async def async_unload_platforms(self, entry, platforms):
        self.unloaded = (entry, platforms)
        return self.unload_ok


class FakeHass:
    def __init__(self, unload_ok=True):
        self.data = {}
        self.config_entries = FakeConfigEntries(unload_ok)
        self.device_registry = types.SimpleNamespace(async_get_device=lambda **kwargs: None)
    async def async_add_executor_job(self, func, *args): return func(*args)
    def async_create_task(self, *_args):
        raise AssertionError("Long-running refresh must not be startup-tracked")


class BackgroundRefreshTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.integration = _load_integration()
        self.client = FakeClient()
        self.integration._create_client = lambda hass, entry: self.client
        self.entry = FakeEntry()

    async def test_refresh_is_entry_owned_background_task(self):
        hass = FakeHass()
        self.assertTrue(await self.integration.async_setup_entry(hass, self.entry))
        self.assertEqual(len(self.entry.background_tasks), 1)
        task_hass, _coroutine, name = self.entry.background_tasks[0]
        self.assertIs(task_hass, hass)
        self.assertEqual(name, "powertech_gate_entry-id_shadow_refresh")
        self.assertNotIn("entry-id_refresh_task", hass.data["powertech_gate"])

    async def test_successful_unload_cleans_runtime_resources(self):
        hass = FakeHass()
        await self.integration.async_setup_entry(hass, self.entry)
        self.assertTrue(await self.integration.async_unload_entry(hass, self.entry))
        self.assertTrue(self.client.listener_removed)
        self.assertTrue(self.client.stopped)
        self.assertNotIn("entry-id", hass.data["powertech_gate"])

    async def test_capture_options_apply_without_restart_or_new_client(self):
        hass = FakeHass()
        await self.integration.async_setup_entry(hass, self.entry)
        self.assertEqual(self.client.capture_settings, [False])
        self.entry.options = {"capture_feedback": True}
        await self.entry.update_listener(hass, self.entry)
        self.assertEqual(self.client.capture_settings, [False, True])
        self.assertIs(hass.data["powertech_gate"][self.entry.entry_id], self.client)

    async def test_failed_unload_keeps_runtime_resources(self):
        hass = FakeHass(unload_ok=False)
        await self.integration.async_setup_entry(hass, self.entry)
        self.assertFalse(await self.integration.async_unload_entry(hass, self.entry))
        self.assertFalse(self.client.listener_removed)
        self.assertFalse(self.client.stopped)
        self.assertIn("entry-id", hass.data["powertech_gate"])

    async def test_diagnostic_action_schema_target_and_background_ownership(self):
        try:
            import voluptuous as vol
        except ImportError:
            self.skipTest("Install voluptuous to exercise the real action schema")
        hass = FakeHass()
        registrations = []
        hass.services = types.SimpleNamespace(
            async_register=lambda *args, **kwargs: registrations.append((args, kwargs)),
        )
        self.assertTrue(await self.integration.async_setup(hass, {}))
        (domain, action, handler), kwargs = registrations[0]
        self.assertEqual((domain, action), ("powertech_gate", "capture_system_status"))
        schema = kwargs["schema"]
        for invalid in ({}, {"config_entry_id": "entry-id", "duration": 91},
                        {"config_entry_id": "entry-id", "command": "FULL OPEN"}):
            with self.assertRaises(vol.Invalid):
                schema(invalid)
        starts = []
        cancelled = []
        self.client.status_probe = types.SimpleNamespace(
            start=lambda *args: starts.append(args), cancel=lambda: cancelled.append(True),
        )
        self.integration.PW200Client = FakeClient
        self.entry.domain = "powertech_gate"
        hass.data[domain] = {"entry-id": self.client}
        hass.config_entries.async_get_entry = lambda entry_id: self.entry if entry_id == "entry-id" else None
        await handler(types.SimpleNamespace(data=schema({"config_entry_id": "entry-id"})))
        creator, executor, duration, include_shadow, protocol = starts[0]
        self.assertEqual(duration, 60)
        self.assertFalse(include_shadow)
        self.assertEqual(protocol, "auto")
        with self.assertRaises(vol.Invalid):
            schema({"config_entry_id": "entry-id", "protocol": "FULL OPEN"})
        await handler(types.SimpleNamespace(data=schema({"config_entry_id": "entry-id", "duration": 1, "protocol": "rs"})))
        self.assertEqual(starts[-1][4], "rs")
        await handler(types.SimpleNamespace(data=schema({"config_entry_id": "entry-id", "include_shadow": True})))
        self.assertTrue(starts[-1][3])
        async def sample(): pass
        creator(sample())
        self.assertEqual(self.entry.background_tasks[-1][2], "powertech_gate_entry-id_system_status_probe")
        await handler(types.SimpleNamespace(data=schema({"config_entry_id": "entry-id", "duration": 0})))
        self.assertEqual(cancelled, [True])
        with self.assertRaisesRegex(RuntimeError, "not loaded"):
            await handler(types.SimpleNamespace(data=schema({"config_entry_id": "missing"})))
