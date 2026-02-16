## ADDED Requirements

### Requirement: Sync prefers rsync over SSH with fallback to scp
The system SHALL attempt to synchronize a local source directory to a remote target directory using rsync over SSH and SHALL fallback to scp when rsync is unavailable or fails to execute.

#### Scenario: rsync succeeds
- **WHEN** rsync is available on both ends
- **THEN** the system completes synchronization using rsync over SSH

#### Scenario: rsync unavailable
- **WHEN** rsync is not available on the remote host
- **THEN** the system falls back to scp to transfer the directory recursively

### Requirement: Sync enforces a default exclude list
The system SHALL exclude .venv, __pycache__, .DS_Store, .git, and .env from synchronization unless explicitly overridden.

#### Scenario: Exclude list applied
- **WHEN** a synchronization starts
- **THEN** the excluded paths are not transferred to the remote target

### Requirement: Sync applies rsync chmod policy
The system SHALL invoke rsync with --chmod=Du=rwx,Dg=rx,Do=rx,Fu=rw,Fg=r,Fo=r to enforce D755/F644 permissions.

#### Scenario: rsync chmod applied
- **WHEN** rsync synchronization begins
- **THEN** the rsync command includes the --chmod policy for directories and files

### Requirement: Remote target directory must not already exist
The system SHALL check for the existence of the remote target directory before synchronization and SHALL abort if the directory exists.

#### Scenario: Target directory exists
- **WHEN** the remote target directory already exists
- **THEN** the system aborts synchronization with a clear error

### Requirement: SSH configuration is applied consistently
The system SHALL use the configured SSH host, user, port, and private key when establishing the synchronization connection.

#### Scenario: SSH parameters applied
- **WHEN** synchronization begins
- **THEN** the SSH connection uses the configured host, user, port, and private key

### Requirement: Sync fixes permissions after transfer
The system SHALL apply chmod -R 755 to the remote target directory and SHALL ensure ownership is set to the configured SSH user.

#### Scenario: Permissions are corrected
- **WHEN** synchronization completes successfully
- **THEN** the remote target directory has 755 permissions and ownership matches the SSH user

### Requirement: Permission fixes are logged
The system SHALL emit a log entry when permission fixes begin and when they succeed or fail.

#### Scenario: Permission fix logging
- **WHEN** the system attempts to fix remote permissions
- **THEN** a log entry is recorded for begin and final status
