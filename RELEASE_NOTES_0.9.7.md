## What's changed

### Privacy-safe AWS Thing identifier diagnostics

Version 0.9.7 adds targeted diagnostics for accounts where AWS IoT MQTT connects
successfully but the default device shadow returns `404`.

The Powertech backend schema can vary between accounts and controller models.
During device discovery, the integration now looks for a conservative set of
possible Thing/client/device identifier fields and records only:

- the field name,
- a non-reversible short fingerprint,
- whether the fingerprint matches the device UUID currently used as the AWS
  Thing name.

Raw identifiers are **not** logged.

### Safety

This is a diagnostic release.

- The integration still uses the device UUID as the AWS Thing name.
- It does not automatically probe alternate Thing names.
- Passive `DEV INFO` / `DEV STATUS` validation remains required.
- No gate movement command is sent during compatibility validation.

### What to share when testing

With debug logging enabled, please share the privacy-safe lines beginning with:

```text
Powertech discovery item
Powertech selected AWS Thing identifier
Powertech shadow request rejected
Powertech shadow validation timed out
```

Do not share full unredacted Home Assistant logs.
