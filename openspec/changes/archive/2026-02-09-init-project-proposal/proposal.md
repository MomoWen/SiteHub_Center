## Why

当前母版仓库仅具备 OpenSpec 框架与少量运维脚本，但缺少“可迁移、可部署、可回滚、可验证”的基线契约与最小可运行实现，导致后续每个站点/项目在环境初始化、依赖安装、发布与回滚、Nginx 接入、服务健康检查等关键环节都需要重复决策与反复踩坑。需要通过一次初始化变更，把这些基线能力固化为规格（specs）与默认实现，从而让母版仓库可以稳定产出可上线的站点骨架。

## What Changes

- 增加最小可运行的 Python/FastAPI 服务骨架（包含健康检查与基础配置加载），作为所有站点的默认应用入口
- 增加标准化的发布目录结构与原子切换流程（`releases/<timestamp>` + `current` 软链），并提供回滚路径与 dry-run
- 增加站点目录与端口的初始化/校验能力，符合 `/vol1/1000/MyDocker/web-cluster/sites/` 的模拟生产结构与 8085-8095 端口约束
- 固化依赖安装的网络策略（优先缓存服务器，否则走代理到官方源；禁止国内镜像），并将其纳入规格与验收
- 固化 Nginx 配置更新的原子化流程（备份、`nginx -t` 预检、失败回滚），保证线上稳定性

## Capabilities

### New Capabilities

- `fastapi-service-skeleton`: 提供最小可运行的 FastAPI 应用入口、健康检查端点、基础配置加载与启动方式约定
- `release-deploy-and-rollback`: 定义发布目录结构、原子切换、回滚路径与 dry-run 的行为契约
- `site-provisioning`: 定义站点目录结构、`.venv` 初始化与 8085-8095 端口分配/占用检查的行为契约
- `dependency-installation-policy`: 定义依赖安装时的网络与源策略（缓存/代理/官方源优先级、禁止国内镜像、必要环境变量）
- `nginx-safe-config-update`: 定义 Nginx 配置生成/替换时的备份、预检与失败自动回滚流程

### Modified Capabilities

(none)

## Impact

- 代码与目录：引入 `src/`（应用骨架）、`scripts/deploy.sh`（发布/回滚）、以及站点初始化相关脚本/配置（如 `sitehub.yaml`）
- 运维与部署：约束发布流程必须支持原子切换与可回滚；Nginx 配置变更必须可预检并自动回滚
- 依赖与网络：依赖安装需遵循缓存服务器/代理策略与“仅官方源”约束；相关行为纳入规格与验收
