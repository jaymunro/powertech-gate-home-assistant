## Passive MQTT diagnostics (0.9.8)

Version 0.9.8 investigates devices where AWS IoT MQTT connects successfully
but every default shadow GET returns `404`.

During the existing passive setup validation window, the integration now also
subscribes to the device-scoped MQTT namespace and to named-shadow update
topics. It does **not** send OPEN, CLOSE, STOP, pedestrian, or other device
commands.

Diagnostics report only:

- subscription acknowledgement results,
- safe topic categories and message counts,
- short non-reversible fingerprints for unknown topic suffixes.

Message payloads and raw unknown topic names are not logged.

The existing `DEV INFO` / `DEV STATUS` safety requirement is unchanged.
Receiving traffic on another MQTT topic does not automatically enable gate
control; the purpose of this release is only to identify the next compatible
state path for affected controllers.
