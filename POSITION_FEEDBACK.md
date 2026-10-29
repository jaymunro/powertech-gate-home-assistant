# PS19001 position feedback test — 0.9.16b2

This test branch builds on the opt-in capture build. It fixes PS19001 cover
open/closed reporting and adds one diagnostic **Controller position** sensor.
Other models retain their existing cover behaviour. Commands and security settings
are unchanged; no extra MQTT requests or movement commands are introduced.

## Evidence and behaviour

Three captured cycles were replayed offline: physical pedestrian opening,
physical full opening, and HA pedestrian opening, each followed by auto-close.
The shared position stream reached 40 in pedestrian mode and 100 in full mode,
then returned to zero. The old decoder remained closed during every cycle;
the old pedestrian cover also kept an earlier `ACK PED OPEN` indefinitely.

After receiving a valid live position, PS19001 covers use zero as closed and
nonzero as open. Later shadow refreshes cannot overwrite that position with an
incorrect endpoint estimate. A pedestrian-open ACK provides the existing immediate
open indication, but the next live position supersedes it. A close ACK alone does
not prove closure. Retained or out-of-range position messages are ignored for this
model. The original decoder is preserved for other models.

No movement direction is inferred: a value such as 40 can mean an intermediate
point or a stationary pedestrian opening. Both covers describe the same physical
gate opening; they are command modes, not independent leaf-position measurements.
The position sensor reports the controller's shared travel scale. It is not a
percentage for either individual leaf, and it offers no set-position command.

## Limitations and testing

The sensor starts unknown after a restart until a live position arrives. Covers
retain their existing shadow fallback until the first live position. Captured
positions have no source timestamp, so arbitrary delayed messages cannot be
ordered beyond MQTT arrival order. Connection loss still makes entities unavailable.

31 offline tests passed, including all three real-message replays, stale ACKs,
shadow refreshes, invalid/retained feedback, connection availability, other-model
behaviour, and the existing capture/privacy/background-task tests.

Physical validation on the fixed build remains required. User-operated tests:

1. Physical pedestrian open, then auto-close.
2. Physical car/full open, then auto-close.
3. HA pedestrian open, then auto-close.

Observe both covers and the Controller position sensor, and retrieve capture after
each cycle. Do not change auto-close or other board settings for this test.

Rollback: download fork release `0.9.16b1` through HACS and restart HA. Keep the
existing integration entry and credentials. The diagnostic position entity is new;
all existing entity unique IDs remain unchanged. Do not accept HACS's default main
branch update while testing; select the exact prerelease tag explicitly.

Button-source detection, individual leaf sensors and configuration controls are
outside this branch. Submit the validated feedback fix separately from the model
recognition PR and future feature work.
