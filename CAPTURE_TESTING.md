# Feedback capture test build

Version `0.9.16b1`, based on upstream 0.9.15 plus PS19001 recognition.
This branch only adds diagnostic observation. It does not fix state precedence,
send extra MQTT requests, or change gate commands, security, or auto-close timing.

Enable **Capture gate feedback (last hour, up to 512 events)** under the existing
Powertech integration's Options. No account reconfiguration or PIN entry is needed.
Enabling/disabling takes effect immediately. Disabling clears the in-memory history;
restarting/reloading also clears it. Capture is off by default. Download diagnostics
promptly after each test: the history holds at most 512 events and expires after one hour.

Diagnostics include a `feedback_capture.events` array with UTC receipt timestamps,
sequence numbers, numeric position payloads before the existing clamp, parsed status
bytes, known acknowledgements, post-message internal state and observed cover decisions.
Shadow versions and per-status vendor timestamps help distinguish stale shadow data.
MQTT callbacks and HA cover callbacks run on different threads: use sequence and
timestamps, and do not assume the cover row always follows the related MQTT row.

Only allowlisted fields are retained. Full payloads, PIN fields, UUIDs, source IDs,
IP/MAC addresses, certificates and unknown acknowledgement text are excluded.
The history is local to HA until diagnostics are retrieved or shared; it is not uploaded
to GitHub. Keep captures private unless a sanitised example is deliberately submitted.

## Physical tests (user operates the gate)

1. Note the time; use a physical full-opening control, then let the gate auto-close.
2. Open fully from HA, then let it auto-close.
3. Open pedestrian mode from HA, then let it auto-close.
4. Open pedestrian mode, then explicitly close it from HA.
5. If useful, repeat pedestrian mode using its physical control or EyeOpen.

For each cycle, note actual movement and when the gate is physically closed. Retrieve
diagnostics between cycles to avoid overwriting earlier events. An acknowledgement or
an integration state alone is not proof of the physical gate position.

## Install and rollback

Use only one HACS repository to manage `custom_components/powertech_gate`. Preserve the
existing HA config entry and all entities. Install the fork's tested tag, restart HA,
verify version and unchanged entity IDs, then enable capture. Do not remove the HA
integration or reconfigure credentials merely to change its code source.

Rollback by downloading upstream 0.9.15 again and restarting HA. It lacks PS19001 in its
model list: the saved capability flag currently keeps the pedestrian entity enabled,
but reconfiguration on upstream 0.9.15 would reset it. Record HACS source/version and
capture options before switching. Do not update both sources over the same directory.
