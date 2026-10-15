## What's changed

### Targeted AWS IoT endpoint diagnostics

Version **0.9.9** follows up on the persistent default-shadow `404` seen on some
PS20088 accounts.

APK analysis of the official EyeOpen Android app confirmed that the WBT01 path
uses a fixed AWS IoT endpoint in `eu-central-1`. This release now compares the
endpoint returned by the Powertech user-certificate API with that official
WBT01 endpoint.

The diagnostic log contains only safe values such as:

```text
Powertech AWS endpoint diagnostic; certificate_endpoint_matches_official=True certificate_region=eu-central-1
```

The raw endpoint hostname, certificate ARN, certificate, private key and device
credentials are not logged.

### 0.9.8 rollback

The broader MQTT wildcard subscriptions introduced in 0.9.8 are removed.
Community testing showed that those subscriptions could cause the AWS IoT
session to disconnect before the normal shadow subscriptions were ready.

0.9.9 therefore restores the known-good MQTT subscription behavior from 0.9.7.

### Safety

This is still a diagnostic release.

- The endpoint used for MQTT is **not** changed automatically.
- The UUID is still used as the AWS IoT Thing name.
- Certificate provisioning and policy attachment are unchanged.
- `DEV INFO` / `DEV STATUS` validation remains mandatory.
- No gate movement command is sent during compatibility validation.

### Testing

Update to **0.9.9** through HACS, restart Home Assistant and try setup again
with debug logging enabled.

Please share these privacy-safe lines:

```text
Powertech AWS endpoint diagnostic
Powertech AWS endpoint source diagnostic
Powertech shadow request rejected
Powertech shadow validation timed out
```
