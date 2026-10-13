# Changelog

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
