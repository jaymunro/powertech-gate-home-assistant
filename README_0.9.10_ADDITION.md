## Read-only RS diagnostic (0.9.10)

When the default AWS IoT shadow returns `404`, version 0.9.10 performs one
additional read-only compatibility check based on the official EyeOpen WBT01
implementation.

The integration sends:

```text
c=RS;src=<source_id>
```

to the existing `<thing>/wbt01Rx` topic and waits for an `ACK RS:` response on
`<thing>/wbt01Tx`.

This is a status-read command, not a movement command. The diagnostic does not
send OPEN, CLOSE, STOP or pedestrian commands.

For privacy and safety, the new log output records only whether a response was
received, whether its hexadecimal structure is valid, and the number of status
bytes. The raw `ACK RS` status value is not logged by the diagnostic.

An `ACK RS` response is diagnostic evidence only. It does not bypass the
existing requirement for `DEV INFO`, `DEV STATUS` and PIN validation before
automatic gate control is enabled.
