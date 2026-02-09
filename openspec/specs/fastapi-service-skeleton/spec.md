## Purpose

Define a minimal, runnable FastAPI service skeleton for SiteHub-based projects.

## Requirements

### Requirement: Template provides a runnable FastAPI application
The template SHALL provide a FastAPI application that can be started via an ASGI server.

#### Scenario: Starting the service
- **WHEN** an operator runs the documented start command
- **THEN** the service starts successfully and begins accepting HTTP requests

### Requirement: Service exposes a liveness health endpoint
The service SHALL expose an unauthenticated HTTP endpoint at `GET /healthz` that indicates the process is alive.

#### Scenario: Liveness check succeeds
- **WHEN** a client sends `GET /healthz`
- **THEN** the service responds with HTTP 200 and a JSON body

### Requirement: Service exposes a readiness endpoint
The service SHALL expose an unauthenticated HTTP endpoint at `GET /readyz` that indicates the service is ready to receive traffic.

#### Scenario: Readiness check succeeds
- **WHEN** the service has completed its startup initialization
- **THEN** a client sending `GET /readyz` receives HTTP 200

### Requirement: Configuration is controlled by environment variables
The service SHALL support configuration via environment variables, including at minimum `SITEHUB_ENV` and `PORT`.

#### Scenario: Running in different environments
- **WHEN** `SITEHUB_ENV` is set to `dev`
- **THEN** the service runs with development defaults

#### Scenario: Binding to a specified port
- **WHEN** `PORT` is set to a valid TCP port
- **THEN** the service binds to that port

### Requirement: Errors are returned as JSON responses
The service SHALL return JSON error responses for request validation errors and unhandled server errors.

#### Scenario: Request validation error
- **WHEN** a client sends a request that fails validation
- **THEN** the service responds with HTTP 4xx and a JSON body describing the error

#### Scenario: Unhandled server error
- **WHEN** an unhandled exception occurs during request handling
- **THEN** the service responds with HTTP 5xx and a JSON body

### Requirement: Logs do not expose secrets
The service SHALL NOT log secret values, including tokens, passwords, and private keys.

#### Scenario: Logging during startup
- **WHEN** the service starts and logs its configuration summary
- **THEN** no secret values appear in logs
