## Purpose

Define a safe, atomic workflow for updating Nginx configuration with validation and rollback.

## Requirements

### Requirement: Configuration updates create a backup before modification
Before modifying an Nginx configuration file, the update process SHALL create a backup of the current configuration.

#### Scenario: Backup is created
- **WHEN** an operator applies an Nginx configuration update
- **THEN** a backup copy of the prior configuration exists

### Requirement: Configuration updates are validated before reload
After writing the new configuration, the update process SHALL run `nginx -t` to validate the configuration before reloading.

#### Scenario: Validation succeeds
- **WHEN** the new configuration is syntactically valid
- **THEN** `nginx -t` succeeds and the process may proceed to reload

### Requirement: Failed validation triggers automatic rollback
If configuration validation fails, the update process SHALL restore the backup configuration and SHALL exit non-zero.

#### Scenario: Validation fails and rollback occurs
- **WHEN** `nginx -t` fails after an update
- **THEN** the prior configuration is restored and Nginx is not reloaded

### Requirement: Successful validation triggers reload
If configuration validation succeeds, the update process SHALL reload Nginx.

#### Scenario: Reload applies new configuration
- **WHEN** `nginx -t` succeeds
- **THEN** Nginx is reloaded and continues serving traffic

### Requirement: Update supports dry-run
The update process SHALL provide a dry-run mode that validates the generated configuration without changing the live configuration.

#### Scenario: Dry-run validates without applying
- **WHEN** an operator runs the update in dry-run mode
- **THEN** the live configuration is not changed and Nginx is not reloaded
