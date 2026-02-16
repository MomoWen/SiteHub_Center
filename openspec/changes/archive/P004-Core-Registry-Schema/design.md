关联 specs 模块：
- specs/app-registry

## Context

SiteHub_Center 需要一个可查询、可约束、可演进的“应用注册表”作为元数据底座，用于统一管理应用的端口、部署路径、状态与配置快照。为保证在 Ubuntu 开发环境与 FnOS 生产环境（宿主机路径位于 `/vol1/1000/`）之间可迁移，注册表中不应存储任何绝对路径。

本变更采用 PocketBase 作为元数据库，FastAPI 作为管理端入口，通过 HTTP API 以异步方式写入 `apps` collection，并在注册过程中自动解析目标应用 `sitehub.yaml` 形成 `sitehub_config` 快照，从而实现“一键注册”。

## Goals / Non-Goals

**Goals:**

- 提供可运行的 PocketBase 存储结构：`apps` collection 及其字段约束（唯一性、枚举等）
- 在 FastAPI 中实现 `POST /apps/register`，异步写入 PocketBase
- 在注册时自动解析目标应用的 `sitehub.yaml` 并写入 `sitehub_config`
- 通过环境变量完成 Ubuntu/FnOS 的路径映射与 PocketBase 实例选择，不在代码中硬编码 `/vol1/1000/`
- 提供一个可复用的初始化脚本入口（连通性检查/可选 schema 初始化）

**Non-Goals:**

- 不实现完整的 CRUD（查询/更新/删除/列表）与权限控制
- 不在本变更中定义 PocketBase 生产部署、备份与迁移策略
- 不在本变更中实现端口自动分配算法（仅做范围校验与唯一性约束）

## Decisions

### 1) PocketBase 作为元数据库，collection 以 `apps` 为核心

选择：使用 PocketBase 作为元数据库，并将应用记录统一存储于 `apps` collection。

理由：

- PocketBase 自带 schema、唯一性约束、JSON 字段与管理 UI，适合“元数据注册表”场景
- 通过 HTTP API 接入成本低，便于 FastAPI 管理端统一封装与演进

备选：

- SQLite/PG 自建表与迁移：需要额外迁移框架与运维复杂度
- 仅文件型注册（YAML/JSON）：缺乏可查询性与一致约束

### 2) FastAPI 与 PocketBase 的交互采用 httpx.AsyncClient

选择：管理端使用 `httpx.AsyncClient` 进行异步 HTTP 调用，封装为 `PocketBaseClient`，FastAPI 端点通过依赖注入获取客户端实例。

理由：

- 与 FastAPI 的异步模型一致，避免阻塞请求线程
- 便于统一处理鉴权（Bearer token）与错误映射
- 客户端封装可以保持 API 层简洁，未来扩展为更多 registry 操作

交互约定：

- 创建记录：`POST /api/collections/apps/records`
- 鉴权优先级：`POCKETBASE_TOKEN` > `POCKETBASE_ADMIN_EMAIL/POCKETBASE_ADMIN_PASSWORD` 换取 token
- 失败处理：PocketBase 4xx/5xx 统一映射为 FastAPI HTTP 502，并携带 PocketBase 原始响应用于定位

### 3) “一键注册”以 sitehub.yaml 快照为基础

选择：在 `POST /apps/register` 中，当请求体未提供 `sitehub_config` 时，尝试从目标应用目录读取 `sitehub.yaml` 并解析为 dict，写入 `sitehub_config`。

理由：

- `sitehub.yaml` 是站点/应用配置的单一事实来源之一，自动解析可降低注册操作成本
- 存储快照利于后续做配置漂移对比、审计与回滚辅助

备选：

- 仅要求调用方上传 `sitehub_config`：会降低“一键注册”的可用性
- 注册时直接写入 PocketBase 文件字段：会增加存储与同步复杂度

### 4) 路径映射通过 APP_ROOT_DIR（或按环境区分）实现

选择：PocketBase `apps.path` 存储相对路径段（例如 `apps/MyBookmark`），运行时通过环境变量提供的根目录拼接出物理路径。

理由：

- 避免将 `/vol1/1000/...` 之类宿主机绝对路径写入元数据库，确保在不同环境可迁移
- 允许同一套 registry 数据在 dev/prod 环境复用

具体策略：

- 优先使用 `APP_ROOT_DIR`
- 若未提供，则按 `SITEHUB_ENV` 选择 `SITEHUB_APPS_ROOT_DEV` / `SITEHUB_APPS_ROOT_PROD`

### 5) init_db.py 作为初始化与连通性检查入口

选择：提供 `scripts/init_db.py`：

- 按 `SITEHUB_ENV` 选择 `POCKETBASE_URL_DEV/POCKETBASE_URL_PROD`，否则回退 `POCKETBASE_URL`
- 通过 `GET /api/health` 进行连通性检查
- 在显式启用开关时，通过管理员 token/凭据确保 `apps` collection schema 存在

理由：

- 形成可自动化执行的初始化入口，便于开发与部署流程统一
- 将 PocketBase 选择逻辑从业务端点抽离，降低耦合

## Risks / Trade-offs

- [PocketBase 鉴权 token 获取失败导致注册不可用] → 提供 `POCKETBASE_TOKEN` 与管理员凭据两套方式，并在错误响应中携带 PocketBase 原始信息便于定位
- [sitehub.yaml 内容不受控导致解析失败] → 解析使用安全模式并对非 mapping 类型做 422；允许调用方显式传入 `sitehub_config` 覆盖
- [APP_ROOT_DIR 未配置导致无法一键解析] → 端点退化为仅写入请求体信息；后续可在任务中强化为“未配置则明确提示”
- [网络不稳定导致元数据库写入失败] → 将错误明确映射为 502，并保留重试空间；未来可补充幂等 key 或队列化写入
