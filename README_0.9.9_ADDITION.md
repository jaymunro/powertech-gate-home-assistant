## AWS endpoint diagnostics (0.9.9)

Version 0.9.9 removes the broad MQTT wildcard subscriptions added in 0.9.8
because community testing showed that those subscriptions could cause the AWS
IoT session to disconnect before normal shadow validation completed.

The release also adds a privacy-safe comparison between:

- the AWS IoT endpoint returned by the Powertech user-certificate API, and
- the WBT01 endpoint hard-coded by the official EyeOpen Android application.

Only boolean comparison results and the AWS region label are logged. The raw
endpoint hostname, certificate ARN, certificate contents and private key are
not logged.

The integration does **not** force or substitute the official endpoint in this
release. Provisioning, policy attachment, the UUID-based Thing name, and the
existing `DEV INFO` / `DEV STATUS` safety validation remain unchanged.
