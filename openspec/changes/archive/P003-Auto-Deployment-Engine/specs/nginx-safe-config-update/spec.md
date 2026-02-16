## ADDED Requirements

### Requirement: Update attempts non-interactive sudo when requested
When the update is configured with use_sudo enabled, the system SHALL attempt sudo -n for backup and configuration writes.

#### Scenario: sudo -n succeeds
- **WHEN** use_sudo is enabled and sudo -n is permitted
- **THEN** the update uses sudo -n to perform backup and write operations

#### Scenario: sudo -n fails
- **WHEN** use_sudo is enabled and sudo -n is not permitted
- **THEN** the update fails with an error that instructs enabling passwordless sudo for Nginx-related commands
