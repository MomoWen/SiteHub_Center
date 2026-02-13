## Purpose

Define a persistent, queryable application registry backed by PocketBase, with a FastAPI management entrypoint.

## Requirements

### Requirement: PocketBase stores application registry records
The system SHALL use PocketBase as the metadata store and SHALL persist application registry records in a collection named `apps`.

#### Scenario: Creating an app record in PocketBase
- **WHEN** the service registers an application
- **THEN** a record is created in the PocketBase `apps` collection with the declared metadata fields

### Requirement: App name is a unique identifier
The system SHALL treat `name` as the unique application identifier.

#### Scenario: Duplicate app name is rejected
- **WHEN** a client registers an app with an existing `name`
- **THEN** the registration fails with an error response

### Requirement: Port is validated and unique
The system SHALL validate `port` is within `8081-8090` and SHALL prevent duplicate port assignments.

#### Scenario: Port outside allowed range is rejected
- **WHEN** a client registers an app with `port` outside `8081-8090`
- **THEN** the service responds with HTTP 4xx

#### Scenario: Duplicate port is rejected
- **WHEN** a client registers an app with a `port` already assigned
- **THEN** the registration fails with an error response

### Requirement: Path is stored without hardcoded absolute roots
The system SHALL store `path` as a relative path segment and SHALL NOT hardcode any absolute filesystem roots in code.

#### Scenario: Resolving filesystem paths per environment
- **WHEN** the service runs in different environments (Ubuntu dev vs FnOS prod)
- **THEN** the effective absolute path is derived from environment variables rather than constants

### Requirement: Register endpoint creates an app record
The service SHALL expose `POST /apps/register` to create an application registry record.

#### Scenario: Successful registration
- **WHEN** a client submits a valid registration payload
- **THEN** the service responds with HTTP 201 and the created record data

### Requirement: Register endpoint parses sitehub.yaml when available
The service SHALL attempt to parse the target application's `sitehub.yaml` during registration and SHALL store the parsed data into `sitehub_config` when available.

#### Scenario: One-click registration from filesystem
- **WHEN** a client registers an app with a valid `path` and the corresponding `sitehub.yaml` exists under the configured app root directory
- **THEN** the created registry record contains a `sitehub_config` JSON snapshot derived from `sitehub.yaml`

### Requirement: Database init script selects PocketBase by environment
The system SHALL provide an `init_db.py` script that selects the PocketBase instance based on environment variables.

#### Scenario: Environment-specific PocketBase selection
- **WHEN** `SITEHUB_ENV` is set to `dev` or `prod`
- **THEN** the init script targets the environment-specific PocketBase URL if provided, otherwise falls back to the default URL
