# PS19001 observed status feedback

PS19001 physical buttons, paired transmitters and automatic closure do not
consistently publish position events. Its AWS shadow can also stay unchanged
through movement. Polling the controller's legacy `READ STATUS` response
supplies independent physical feedback, without requiring a Home Assistant
command acknowledgement.

## Scope and timing

Only PS19001 reporting UART 1 receives background status requests. Other
models receive no new commands. The entry owns the background task, so startup
does not wait for it, and unloading cancels it.

Polling runs every 10 seconds at idle and every 2 seconds during detected
activity for up to 90 seconds. A new opening or closing phase restarts that
window. A request waits at most 8 seconds before backing off to 20, 40, then
60 seconds. There is at most one request awaiting a reply. The poller sends
only `READ STATUS`; movement commands and controller settings are unchanged.

Feedback older than 60 seconds makes the covers and travel sensor unavailable
on the next update. Retained or malformed replies are not fresh evidence.
Shadows continue updating metadata but cannot overwrite observed live state.
An independent position event clears old direction; position zero closes both
modes. Command acknowledgements alone do not establish physical closure.

## Access modes and physical state

These two covers represent car and pedestrian access modes, not individual
left and right leaves:

| Observed feedback | Car cover | Pedestrian cover |
| --- | --- | --- |
| CLOSED with raw position 0–5 | closed | closed |
| SINGLE STOPPED with position above 5 | closed | open |
| OPEN or OPENED with position 95–100 | open | closed |
| Movement without an identified mode | unknown | unknown |
| Closing after an identified mode | active mode closing | other mode closed |
| Stale or disconnected | unavailable | unavailable |

A closed car-mode cover does not mean the whole gateway is physically shut.
Use the **Physical gate closed** binary sensor for that distinction. It is
enabled by default for PS19001 / UART 1, including when UART metadata arrives
after startup. Its unique ID ends in `_physical_gate_closed`. **On** confirms
closure from fresh controller feedback; **off** means the gateway is not closed,
including pedestrian opening, full opening and motion before the mode is known.
It becomes **unavailable** on disconnection or expired feedback, rather than
retaining a misleading confirmed-closed value. It has no opening device class
because that class uses the opposite polarity (on = open).

Security conditions must require this sensor to be explicitly **on**; unknown
or unavailable is not confirmation of closure. This remains cloud controller
feedback, with the same polling delay and freshness bounds as the covers; it
is not a new physical contact sensor or an immediate alarm-grade signal.

The existing `physical_gate_closed` cover attribute is preserved and is unknown
when feedback is stale. Cover attributes also expose `representation`,
`opening_mode`, `physical_gate_state`, `controller_status`, `status_position`
and `feedback_source`.

The controller's PED prefix occurs during both types of movement and does not
identify the active mode. Classification uses stationary feedback. A short
opening may reach its stationary state before the next idle poll. Interrupted
or unusual cycles need further physical validation; no leaf positions are
inferred from the single controller travel value.

The diagnostic position sensor reports that raw travel value, not a normalized
per-leaf percentage. Entity IDs of existing covers are preserved. The separate
model-support PR #7 adds automatic pedestrian-capability recognition for
PS19001; this change does not duplicate its model-list modification.

## Validation

Offline tests replay sanitized physical-button full and pedestrian cycles
through production API and cover code, interleaving stale shadows. They also
cover invalid/retained feedback, endpoint tolerance, freshness, model isolation,
request gating, timeout backoff, cancellation and background task ownership.
Fixtures contain no account, controller or network identifiers.

On a PS19001 with module firmware P3.6 / UART 1, the development build's same
status and cover logic was tested with paired wireless transmitters:

- Pedestrian: SINGLE STOPPED at 25 selected pedestrian mode; CLOSING at 22
  and 2 retained it; CLOSED at 0 closed both mode covers after automatic closure.
- Both leaves: initial position 40 and OPENING at 65/87 left the mode unknown;
  OPENED at 100 selected car mode; CLOSING at 84/47/23/0 retained it until
  CLOSED at 0 closed both covers.

The clean PR removes experimental capture services and alternative protocol
probes. Its offline tests are separate from the physical testing of the prior
development build. No new physical movement was initiated for PR preparation.
