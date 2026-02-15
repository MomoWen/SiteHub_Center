## ADDED Requirements

### Requirement: External port allocations are recorded
The provisioning process SHALL record external_port when it is provided for a site.

#### Scenario: External port recorded
- **WHEN** an operator provisions a site with external_port
- **THEN** the site records the external_port value for later conflict checks

### Requirement: External port conflicts are rejected during provisioning
The provisioning process SHALL reject external_port values that are already recorded by another site.

#### Scenario: External port already used
- **WHEN** an operator provisions a site with an external_port already recorded by a different site
- **THEN** provisioning fails with a clear conflict error

### Requirement: SiteConfig defines external_port with range validation
The system SHALL define SiteConfig.external_port as int or None and SHALL validate that any provided value is within 8400-8500.

#### Scenario: external_port omitted
- **WHEN** external_port is not provided
- **THEN** SiteConfig.external_port is None and validation passes

#### Scenario: external_port out of range
- **WHEN** external_port is provided outside 8400-8500
- **THEN** validation fails with PortRangeError
