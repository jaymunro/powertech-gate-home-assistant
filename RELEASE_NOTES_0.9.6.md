# Powertech Gate (EyeOpen) 0.9.6

## Improved AWS IoT shadow request reliability and diagnostics

This release addresses a possible MQTT subscription timing issue reported during
community testing of PS20088 setup. The integration now waits for SUBACK
confirmation of both AWS IoT shadow GET response topics before sending the
initial shadow request, and retries unanswered requests during the existing
12-second passive validation window.

The logs now show privacy-safe subscription outcomes, shadow GET attempt counts,
accepted/rejected response counts and a concise timeout summary. Credentials,
Thing IDs, endpoints and raw AWS response bodies are not added to these logs.

**This is a diagnostic/reliability release.** If your device does not expose
`DEV INFO` and `DEV STATUS` through its AWS shadow, setup will still stop safely.
No gate movement commands are sent during setup validation. Gate controls,
certificate provisioning, PIN handling and support for shared accounts remain
unchanged.

## Updating / testing

1. Update through HACS to 0.9.6 and restart Home Assistant.
2. Retry setup or Reconfigure with Powertech debug logging enabled.
3. If passive validation still fails, share only the `Powertech MQTT subscription`,
   `Powertech shadow GET` and `Powertech shadow validation timed out` lines
   in the Home Assistant Community thread.

Feedback: https://community.home-assistant.io/t/powertech-gate-eyeopen-gate-control-and-live-status-in-home-assistant/1023045
