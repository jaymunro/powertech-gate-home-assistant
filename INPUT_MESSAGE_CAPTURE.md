# Input/source investigation build — 0.9.16b9

This separate diagnostic branch retains b8's verified cover logic and adds an
explicit passive capture action. It is independent of upstream feedback PR #8.

`powertech_gate.capture_input_messages` takes `config_entry_id` and `duration`
(0 to stop; 1–180 seconds to start a fresh window). It sends no command and adds
no subscriptions. Existing status polling continues unchanged. It records all
received payload types on the existing command-reply, position and shadow
accepted/rejected/update subscriptions, before ordinary message handling.

The private diagnostics field `input_message_capture` includes unfamiliar text,
extra shadow fields, original receive times, sequence numbers, payload lengths,
retain/duplicate flags and format. IDs in `src` are replaced with consistent
salted aliases per window; this HA connection is labeled `home_assistant`.
Aliasing does not prove that a source is a radio transmitter or physical input.
Known credential fields, IP/MAC/email values and known controller/account-source
identifiers are redacted. Captures may still contain private unknown protocol
data: never publish a diagnostic export without separately reviewing it.

Capture stops accepting messages at the deadline. Memory is limited to 512
messages, each up to 16 KiB. Oversized payloads are marked omitted. Exports older
than one hour are cleared on access; restarting discards all captures. A new
window replaces the old window, so save private results before starting again.

## Test sequence

1. Install this exact prerelease through the existing fork in HACS, restart HA
   once and verify the same covers, IDs and ordinary status polling recover.
2. Arm a short idle window; verify new capture data and known redactions. Stop
   and save it privately before requesting any user-operated physical test.
3. Obtain user readiness, arm a fresh window and signal capture started before
   the user operates one input. Compare wired pedestrian, wired full, transmitter
   pedestrian and transmitter full separately, each through automatic closure.
4. Look for unsolicited messages, source aliases or extra shadow changes before
   movement. Distinguish them from responses to the regular READ STATUS polls.
5. Treat press intent separately from actual opening/stopping/closing. Do not
   create event entities or announce a mode until signatures are verified.

No movement, pairing, learning, PIN or parameter commands are added. Rollback:
select existing fork tag 0.9.16b8 in HACS and restart; preserve the config entry.
