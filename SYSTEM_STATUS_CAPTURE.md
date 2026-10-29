# Explicit system-status capture — 0.9.16b6

Separate diagnostic branch based on the tested position-feedback build. Adds
`powertech_gate.capture_system_status` for a specifically selected loaded PS19001
config entry. It never starts automatically.

b6 adds optional `include_shadow: true`: each sample also requests the existing
AWS shadow with fixed empty payload. This reads stored cloud data and does not
force a fresh controller measurement. Compare captured raw bytes, shadow version
and status timestamps against the live text replies. Defaults to false; only the
explicit bounded capture uses this faster snapshot cadence. A failed shadow
publish stops the capture. At most 45 shadow GETs in a 90-second window.

The action sends only fixed read-only status commands: `READ STATUS` for reported UART 1,
or `RS` for newer UART, with the existing source
ID, on the existing authenticated MQTT connection. It accepts no arbitrary
command, topic, credentials or payload. Cover commands and feedback logic are
unchanged from b2. The initial RS idle test on this UART-1 controller returned `ERROR:RS;src`;
b4 therefore follows the app's legacy READ STATUS selection.

Raw replies are captured with the existing numeric allowlist;
the probe does not apply RS data to cover state.

b5 also recognizes the legacy `SINGLE` status prefix. The previous allowlist
missed `ACK STATUS:SINGLE STOPPED,26` and stopped a pedestrian capture early.
This only corrects capture parsing; it does not assign physical leaf semantics
to `SINGLE`, `PED`, or their numeric positions.

Enable feedback capture first. Set `config_entry_id` to the desired integration
entry and `duration` to 1-90 seconds (default 60). Duration 0 cancels. Requests
are at least two seconds apart, with at most 45 during a 90-second window.
The probe waits up to three seconds for a structurally valid RS or ACK STATUS reply and stops
after the first unanswered request. It also stops on publish failure,
disconnection, disabled capture, cancellation, or entry unload/restart. Concurrent
probes for the same client are rejected. A final reply may be awaited up to
three seconds beyond the sampling window.

Diagnostics include `system_status_probe` request/response counts and finish
reason. Capture includes timestamped `status_request` events and allowlisted
`ACK RS` bytes or `ACK STATUS` mode/position. A valid reply is evidence of a response to an RS-capable path,
not proof that the firmware freshly sampled every sensor. Compare changing
bytes with observed movement. RS has no transaction ID, so replies from another
client cannot be distinguished; keep EyeOpen closed during controlled captures.

First request one idle sample and confirm a valid response before starting a
movement window. The user operates the physical full-opening and pedestrian
buttons in separate windows, allows auto-close, and reports completion times.
Read diagnostics after each test. Do not change auto-close or other settings.

Rollback: download exact fork tag `0.9.16b2` through HACS and restart HA. Preserve
the integration entry, options and entity IDs. The diagnostic action disappears;
the validated b2 feedback behavior and position sensor remain.
