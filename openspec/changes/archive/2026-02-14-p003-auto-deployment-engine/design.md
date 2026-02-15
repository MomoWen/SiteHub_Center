## Context

需要在 SiteHub_Center 中建立从开发机（120）到宿主机（80）的自动化部署引擎，绕过 Git，使用 SSH 进行源码同步，并在同步完成后根据 sitehub.yaml 自动下发 Nginx 配置与热重载。当前已有 SSH 连接配置与环境探测能力，以及 Nginx 安全更新脚本，但缺少部署服务层的编排与对 rsync/scp 的封装。

## Goals / Non-Goals

**Goals:**
- 提供 SyncEngine 封装 rsync/scp 的同步流程与默认排除列表
- 实现同步后站点配置解析与 Nginx 配置生成、推送与热重载
- 复用 P002 锁定的 SSH 参数与私钥认证
- 在 Nginx 配置写入时支持 sudo -n 权限兜底与失败备份逻辑

**Non-Goals:**
- 不引入新的部署编排框架或外部依赖
- 不覆盖或改动现有 releases/current 的发布回滚流程
- 不实现多节点或并行部署策略

## Decisions

- 采用 SyncEngine 封装 rsync 为主、scp 为备的传输策略，确保在 rsync 不可用时仍可完成同步
- 默认排除 .venv、__pycache__、.DS_Store、.git 与本地 .env 文件，避免同步开发环境产物与敏感配置
- 同步前在宿主机侧进行目录存在性校验，阻止对已有项目的覆盖
- 同步完成后在宿主机读取 sitehub.yaml，若缺失则停止 Nginx 更新并返回 Warning，确保“配置跟随源码”
- 复用现有 SSH 连接配置，使用私钥认证与固定端口，保证与 P002 验证结果一致
- Nginx 配置推送通过远程执行安全更新脚本完成，优先 sudo -n 非交互模式；失败时触发备份流程并提示免密配置建议

## Risks / Trade-offs

- rsync 不可用时回退 scp 会牺牲增量同步效率 → 提供明确日志与后续可观测性
- 站点缺少 sitehub.yaml 会导致 Nginx 配置不更新 → 以 Warning 形式输出并允许同步成功
- sudo -n 在默认权限下可能失败 → 提示用户配置免密 sudo 权限
