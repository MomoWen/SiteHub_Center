## 1. 服务骨架（FastAPI）

- [x] 1.1 创建 `src/` 目录与 FastAPI 应用入口文件
- [x] 1.2 实现 `GET /healthz` 与 `GET /readyz` 端点
- [x] 1.3 增加基于环境变量的配置加载（至少 `SITEHUB_ENV`、`PORT`）
- [x] 1.4 统一 JSON 错误响应（校验错误与未处理异常）
- [x] 1.5 增加启动命令与进程运行方式（ASGI server）到脚本或配置

## 2. 发布与回滚（releases/current）

- [x] 2.1 新增 `scripts/deploy.sh` 并实现 `--dry-run`
- [x] 2.2 实现 `releases/<timestamp>` 构建与 `current` 软链原子切换
- [x] 2.3 实现回滚到指定 release 的能力
- [x] 2.4 增加部署前置校验（路径、入口可执行、关键文件存在）
- [x] 2.5 将部署动作与结果追加写入 `sitehub.log`

## 3. 站点初始化与端口管理

- [x] 3.1 新增站点初始化脚本并创建模拟生产目录结构（`/vol1/1000/MyDocker/web-cluster/sites/<site>/`）
- [x] 3.2 实现 8085-8095 范围内端口分配（显式指定优先，自动分配兜底）
- [x] 3.3 增加端口冲突检测与无可用端口时的错误输出
- [x] 3.4 增加 `.venv` 初始化能力并保持幂等

## 4. 依赖安装策略固化

- [x] 4.1 对齐并补全依赖安装脚本的行为与规格（官方源、缓存优先、代理兜底）
- [x] 4.2 增加对国内镜像的检测与失败退出（pip/npm/pnpm 配置）
- [x] 4.3 将 CACHE/PROXY 策略与结果写入 `sitehub.log`

## 5. Nginx 安全更新流程

- [x] 5.1 增加 Nginx 配置更新脚本的备份流程
- [x] 5.2 增加 `nginx -t` 预检与失败自动回滚
- [x] 5.3 增加 dry-run（仅生成与校验，不写入 live 配置）
- [x] 5.4 成功路径执行 reload 并记录操作日志

## 6. 验证与质量门禁

- [x] 6.1 为关键脚本增加最小可用的自检用例（可在 CI/本地运行）
- [x] 6.2 运行 `.venv/bin/flake8 src/` 并修复问题
- [x] 6.3 运行 `.venv/bin/pytest` 并修复问题
- [x] 6.4 运行 `bash scripts/deploy.sh --dry-run` 并确保输出符合预期
