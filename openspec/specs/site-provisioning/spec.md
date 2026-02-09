## Purpose

Define site provisioning for a multi-site environment, including port allocation and optional virtualenv setup.

## Requirements

### Requirement: Site provisioning creates an isolated site directory
The provisioning process SHALL create an isolated site directory under `/vol1/1000/MyDocker/web-cluster/sites/<site>/`.

#### Scenario: Creating a new site directory
- **WHEN** an operator provisions a site with name `<site>`
- **THEN** `/vol1/1000/MyDocker/web-cluster/sites/<site>/` exists and is owned by the site

### Requirement: Site provisioning is idempotent
Provisioning the same site multiple times SHALL NOT corrupt existing state and SHALL result in the same intended structure.

#### Scenario: Re-running provisioning
- **WHEN** an operator provisions an already-provisioned `<site>`
- **THEN** provisioning completes successfully without duplicating or deleting unrelated data

### Requirement: Site provisioning assigns an application port within the allowed range
The provisioning process SHALL allocate an application port within 8085-8095, unless an explicit port is provided.

#### Scenario: Explicit port is respected
- **WHEN** an operator provisions a site with an explicit port in the allowed range
- **THEN** the site is configured to use that port

#### Scenario: Automatic port allocation succeeds
- **WHEN** an operator provisions a site without specifying a port
- **THEN** an unused port in 8085-8095 is selected and recorded for the site

### Requirement: Port conflicts are detected and reported
The provisioning process SHALL detect port conflicts and SHALL fail with a clear error message if no allowed ports are available.

#### Scenario: No ports available
- **WHEN** all ports 8085-8095 are already in use
- **THEN** provisioning exits non-zero and reports the conflict

### Requirement: Provisioning can initialize a Python virtual environment
The provisioning process SHALL support creating a Python virtual environment for the site.

#### Scenario: Creating a virtual environment
- **WHEN** an operator requests virtual environment initialization
- **THEN** the site contains a ready-to-use virtual environment directory
