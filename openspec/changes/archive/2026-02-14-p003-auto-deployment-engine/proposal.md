## Why

当前 SiteHub_Center 仍缺乏从开发机（120）到宿主机（80）的端到端自动化部署能力，导致上线需要人工传输与手工调整 Nginx 配置，难以保证一致性与可追溯性。需要引入核心部署引擎，以绕过 Git、直接通过 SSH 同步源码并自动下发 Nginx 配置，形成可重复、可验证的部署链路。

## What Changes

- 增加基于 SSH 的源码同步引擎，优先使用 rsync（必要时回退到 scp），通过 SSH 隧道直接同步本地开发目录到宿主机站点目录，并默认排除 .venv、__pycache__、.DS_Store、.git 与本地 .env 文件 [cite: 2026-02-09] [cite: 2026-02-10]
- 同步前在宿主机侧检查目标目录是否存在，避免覆盖已有项目
- 同步完成后自动解析宿主机目标项目中的 sitehub.yaml，用于生成并推送 Nginx 虚拟主机配置；若缺少 sitehub.yaml，则停止 Nginx 更新并发出 Warning，但允许同步成功 [cite: 2026-02-14]
- 推送 Nginx 配置时提供权限兜底策略，优先尝试 sudo -n 非交互模式；若失败，提示用户在宿主机为 MomoWen 开放 Nginx 相关命令的免密权限 [cite: 2026-02-13]
- 复用 P002 锁定的 SSH 连接配置（MomoWen@10.8.8.80:1022，私钥认证），确保环境一致性

## Capabilities

### New Capabilities
- `ssh-code-sync`: 定义通过 SSH 隧道执行 rsync/scp 的源码同步流程、排除列表与目标目录安全检查
- `auto-deployment-engine`: 定义从同步完成到 sitehub.yaml 解析、Nginx 配置生成与下发、宿主机侧热重载的自动化链路

### Modified Capabilities
- `nginx-safe-config-update`: 增强配置下发的权限兜底与备份策略，覆盖 config_writable=false 的场景

## Impact

- 代码：新增 app/services/deploy_service.py 与相关服务逻辑；扩展现有 SSH 配置复用路径
- 配置：读取并解析宿主机侧 sitehub.yaml 以驱动 Nginx 配置生成
- 运维：Nginx 配置更新与热重载纳入自动化流程，需兼容 sudo/备份兜底策略
- 安全：部署前强制目录存在性校验，避免误覆盖生产站点
