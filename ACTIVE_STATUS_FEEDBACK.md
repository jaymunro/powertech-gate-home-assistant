# PS19001 active legacy feedback test build — 0.9.16b8

Physical buttons and automatic closure do not consistently publish position
messages. This build reads the PS19001's verified legacy READ STATUS response
and applies its observed state independently of stale AWS shadow snapshots.
It is based on the tested diagnostic branch, on active-status-feedback.

State handling is independent of command origin: Home Assistant controls,
physical controller buttons and paired wireless transmitters all use the
controller's observed feedback. No HA command ACK or button event is required.
Transmitter-operated full/pedestrian cycles must also be physically validated;
the existing replay fixtures came from physical-button cycles.

## Scope and cadence

- Enabled only for PS19001 reporting UART 1. Other models/protocols retain their
  existing state handling; they receive no background status requests.
- Entry-owned background task; setup does not await this long-running loop.
- Normal interval 10 seconds, at most one request awaiting a reply. Replies may
  take up to 8 seconds. Detected non-closed activity uses a 2-second interval for
  up to 90 seconds; a new opening/closing phase can start another fast window.
- Timeout/publish failures back off to 20,40,then60 seconds. No command retries
  for gate movement are added. Unknown/disconnected devices are not polled.
- Feedback older than60 seconds makes these covers and the travel sensor
  unavailable on their next update. No startup shadow-only closed assumption
  is used once the UART-1 feedback path is active.
- Polling works independently of optional diagnostic capture. An explicit
  diagnostic probe pauses background sampling. Starting a probe while a
  background request is awaiting a reply is rejected; retry after it completes.

## Covers represent access modes

The user selected access-mode semantics for the existing cover entities:

| Observed condition | Car cover | Pedestrian cover |
| --- | --- | --- |
| Explicit CLOSED with raw position0-5 | closed | closed |
| SINGLE STOPPED above5 | closed | open |
| OPENED at95-100 | open | closed |
| Opening without a known mode | unknown | unknown |
| Closing after a known mode | active mode closing | other mode closed |
| Stale/disconnected feedback | unavailable | unavailable |

This is deliberately not a left/right leaf representation. A closed car cover
means car-access mode is inactive; it does not prove both leaves are shut. Each
cover exposes representation=access_mode, opening_mode, physical_gate_closed,
physical_gate_state, controller_status, status_position and feedback_source.
Use physical_gate_closed for whole-gateway closed checks.

PED prefixes do not select a mode: they occurred during both confirmed types
of movement. Classification uses the observed stationary SINGLE STOPPED and
full OPENED conditions. Until classification, new physical-button movements
remain unknown for the two modes; physical direction/state is in attributes.
Manually interrupted/unusual cycles require further physical validation.

Stale shadows still refresh module metadata but cannot override live state or
position. A new position event can supersede status feedback and clear stale
direction; zero closes both modes. Command ACKs alone do not establish physical
state. Retained and malformed feedback are not used as fresh physical evidence.

The existing diagnostic travel sensor preserves raw controller values:98 for
full open,26 for pedestrian rest in captured examples. It is not a normalized
per-leaf percentage. Its attributes state that distinction. There are no new
leaf sensors, renamed entity IDs, auto-close settings or movement commands.

## Validation and rollback

Offline tests replay sanitized confirmed full and pedestrian cycles through
real API and cover code, interleaving stale shadow replies. Additional checks
cover endpoint tolerance, invalid/retained replies, loss of freshness, model
isolation, bounded polling, timeout backoff, cancellation and background task
ownership. Live idle and user-operated movement checks remain necessary after
installation; unit replay is not physical validation.

Rollback: download fork tag0.9.16b7 in HACS and restart Home Assistant. Preserve
the existing config entry, options and entity IDs. This removes background
status polling and restores the preceding position-based cover behavior.
