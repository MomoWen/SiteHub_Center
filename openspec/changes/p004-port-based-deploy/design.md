## Context

现有部署流程以 Host 路由为主，Nginx 容器通过 84xx 端口映射对外服务，导致 listen 端口与访问入口不一致时出现命中默认站点的问题。为满足“端口即入口”的运维习惯，需要端口驱动的 vhost 生成策略，并在部署前确保 external_port 不与其他站点冲突。

## Goals / Non-Goals

**Goals:**
- 以 external_port 驱动 vhost 生成，listen 端口与宿主机入口一致
- 通过正则解析 listen 指令，准确提取端口并规避注释或其他字段干扰
- 支持“更新同一应用”场景下的端口复用，不误判为冲突
- 端口冲突在写配置前被阻断，并给出明确的冲突来源

**Non-Goals:**
- 不在本次变更中引入域名路由策略回退
- 不实现 Nginx 多实例或跨主机的端口分配
- 不在此阶段改动现有部署脚本的发布/回滚机制

## Decisions

- **端口驱动条件**：当 sitehub.yaml 存在 external_port 且处于 8400-8500 范围内时启用端口驱动模式。选择范围约束是为了保持可预期的运维管理边界，并避免与现有端口策略冲突。
- **listen 端口解析**：使用正则 `r"listen\s+(?:[\d\.]+:|\[[a-fA-F\d:]+\]:)?(\d+)\b"` 从 server 块中提取端口。该正则避免误识别 proxy_pass 或注释中的端口，且兼容 IPv4/IPv6 写法与 listen 参数扩展（如 ssl）。
- **冲突判定的原子化保护**：扫描冲突时允许“同应用更新”覆盖。实现方式为：如果发现 external_port 被占用，但占用方配置文件名与当前 app_name 前缀一致（或 server 块 root 指向 /usr/share/nginx/sites/{app_name}），则视为同应用更新并允许继续写入。
- **扫描边界**：仅扫描 /etc/nginx/conf.d/ 下的 .conf 文件，避免解析主配置或 include 之外的路径，以保证性能和可控性。
- **端口驱动模板**：端口驱动的 vhost 使用 listen <external_port> default_server，确保该端口下命中默认 server。
- **重载前语法检查**：deploy_service 在 reload 前执行 nginx -t，失败时阻断重载并返回错误。

## Risks / Trade-offs

- 误判冲突来源 → 通过“配置文件名 + root 路径”双重判定降低风险
- 正则解析无法覆盖所有 listen 变体 → 保留解析失败的告警记录，并在失败时保守阻断冲突结论
- 多端口 server 块导致端口复用误判 → 逐端口解析并对每个端口进行冲突检查

## Migration Plan

- 先落地 external_port 字段解析与端口驱动 vhost 模板
- 增加端口扫描与冲突判定
- 灰度验证：部署一个指定 external_port 的应用并通过直连访问验证
- 如需回退，移除 external_port 字段即可恢复既有 Host 路由流程

## Open Questions

- “同应用更新”判定是否需要同时检查 server_name 或仅以 root/文件名为准
- 端口冲突扫描失败时是阻断还是降级为警告
