---
name: "sitehub-provisioner"
description: "初始化 SiteHub 环境：在 /vol1/1000/MyDocker/web-cluster/sites/ 下创建隔离结构、生成 .venv，并分配 8085-8095 端口。调用于创建新站点或确保目录与端口规范化。"
---

# SiteHub-Provisioner（基础环境构建）

目标
- 初始化全新 SiteHub 应用环境，统一项目目录结构与端口分配，避免路径与端口漂移

触发时机
- 需要在 /vol1/1000/MyDocker/web-cluster/sites/ 下创建新项目
- 需要确保目录结构 100% 对齐、端口分配在 8085-8095 之间且不冲突

输入参数
- project_name：站点名称（必填，字母/数字/短横线）
- target_root：默认 /vol1/1000/MyDocker/web-cluster/sites/
- port_range：默认 8085-8095
- SITEHUB_ENV：dev 或 prod
- CACHE_SERVER：可选，如果启用则 pip 使用该缓存源
- nginx_bin：可选，默认 /usr/sbin/nginx
- nginx_conf_root：可选，默认 /etc/nginx/conf.d/
- nginx_backup_root：可选，默认 /etc/nginx/backups/

前置约束
- 遵循 OpenSpec：先生成 proposal 与 tasks，validate 通过后才执行 Apply
- 禁用国内镜像源；优先 10.8.8.80 缓存
- 路径统一使用 Unix 风格，保证 Ubuntu/FnOS 可迁移

执行步骤
1) 计划与校验
- 在 openspec/changes/{id}/ 生成 proposal.md，包含用户故事、验收标准、安全/性能影响
- 在 specs/ 生成 Deltas，运行 openspec validate

2) 目录结构
- 创建 {target_root}/{project_name}/
- 子目录：src/、scripts/、openspec/、.trae/
- 在 scripts/ 放置 deploy.sh（实现 releases/ 时间戳目录 + current 软链的原子替换逻辑占位）

3) 虚拟环境
- 在项目根创建 .venv：python3 -m venv .venv
- 约定依赖安装遵守 CACHE_SERVER（存在时 pip 追加 --index-url http://10.8.8.80:3141/...）

4) 端口分配
- 扫描 target_root 下各项目的 sitehub.yaml，收集已占用端口
- 在 port_range 中选择首个未占用端口
- 写入 {project_root}/sitehub.yaml，记录：
  - port: <allocated>
  - rollback: <releases/ 与 current 的路径策略>

5) 初始化校验
- 运行 .venv/bin/flake8 src/（如 src/ 尚为空，可跳过或放置占位文件）
- 运行 openspec validate
- 运行 .venv/bin/pytest（如无测试，提示补充后再执行）
- Dry-run 部署：bash scripts/deploy.sh --dry-run

6) 环境自愈（Nginx 配置）
- 预检：执行 `${nginx_bin} -t`
- 失败处理：自动恢复最近一次备份 `${nginx_backup_root}/{latest}/{conf_name}` 至 `${nginx_conf_root}/{conf_name}`，并执行 `${nginx_bin} -s reload`
- 记录：在 `sitehub.log` 写入 `[HEAL] Nginx rollback applied`，并建议触发 Nginx-Hotfix-Master 进行完整回滚审计

幂等与冲突处理
- 项目目录已存在：不重复创建；端口冲突则选择下一个可用端口
- 端口段不足（8085-8095 全占用）：返回错误并提示调整范围

输出
- 规范化的项目目录、可用的 .venv、分配的端口、初始化的 sitehub.yaml 与 deploy.sh

示例
- 初始化：SiteHub-Provisioner(project_name="blog", SITEHUB_ENV="dev")
- 结果：/vol1/1000/MyDocker/web-cluster/sites/blog 完成初始化，端口 8085（或下一个可用）

架构价值
- 所有新项目结构 100% 对齐，端口集中管理，避免 Trae 即兴发挥导致的路径与端口混乱
- 引入环境自愈机制，降低因 Nginx 配置错误导致的不可用风险，保障模板初始化可达与可维护
