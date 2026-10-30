# Gate state — 0.9.16b11

The operational binary sensor is named Gate state and uses the opening device
class. Home Assistant displays Open (on), Closed (off), or Unavailable. Open
means not closed, including motion and either access mode. Closed requires
fresh controller feedback. Unknown/unavailable must not confirm closure.

The b10 prototype used the opposite polarity (on=closed). Any condition written
for that prototype must be changed to require off for closure. Before this
update, the HA search found no automation/script/scene/helper consumer. The user
explicitly requested renaming the unused entity ID to
binary_sensor.gate_front_gates_gate_state. The internal unique ID is retained
for registry continuity; rename the existing entity through the registry API.
The display name is supplied by integration translation, not a user override.

PS19001/UART1 discovery, freshness/disconnection handling, cover IDs, attributes,
modes, commands and polling intervals are unchanged. This is cloud controller
feedback, not a new contact sensor. No history API, announcement or security
changes. During movement Open means not fully closed.

IP address and Wi-Fi MAC diagnostics now default to disabled; controller position
remains enabled. Existing registry preferences are preserved by an upgrade.

Validation: 78 diagnostic-build and 48 clean-PR tests, plus compilation/diff
checks. No gate operation required; runtime verification is separate from replay.
Install exact fork tag0.9.16b11 through HACS and restart once. Verify Gate state
shows Closed for fresh PED CLOSED/0. Rollback exact tag0.9.16b10 and restart;
rollback also restores b10's opposite polarity and original display name.
