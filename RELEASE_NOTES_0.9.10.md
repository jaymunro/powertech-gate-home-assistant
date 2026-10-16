## What's changed

### Read-only WBT system-status diagnostic

Version **0.9.10** adds the next targeted diagnostic for devices where the AWS
IoT connection works but the default shadow consistently returns `404`.

Analysis of the official EyeOpen Android app confirmed that it can issue a
read-only system-status request over the normal WBT MQTT command channel:

```text
c=RS;src=<source_id>
```

The expected response is:

```text
ACK RS:...
```

on the existing `wbt01Tx` topic.

In 0.9.10, this request is sent **once**, only after a shadow `404` has already
been observed and the command-response subscription is confirmed.

### Safety

This remains a diagnostic release.

- `RS` is a read-only system-status request.
- No OPEN, CLOSE, STOP, PED or other movement command is sent.
- The raw `ACK RS` payload is not logged by the new diagnostic.
- An `ACK RS` response does **not** bypass `DEV INFO` / `DEV STATUS` validation.
- PIN verification remains unchanged.
- Gate control is not enabled from the RS response alone.

### Testing

Update to **0.9.10** through HACS, restart Home Assistant, and try setup again
with debug logging enabled.

Please share the privacy-safe lines containing:

```text
Powertech AWS endpoint diagnostic
Powertech shadow request rejected
Powertech read-only system status diagnostic requested
Powertech read-only system status response received
Powertech shadow validation timed out
```

The timeout line now also includes:

```text
rs_requested=...
rs_ack_received=...
rs_ack_format_valid=...
rs_publish_failures=...
```

If `rs_ack_received=True`, that will confirm that the controller is reachable
through the normal WBT command channel even though its default AWS IoT shadow
is unavailable.
