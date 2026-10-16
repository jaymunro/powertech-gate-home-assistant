## Passive EyeOpen traffic observation (0.9.11)

Version 0.9.11 observes the already-authorized `wbt01Tx` and `position` MQTT
topics for at least 30 seconds during setup. Home Assistant sends no diagnostic
or movement command during this window.

Start setup, then operate the same gate once from the official EyeOpen app.
The log records only message counts for the known topics. Raw payloads are not
included in the new passive-observation lines.

Observed traffic does not bypass `DEV INFO`, `DEV STATUS` or PIN-related safety
validation.
