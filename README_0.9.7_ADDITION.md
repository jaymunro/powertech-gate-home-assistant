## AWS Thing identifier diagnostics (0.9.7)

Version 0.9.7 adds privacy-safe discovery logging to investigate accounts where
MQTT connects successfully but the default AWS IoT shadow returns `404`.

The integration still uses the Powertech device UUID as the AWS Thing name.
During discovery it now checks a conservative allow-list of possible alternate
identifier fields (for example Thing/client/device ID variants) and logs only:

- the backend field name,
- a non-reversible short SHA-256 fingerprint,
- whether that fingerprint matches the UUID fingerprint.

Raw identifiers are never written to these diagnostics. Shared-device
`devies_info` records receive the same treatment.

This release does not automatically try alternate Thing names and does not
bypass passive protocol validation. The additional diagnostics are intended to
determine whether a future compatibility fix can safely select a different
Thing identifier for affected accounts.
