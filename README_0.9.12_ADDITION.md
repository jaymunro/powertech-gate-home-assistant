## Reconnect-safe passive observation (0.9.12)

Version 0.9.12 keeps the passive EyeOpen observation running through temporary
MQTT disconnects.

The integration preserves the `wbt01Tx` and `position` message counters across
reconnects, re-subscribes through the normal MQTT connection callback, and uses
a short bounded reconnect fallback during the 30-second validation window.

The diagnostic log records only safe lifecycle information such as disconnect
reason codes, reconnect counts, and known-topic message counts. No raw unknown
topic names or credentials are logged.

Home Assistant still sends no diagnostic or movement command during this test.
