# Changelog

## 0.9.9
- Remove the broad MQTT wildcard subscriptions introduced in 0.9.8 after community testing showed they could disrupt the AWS IoT session before normal shadow validation completed.
- Restore the known-good 0.9.7 MQTT subscription behavior.
- Add privacy-safe diagnostics comparing the user-certificate AWS IoT endpoint with the endpoint hard-coded by the official EyeOpen WBT01 client.
- Log only boolean comparison results and the AWS region label; raw endpoints, certificates and credentials are not logged.
- Keep certificate provisioning, policy attachment, Thing UUID selection and `DEV INFO` / `DEV STATUS` safety validation unchanged.
- Diagnostic release for investigating persistent default-shadow `404` responses on some PS20088 accounts.

## 0.9.8
- Add passive MQTT topic diagnostics for devices whose default AWS IoT shadow consistently returns `404`.
- Subscribe to the existing thing-scoped MQTT namespace and named-shadow update namespace without sending gate movement commands.
- Record only topic categories, counts, SUBACK results, and short non-reversible fingerprints for unknown topic suffixes.
- Never log payloads from newly observed topics; command-ack payload logging is also removed.
- Keep `DEV INFO` / `DEV STATUS` shadow validation unchanged. Passive topic activity does not enable gate control by itself.
- Diagnostic release intended to determine whether affected controllers report state outside the default AWS IoT shadow.

## 0.9.7
- Add privacy-safe discovery diagnostics for possible alternate AWS IoT Thing identifiers.
- Fingerprint only a conservative allow-list of identifier-like backend fields such as Thing/client/device IDs; raw values are never logged.
- Log whether each candidate identifier fingerprint matches the UUID currently used as the AWS Thing name.
- Include the same privacy-safe checks for nested `devies_info` records used by shared devices.
- Keep the current UUID-based Thing selection and all gate-control safety validation unchanged.
- Diagnostic release for investigating PS20088 accounts where MQTT connects successfully but the default shadow GET returns HTTP-style AWS code 404.

## 0.9.6
- Wait for AWS IoT subscription acknowledgements for both shadow GET response topics before sending the initial shadow request.
- Retry unanswered shadow GET requests within the existing 12-second passive validation window.
- Add privacy-safe logging for MQTT subscription requests, SUBACK outcomes, shadow GET attempts and validation timeouts.
- Preserve all existing gate movement commands, PIN handling and post-provisioning safety validation.
- Diagnostic/reliability release: does not guarantee compatibility for devices that never expose the required DEV INFO / DEV STATUS shadow fields.

## Previous releases
See the repository history for earlier release notes.
