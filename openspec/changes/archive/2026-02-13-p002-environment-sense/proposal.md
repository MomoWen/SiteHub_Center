## Why

当前管理端无法明确感知 FnOS 宿主机关键路径与 Nginx 配置的可访问性，导致在环境权限不足或路径不可达时只能被动失败，缺少清晰的健康反馈与可操作指引。需要引入环境探测与健康报告能力，确保上线前对宿主机路径、读写权限与 Nginx 配置可操作性有可验证的结论。

## What Changes

- 新增环境探测能力，验证管理端对 `/vol1/1000/` 与 `/vol1/1000/MyDocker/web-cluster/sites` 的可访问性与读写权限，并采用异步探测避免阻塞
- 新增 `GET /env/health` 端点，输出包含磁盘空间、目录读写状态、Nginx 可用性、失败原因与连接延迟的健康报告
- 增加对 Nginx 配置目录与二进制路径的可用性检测，并在尝试修改前自动备份 `nginx.conf`（时间戳命名且仅保留最近 5 个版本）
- 调整 `sitehub.yaml` 解析逻辑，支持从环境动态注入宿主机 APP_ROOT_DIR，并提供合理的默认值

## Capabilities

### New Capabilities
- `environment-sense`: 定义宿主机路径、读写权限与 Nginx 可用性的探测与健康报告行为

### Modified Capabilities
- `app-registry`: `sitehub.yaml` 解析与路径解析支持动态 APP_ROOT_DIR 注入

## Impact

- 代码与接口：新增环境探测服务、增加 `GET /env/health` 健康报告端点，写权限探测需确保探针文件在 finally 中清理
- 配置与路径：`sitehub.yaml` 解析使用动态 APP_ROOT_DIR，保留开发环境默认值，路径探测支持 FnOS 宿主机目录
- 运维安全：Nginx 配置操作前提供自动备份并控制版本数量；错误处理需明确区分不可达与权限不足；连接延迟超过阈值时标记 Warning
- 依赖与安全：禁止硬编码 root 密码，优先使用现有 SSH Key 或 MCP 授权链路
