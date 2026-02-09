## Purpose

Define dependency installation source policy, network fallback strategy, and forbidden mirrors.

## Requirements

### Requirement: Dependency installation uses official upstream sources
Dependency installation SHALL use official upstream package sources (for example, PyPI for pip and registry.npmjs.org for npm).

#### Scenario: Installing Python dependencies
- **WHEN** dependencies are installed via pip
- **THEN** the index source is the official upstream source unless a cache server is explicitly used

### Requirement: Domestic mirrors are forbidden
The project SHALL NOT reference domestic mirrors, including `mirrors.aliyun.com` and `tsinghua.edu.cn`, in dependency configuration.

#### Scenario: Forbidden mirror is detected
- **WHEN** dependency configuration contains a forbidden mirror domain
- **THEN** installation fails with a clear error

### Requirement: Cache server is preferred when available
When `CACHE_SERVER` is configured and reachable, dependency installation SHALL prefer the cache server.

#### Scenario: Cache server is used
- **WHEN** `CACHE_SERVER` is set and reachable
- **THEN** installation uses the cache server as the package source

### Requirement: Proxy fallback is used when cache is unavailable
When the cache server is unavailable, dependency installation SHALL fall back to proxy-based access to official sources.

#### Scenario: Proxy fallback succeeds
- **WHEN** `CACHE_SERVER` is unreachable and `PROXY_GATEWAY` is reachable
- **THEN** installation proceeds using the proxy to access official sources

### Requirement: Network strategy is recorded
Dependency installation SHALL record whether it used cache or proxy strategy to `sitehub.log`.

#### Scenario: Logging installation strategy
- **WHEN** an installation begins
- **THEN** `sitehub.log` contains an entry indicating CACHE or PROXY strategy
