# Explicit system-status capture — 0.9.16b3

Separate diagnostic branch based on the tested position-feedback build. Adds
`powertech_gate.capture_system_status` for a specifically selected loaded PS19001
config entry. It never starts automatically.

The action sends only the fixed read-only `RS` command, with the existing source
ID, on the existing authenticated MQTT connection. It accepts no arbitrary
command, topic, credentials or payload. Cover commands and feedback logic are
unchanged from b2. Raw replies are captured with the existing numeric allowlist;
the probe does not apply RS data to cover state.

Enable feedback capture first. Set `config_entry_id` to the desired integration
entry and `duration` to 1-90 seconds (default 60). Duration 0 cancels. Requests
are at least two seconds apart, with at most 45 during a 90-second window.
The probe waits up to three seconds for a structurally valid RS reply and stops
after the first unanswered request. It also stops on publish failure,
disconnection, disabled capture, cancellation, or entry unload/restart. Concurrent
probes for the same client are rejected. A final reply may be awaited up to
three seconds beyond the sampling window.

Diagnostics include `system_status_probe` request/response counts and finish
reason. Capture includes timestamped `status_request` events and allowlisted
`ACK RS` bytes. A valid reply is evidence of a response to an RS-capable path,
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
