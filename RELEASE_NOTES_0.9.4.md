# Powertech Gate (EyeOpen) 0.9.4

## Fixed

Improved device discovery for EyeOpen accounts whose initial device-list response omits `iot_endpoint`.

- Devices with a stable UUID are now included in discovery even when the initial record has no AWS IoT endpoint.
- Automatic certificate provisioning still supplies the authoritative AWS IoT endpoint before policy attachment and MQTT connection.
- Existing devices with an endpoint continue through the same provisioning and passive validation process.

**Testing:** The endpoint-less path passed simulated discovery/provisioning tests. An existing PS20088D installation was also successfully reconfigured with the change. Marek's endpoint-less PS20088 hardware case still needs real-world confirmation.

No changes to movement commands, pedestrian control, PIN verification or runtime MQTT behavior.

## Updating

Update through HACS and restart Home Assistant. If your gate was previously missing during automatic setup, try adding the integration again using your EyeOpen account. Existing working installations do not need Reconfigure for this update.
