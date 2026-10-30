# Physical gate closed — 0.9.16b10

Adds one operational binary sensor to the existing PS19001 / UART 1 device.
Physical gate closed is on only when fresh controller feedback confirms
closure; off means not closed, including movement and either access mode.
It becomes unavailable when disconnected or feedback is older than the existing
60-second freshness bound (on the next normal update). Unknown/unavailable
must not be treated as confirmation of closure in a security condition.

No opening device class is set, because its on=open polarity contradicts this
sensor's on=closed name. It is enabled by default and uses the stable unique ID
suffix _physical_gate_closed. Discovery also works if UART metadata arrives
after startup. Existing cover IDs, attributes, modes, commands and polling
intervals are unchanged. This is cloud controller feedback, not a new physical
contact sensor. No history API login, event path or announcement changes.

Validation: 76 offline tests pass, including the ten new closure entity tests;
compilation and diff checks pass. Offline replay includes both access modes,
unknown movement, closing at zero, stale/retained/invalid feedback, disconnection,
startup without feedback and delayed discovery. No gate operation is needed to
install this change. Runtime verification is separate from offline replay.

Install exact fork tag 0.9.16b10 through HACS, preserve the existing entry and
options, then restart Home Assistant once. Verify the new entity and existing
cover IDs; do not migrate security or announcements as part of this deployment.
Rollback: download exact fork tag 0.9.16b9 and restart once.
