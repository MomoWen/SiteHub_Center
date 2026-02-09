## ADDED Requirements

### Requirement: Deployments use immutable release directories
The deployment process SHALL create a new immutable directory at `releases/<timestamp>` for each deployment.

#### Scenario: Creating a new release
- **WHEN** a deployment is executed
- **THEN** a new `releases/<timestamp>` directory is created and contains the deployed application

### Requirement: Active version is selected by an atomic current symlink
The deployment process SHALL select the active version by updating a `current` symlink to a target release directory.

#### Scenario: Switching active release
- **WHEN** a deployment completes successfully
- **THEN** the `current` symlink points to the new release directory

### Requirement: Deployment provides a dry-run mode
The deployment process SHALL provide a dry-run mode that performs validation and prints planned actions without modifying the filesystem.

#### Scenario: Dry-run does not modify state
- **WHEN** a deployment is executed in dry-run mode
- **THEN** no `releases/<timestamp>` directory is created and `current` is not changed

### Requirement: Rollback switches current to a previous release
The deployment process SHALL support rollback by switching `current` to a specified prior release.

#### Scenario: Rolling back to a known good release
- **WHEN** an operator triggers rollback to an existing release directory
- **THEN** the `current` symlink points to that release directory

### Requirement: Deployment validates prerequisites before switching traffic
The deployment process SHALL validate prerequisites before changing `current`, including required paths and executable entrypoints.

#### Scenario: Validation failure aborts deployment
- **WHEN** a prerequisite check fails
- **THEN** the deployment exits non-zero and `current` remains unchanged

### Requirement: Deployment records actions to a log
The deployment process SHALL append a human-readable record of actions and outcomes to `sitehub.log`.

#### Scenario: Logging a successful deployment
- **WHEN** a deployment completes successfully
- **THEN** `sitehub.log` contains an entry with timestamp, strategy, and release identifier
