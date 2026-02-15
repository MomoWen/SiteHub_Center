# SiteHub_Center

本仓库是 SiteHub_Center 项目：提供最小可运行 FastAPI 服务骨架，以及多站点初始化、发布/回滚、依赖安装网络策略与 Nginx 安全更新脚本。

## 快速开始

### 1) 安装依赖

建议使用仓库自带的网络策略脚本安装依赖：优先缓存服务器，失败则使用代理访问官方源；默认禁止国内镜像。

```bash
python3 -m venv .venv

# 使用缓存/代理策略安装（默认需要 CACHE_SERVER 或 PROXY_GATEWAY 可用）
PATH="$(pwd)/.venv/bin:$PATH" bash scripts/dependency-check.sh pip -r requirements-dev.txt

# 如果环境没有缓存/代理，但允许直连官方源：
ALLOW_DIRECT=true PATH="$(pwd)/.venv/bin:$PATH" bash scripts/dependency-check.sh pip -r requirements-dev.txt
```

相关环境变量：

- `CACHE_SERVER`：缓存服务地址（可选）
- `PROXY_GATEWAY`：HTTP 代理地址（可选）
- `prefer_cache`：是否优先缓存（默认 true）
- `ALLOW_DIRECT`：当缓存/代理都不可用时允许直连官方源（默认 false）

### 2) 运行服务

```bash
SITEHUB_ENV=dev PORT=8085 bash scripts/run.sh
```

健康检查：

- `GET /healthz`
- `GET /readyz`

## 多站点初始化

在模拟生产目录下创建站点目录，并分配 8085-8095 端口（可显式指定端口，脚本具备幂等性）。

```bash
bash scripts/provision-site.sh --site demo-site

# 指定 sites 根目录（用于本地测试）
bash scripts/provision-site.sh --site demo-site --sites-base /tmp/sites --no-venv

# 显式指定端口
bash scripts/provision-site.sh --site demo-site --port 8087
```

站点目录下会生成 `sitehub.env` 记录端口等信息。

## 发布与回滚

发布采用不可变 `releases/<timestamp>` + `current` 软链原子切换。

```bash
# dry-run：只打印计划动作，不修改文件系统
bash scripts/deploy.sh --dry-run

# 发布到指定站点根目录（通常是 provision 出来的站点目录）
SITE_ROOT="/vol1/1000/MyDocker/web-cluster/sites/demo-site"
bash scripts/deploy.sh --source "$(pwd)" --site-root "$SITE_ROOT"

# 回滚到某个 release
bash scripts/deploy.sh --site-root "$SITE_ROOT" --rollback 20260209120000
```

部署与回滚过程会追加写入 `sitehub.log`。

## 站点配置（sitehub.yaml）

部署引擎会读取站点根目录下的 `sitehub.yaml` 生成 Nginx 配置。

```yaml
name: demo-site
port: 8498
mode: static
```

字段说明：

- `name`：站点名
- `port`：应用端口（proxy 模式下转发到该端口）
- `mode`：`proxy` 或 `static`，默认 `proxy`

当 `mode=static` 时，Nginx 从 `/usr/share/nginx/sites/<name>` 提供静态文件，需要容器挂载：

`/vol1/1000/MyDocker/web-cluster/sites:/usr/share/nginx/sites:ro`

## Nginx 安全更新

更新流程：备份 → 写入 → `nginx -t` 预检 → 失败回滚/成功 reload。

```bash
# dry-run：仅校验生成的配置，不改 live 配置
bash scripts/nginx-safe-update.sh --src /path/to/generated.conf --dest /etc/nginx/nginx.conf --dry-run

# 应用到 live 配置
sudo bash scripts/nginx-safe-update.sh --src /path/to/generated.conf --dest /etc/nginx/nginx.conf
```

可通过 `NGINX_BIN` 指定 nginx 可执行文件路径。

## 质量门禁

```bash
.venv/bin/flake8 src/
.venv/bin/mypy src/
.venv/bin/pytest
```
