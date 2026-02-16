## MODIFIED Requirements

### Requirement: Path is stored without hardcoded absolute roots
The system SHALL store `path` as a relative path segment and SHALL NOT hardcode any absolute filesystem roots in code. The effective absolute path SHALL be derived from environment variables, falling back to a default APP_ROOT_DIR when no environment override is provided.

#### Scenario: Resolving filesystem paths per environment
- **WHEN** the service runs in different environments (Ubuntu dev vs FnOS prod)
- **THEN** the effective absolute path is derived from environment variables or the default APP_ROOT_DIR rather than constants
