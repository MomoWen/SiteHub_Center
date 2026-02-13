## Why

SiteHub_Center 管理端缺少“应用注册表”这一统一的结构化元数据底座，导致应用的端口分配、部署路径、状态与配置快照难以被一致管理与查询。引入可查询、可约束（唯一性）、可演进的元数据库后，才能在此基础上逐步构建部署编排、状态观测与运维自动化能力。

## What Changes

- 新增 PocketBase 作为元数据库，建立 `apps` Collection 存储应用元数据，并提供本地开发可启动的 PocketBase 运行方式（docker-compose）。
- 在 FastAPI 管理端新增应用注册的基础 CRUD 起点：实现 `POST /apps/register`，自动解析目标应用的 `sitehub.yaml` 并将应用元数据写入 PocketBase。
- 增加数据库初始化脚本 `scripts/init_db.py`：根据 `SITEHUB_ENV` 自动选择并连接对应 PocketBase 实例，完成连通性检查与初始化动作的统一入口。
- 引入应用路径字段的环境映射策略：不在代码中硬编码任何绝对路径，使用 `APP_ROOT_DIR`（或按环境区分的根路径变量）在 Ubuntu 开发机与 FnOS `/vol1/1000/` 宿主机之间做逻辑映射；PocketBase 中仅存相对路径段。

## Technical Details

### Data Model (PocketBase `apps` collection)

`apps` Collection 作为“应用注册表”的权威数据源，记录字段与约束如下（与 PocketBase schema 对齐）：

- `name` (Text, Unique)：应用唯一标识符（如 `MyBookmark`）
- `port` (Number, Unique)：分配端口（`8081-8090`）
- `path` (Text)：相对路径段（例如 `apps/MyBookmark`），不允许绝对路径；实际物理路径由环境变量根目录 + `path` 拼接得到
- `git_repo` (Text)：源代码仓库地址（可选）
- `status` (Select)：`running | stopped | deploying | error`
- `sitehub_config` (JSON)：注册时从目标应用的 `sitehub.yaml` 解析得到的快照（可选）

### FastAPI ↔ PocketBase Async Interaction

管理端以 FastAPI 为入口，以 `httpx.AsyncClient` 与 PocketBase HTTP API 进行异步交互：

- **请求建模与校验**：`POST /apps/register` 使用 Pydantic 模型对 `name/port/path/status` 等字段进行输入校验，其中 `path` 强制为相对路径段（拒绝以 `/` 开头与包含 `..`）。
- **sitehub.yaml 自动解析**：当请求体未显式提供 `sitehub_config` 且配置了 `APP_ROOT_DIR`（或按环境区分的 root），服务端根据 `APP_ROOT_DIR + path + /sitehub.yaml` 定位文件，并使用安全模式解析为 dict；解析结果写入 `sitehub_config` 后再执行入库。
- **PocketBase 写入**：服务端将校验后的 payload 以 JSON 形式调用 `POST /api/collections/apps/records` 创建记录，并将 PocketBase 返回的 record 映射为响应模型返回给调用方。
- **鉴权策略**：优先使用 `POCKETBASE_TOKEN`（Bearer token）；如未提供，则在配置了 `POCKETBASE_ADMIN_EMAIL/POCKETBASE_ADMIN_PASSWORD` 时通过 `/api/admins/auth-with-password` 进行一次性登录换取 token 后再请求。
- **错误处理**：PocketBase 返回 4xx/5xx 时，服务端以网关错误形式返回（HTTP 502），并携带 PocketBase 原始响应文本以便定位。

### Database Initialization (init_db.py)

提供 `scripts/init_db.py` 作为初始化/连通性检查入口：

- **按环境选择实例**：脚本读取 `SITEHUB_ENV`，在 `prod` 时优先使用 `POCKETBASE_URL_PROD`，在 `dev` 时优先使用 `POCKETBASE_URL_DEV`，否则回退到 `POCKETBASE_URL`。
- **健康检查**：对目标 PocketBase 发起 `GET /api/health`，用于快速判断实例可用性。
- **Schema 初始化（可选）**：当显式启用初始化开关时，使用 token/管理员凭据确保 `apps` collection schema 存在并包含约定字段。

### Path Mapping (Ubuntu dev ↔ FnOS prod)

`path` 字段仅存相对路径段，严禁将 `/vol1/1000/...` 之类绝对宿主机路径写入记录或硬编码进代码。运行时通过以下变量完成映射：

- `APP_ROOT_DIR`：当前环境应用根目录（优先）
- 或按环境区分：`SITEHUB_APPS_ROOT_DEV` / `SITEHUB_APPS_ROOT_PROD`

## Capabilities

### New Capabilities

- `app-registry`: 应用元数据的结构化存储（PocketBase `apps` Collection）与基础注册接口（FastAPI `POST /apps/register`），包含字段约束、端口范围校验与路径映射策略。

### Modified Capabilities

## Impact

- 新增运行依赖：PocketBase（通过 docker-compose 本地启动，生产环境部署方式由后续变更定义）。
- 后端代码新增：Pydantic 模型（`src/sitehub/models/`）、API 路由（`src/sitehub/api/v1/apps.py`）、PocketBase 客户端封装与初始化脚本（`scripts/init_db.py`）。
- 新增配置项（环境变量）：`POCKETBASE_URL`（可按环境区分）、`POCKETBASE_TOKEN` 或 `POCKETBASE_ADMIN_EMAIL/POCKETBASE_ADMIN_PASSWORD`，以及 `APP_ROOT_DIR`（或 `SITEHUB_APPS_ROOT_DEV/PROD`）。
- 新增 Python 依赖：用于解析 `sitehub.yaml` 的 YAML 解析库（母版仓库仅用于该用途）。
- 依赖安装流程需遵循网络规约：依赖安装前使用仓库提供的网络策略脚本（`bash scripts/dependency-check.sh pip ...`）确保仅使用官方源并优先海外缓存/代理。
