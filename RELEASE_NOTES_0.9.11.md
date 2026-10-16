## What's changed

### Passive EyeOpen MQTT observation

Version **0.9.11** adds a 30-second passive observation test for controllers
where MQTT connects, the default shadow returns `404`, and the read-only `RS`
diagnostic receives no response.

Home Assistant listens only to the already-authorized:

```text
<thing>/wbt01Tx
<thing>/position
```

topics, together with the normal shadow response topics.

### How to test

Update to **0.9.11** through HACS and restart Home Assistant.

Start adding the integration. Immediately after starting the setup attempt, use
the official EyeOpen app to operate the same gate once, then wait for the
Home Assistant setup attempt to finish.

Please share the lines containing:

```text
Powertech passive MQTT observation window started
Powertech passive MQTT activity observed
Powertech shadow validation timed out
```

The final timeout line includes:

```text
passive_command_ack_messages=...
passive_position_messages=...
```

### Safety

This remains a diagnostic release.

- Home Assistant sends no OPEN, CLOSE, STOP, PED or other movement command.
- The 0.9.10 `RS` request is not sent during this test.
- No wildcard MQTT subscriptions are used.
- Passive traffic does not bypass existing protocol or PIN validation.
- Gate control is not enabled from passive traffic alone.
