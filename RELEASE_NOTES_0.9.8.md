## What's changed

### Passive MQTT diagnostics for shadow `404` devices

Version **0.9.8** adds a new privacy-safe diagnostic path for controllers where:

- AWS IoT MQTT connects successfully,
- all required subscriptions are acknowledged,
- but every default shadow GET is rejected with `404`.

During the existing setup validation window, the integration now passively
observes the device-scoped MQTT namespace and named-shadow update namespace.

It records only:

- subscription acknowledgement results,
- topic categories and message counts,
- short non-reversible fingerprints for unknown topic suffixes.

Raw unknown topic names and message payloads are **not** logged.

### Safety

This remains a diagnostic release.

- No gate movement commands are sent during validation.
- `DEV INFO` / `DEV STATUS` validation is unchanged.
- Traffic seen on another MQTT topic does not automatically enable gate control.
- The purpose is to determine whether affected controllers expose their state
  outside the default AWS IoT shadow.

### Testing

Update to **0.9.8** through HACS, restart Home Assistant, and try setup again
with debug logging enabled.

If setup still fails, please share only the privacy-safe Powertech lines
containing:

```text
Powertech MQTT subscription acknowledged
Powertech passive MQTT activity
Powertech shadow request rejected
Powertech shadow validation timed out
```

The final timeout line now includes passive topic counts and any safe unknown
topic fingerprints.
