> 状态：DEPRECATED —— 本端口冲突扫描能力已被单端口网关模式取代。

## ADDED Requirements

### Requirement: External port conflicts are detected
The system SHALL scan /etc/nginx/conf.d/*.conf to detect whether external_port is already in use.

#### Scenario: conflict detected
- **WHEN** any existing server block listens on the requested external_port
- **THEN** the deployment is blocked with a clear conflict error

### Requirement: Listen parsing ignores non-listen ports
The system SHALL extract ports only from listen directives and SHALL ignore ports found in comments or proxy_pass lines.

#### Scenario: comment port ignored
- **WHEN** a configuration contains a port in a comment or proxy_pass line
- **THEN** the port is not considered in conflict detection

### Requirement: Listen parsing supports IPv4/IPv6 forms
The system SHALL parse listen directives that include IPv4 or IPv6 address prefixes.

#### Scenario: address-prefixed listen
- **WHEN** a listen directive includes 0.0.0.0:<port> or [::]:<port>
- **THEN** the port is extracted for conflict detection

### Requirement: Same-app updates are allowed
The system SHALL treat a conflict as safe when the port is already owned by the same app being updated.

#### Scenario: same app reuses port
- **WHEN** a configuration file name shares the same app_name prefix and already listens on external_port
- **THEN** the deployment proceeds and overwrites the existing config

### Requirement: Conflict errors include owner hint
The system SHALL raise PortConflictError and include the conflict_conf filename in the error message.

#### Scenario: conflict error detail
- **WHEN** a conflict is detected
- **THEN** the error includes the conflicting configuration filename
