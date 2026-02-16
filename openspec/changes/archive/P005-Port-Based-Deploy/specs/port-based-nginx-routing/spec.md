> 状态：DEPRECATED —— 本端口驱动路由模式已被单端口网关模式取代。

## ADDED Requirements

### Requirement: Port-based routing is enabled by external_port
The system SHALL enable port-based Nginx routing when sitehub.yaml defines external_port within 8400-8500.

#### Scenario: external_port in range
- **WHEN** external_port is between 8400 and 8500
- **THEN** the system selects port-based routing for Nginx configuration

### Requirement: Nginx listens on external_port
The system SHALL generate a server block that listens on the external_port value with default_server enabled.

#### Scenario: listen uses external_port
- **WHEN** port-based routing is selected
- **THEN** the generated configuration includes listen <external_port> default_server

### Requirement: Nginx accepts all Host headers
The system SHALL set server_name to underscore to match all hosts for the port-based vhost.

#### Scenario: server_name wildcard
- **WHEN** port-based routing is selected
- **THEN** server_name is set to _

### Requirement: Static root maps to app name
The system SHALL set root to /usr/share/nginx/sites/<app_name> and index to index.html index.htm.

#### Scenario: static root configured
- **WHEN** port-based routing is selected
- **THEN** root and index are configured for static file serving

### Requirement: Port-based vhost uses static file fallback
The system SHALL configure location / to use try_files $uri $uri/ =404.

#### Scenario: static fallback
- **WHEN** port-based routing is selected
- **THEN** location / uses try_files $uri $uri/ =404

### Requirement: Out-of-range external_port is rejected
The system SHALL raise PortRangeError when external_port is outside 8400-8500 but port-based routing is requested.

#### Scenario: external_port out of range
- **WHEN** external_port is set outside 8400-8500
- **THEN** the system raises PortRangeError and does not generate a port-based vhost

### Requirement: Nginx reload is gated by syntax check
The system SHALL run nginx -t before reloading Nginx and SHALL abort reload when the syntax check fails.

#### Scenario: syntax check fails
- **WHEN** nginx -t reports a failure
- **THEN** the system does not reload Nginx and returns the failure error
