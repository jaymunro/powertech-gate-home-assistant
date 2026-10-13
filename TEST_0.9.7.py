"""Synthetic privacy test for v0.9.7 identifier diagnostics."""
import importlib.util
import sys
import types
from pathlib import Path

root = Path(__file__).resolve().parent
backend_path = root / "custom_components" / "powertech_gate" / "backend.py"

pkg = types.ModuleType("custom_components")
pkg.__path__ = []
sys.modules["custom_components"] = pkg
subpkg = types.ModuleType("custom_components.powertech_gate")
subpkg.__path__ = []
sys.modules["custom_components.powertech_gate"] = subpkg
const = types.ModuleType("custom_components.powertech_gate.const")
const.BACKEND_BASE_URL = "https://example.invalid"
const.BACKEND_REST_TOKEN = "x"
const.KNOWN_PEDESTRIAN_MODELS = set()
sys.modules["custom_components.powertech_gate.const"] = const

spec = importlib.util.spec_from_file_location(
    "custom_components.powertech_gate.backend", backend_path
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

item = {
    "uuid": "uuid-secret-value",
    "thingName": "different-secret-thing",
    "client_id": "uuid-secret-value",
    "deviceId": "device-secret-value",
    "iot_endpoint": "secret.endpoint.example",
}
diag = mod._redact_device_for_debug(item)
text = repr(diag)

assert "uuid-secret-value" not in text
assert "different-secret-thing" not in text
assert "device-secret-value" not in text
assert "secret.endpoint.example" not in text

candidates = {x["field"]: x for x in diag["identifier_candidates"]}
assert candidates["thingName"]["matches_uuid"] is False
assert candidates["client_id"]["matches_uuid"] is True
assert candidates["deviceId"]["matches_uuid"] is False
assert len(candidates["thingName"]["fingerprint"]) == 10

print("PASS")
print(diag)
