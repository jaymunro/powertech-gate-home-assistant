# Powertech Gate (EyeOpen) 0.9.5

## Improved diagnostics

This release helps investigate AWS IoT shadow request failures reported by a PS20088 user after v0.9.4 fixed device discovery.

- When AWS IoT rejects a shadow GET request, the integration now logs **only the numeric rejection code**, for example `Powertech shadow request rejected; code=403`.
- If the response is malformed or the numeric code is missing, the log shows `code=None`.
- The full AWS error payload is **not logged** to avoid exposing request metadata.

This is a **diagnostic update**, not a confirmed fix for the underlying shadow rejection. Gate control remains disabled unless passive validation receives both `DEV INFO` and `DEV STATUS`.

No changes to device discovery, certificate/policy provisioning, PIN verification, MQTT command transport, or gate movement.

## Updating

Update to **0.9.5** through HACS and restart Home Assistant.

If your setup previously failed during passive validation, retry adding the integration (or Reconfigure an existing entry), then enable Powertech debug logging and check for:

```text
Powertech shadow request rejected; code=...
Powertech candidate rejected after passive shadow validation
```

Share only the sanitized Powertech lines rather than a complete Home Assistant log.
