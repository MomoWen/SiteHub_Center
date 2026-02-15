## Purpose

Define the deployment engine flow from code sync to Nginx configuration and reload.

## Requirements

### Requirement: Engine parses sitehub.yaml after sync
The system SHALL locate and parse sitehub.yaml from the synchronized remote project root to drive deployment configuration.

#### Scenario: sitehub.yaml present
- **WHEN** sitehub.yaml exists in the remote project root
- **THEN** the system parses it and proceeds to generate Nginx configuration

### Requirement: Missing sitehub.yaml skips Nginx updates
If sitehub.yaml is missing or invalid, the system SHALL skip Nginx configuration updates and SHALL emit a warning while still reporting the synchronization as successful.

#### Scenario: sitehub.yaml missing
- **WHEN** sitehub.yaml is not found in the remote project root
- **THEN** the system returns a warning and does not attempt Nginx updates

### Requirement: Engine generates Nginx server configuration
The system SHALL generate an Nginx server configuration that proxies HTTP traffic to the application port declared in sitehub.yaml.

#### Scenario: Nginx config generation
- **WHEN** a valid sitehub.yaml is parsed
- **THEN** the generated configuration includes a server block that listens on port 80 and proxies to 127.0.0.1:<port>

### Requirement: Engine writes Nginx config to FnOS path
The system SHALL write the generated Nginx configuration to /vol1/1000/MyDocker/nginx/conf.d/<app>.conf.

#### Scenario: Nginx config written
- **WHEN** a generated configuration is applied
- **THEN** the file is written under /vol1/1000/MyDocker/nginx/conf.d

### Requirement: Engine supports Nginx config preview
The system SHALL provide a preview mode that renders the generated Nginx configuration without applying it.

#### Scenario: Preview only
- **WHEN** preview mode is requested
- **THEN** the system returns the generated Nginx configuration without modifying the live configuration

### Requirement: Nginx reload uses docker exec
The system SHALL reload Nginx by running docker exec sitehub-nginx nginx -s reload.

#### Scenario: Nginx reload succeeds
- **WHEN** the configuration is updated
- **THEN** the system executes docker exec sitehub-nginx nginx -s reload successfully
