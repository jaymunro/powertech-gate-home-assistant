## What's changed

### Reconnect-safe passive EyeOpen observation

Version **0.9.12** improves the v0.9.11 passive observation test after a
community test showed that the MQTT session could disconnect before the
30-second window completed.

This release now:

- preserves passive `wbt01Tx` and `position` counters across reconnects
- re-subscribes after a successful reconnect
- uses a shorter reconnect backoff during setup validation
- performs a bounded reconnect fallback if the client remains disconnected
- records privacy-safe disconnect and reconnect diagnostics

### How to test

Update to **0.9.12** through HACS and restart Home Assistant.

Start adding the integration and, during the 30-second observation window, use
the official EyeOpen app to operate the same gate once.

Please share the Powertech lines containing:

```text
Powertech passive MQTT observation window started
Powertech MQTT disconnected during validation
Powertech MQTT reconnect attempt
Powertech MQTT reconnected
Powertech passive MQTT activity observed
Powertech shadow validation timed out
```

The final timeout line now includes:

```text
passive_command_ack_messages=...
passive_position_messages=...
successful_connects=...
disconnect_events=...
reconnect_attempts=...
reconnect_failures=...
```

### Safety

This remains a diagnostic release.

- Home Assistant sends no `RS` request.
- Home Assistant sends no OPEN, CLOSE, STOP, PED or other movement command.
- No wildcard MQTT subscriptions are used.
- Passive traffic does not bypass `DEV INFO` / `DEV STATUS` or PIN validation.
- Gate control is not enabled from passive traffic alone.
