## ADDED Requirements

### Requirement: Health endpoint provides a human-readable environment report
The service SHALL expose `GET /env/health` and SHALL return a JSON report that is formatted with indentation for human readability.

#### Scenario: Requesting the environment report
- **WHEN** a client sends `GET /env/health`
- **THEN** the service responds with HTTP 200 and a pretty-printed JSON report

### Requirement: Health report includes path availability and permission results
The report SHALL include status for `/vol1/1000/` and `/vol1/1000/MyDocker/web-cluster/sites`, including explicit reason codes for unreachable vs permission denied.

#### Scenario: Host path is unreachable
- **WHEN** the probe cannot reach the host path target
- **THEN** the report marks the path status as `unreachable` and includes the failure reason

#### Scenario: Host path permission is denied
- **WHEN** the probe reaches the host path but lacks permissions
- **THEN** the report marks the path status as `permission_denied` and includes the failure reason

### Requirement: Write permission probe cleans temporary files
Write permission checks SHALL create a `.sitehub_probe` file and SHALL always remove it, even on failure.

#### Scenario: Write permission probe succeeds
- **WHEN** the probe creates and deletes `.sitehub_probe`
- **THEN** the report marks the path as writable and `.sitehub_probe` does not exist

#### Scenario: Write permission probe fails
- **WHEN** the probe encounters a failure during write validation
- **THEN** the report marks the path as not writable and `.sitehub_probe` does not exist

### Requirement: Health report includes SSH handshake latency warning
The report SHALL include SSH handshake latency and SHALL mark a warning when the latency exceeds 2000ms.

#### Scenario: SSH latency exceeds threshold
- **WHEN** the SSH handshake latency is greater than 2000ms
- **THEN** the report includes a warning indicating elevated latency

### Requirement: Nginx configuration backup retains a bounded history
When the system performs an Nginx configuration backup, it SHALL create a timestamped backup file and retain only the most recent 5 backups.

#### Scenario: Backup retention is enforced
- **WHEN** a new backup is created
- **THEN** the backup file name includes a timestamp suffix and only the latest 5 backups remain

### Requirement: Environment probes are executed asynchronously
The health endpoint SHALL execute environment probes concurrently and SHALL mark slow probes as timed out when they exceed the configured timeout.

#### Scenario: Probe exceeds timeout
- **WHEN** a probe exceeds the configured timeout
- **THEN** the report marks the probe status as `timeout`
