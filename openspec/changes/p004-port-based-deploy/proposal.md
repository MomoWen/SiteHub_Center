## Why

当前部署链路依赖 Host 头路由，配合容器端 84xx 端口映射时会出现配置与访问不一致的问题。为避免域名绑定和 Hosts 修改的成本，需要将部署策略升级为端口驱动，并确保 Nginx listen 端口与宿主机 external_port 一致。

## What Changes

- 在 sitehub.yaml 中增加 external_port 字段，作为端口驱动部署的入口条件
- 当 external_port 位于 8400-8500 范围内时，生成端口驱动的 Nginx vhost（listen external_port，server_name _）
- vhost root 固定指向 /usr/share/nginx/sites/{app_name}，支持静态站点直出
- 部署前扫描 /etc/nginx/conf.d/ 下现有配置，阻止 external_port 冲突
- 自动化闭环保持为：同步代码 -> 生成端口配置 -> 重载 Nginx -> 汇报可访问 URL

## Capabilities

### New Capabilities
- `port-based-nginx-routing`: 基于 external_port 生成端口驱动的 Nginx vhost 配置并回写
- `external-port-conflict-scan`: 部署前扫描现有 Nginx vhost，阻止端口冲突

### Modified Capabilities
- `site-provisioning`: 记录已分配的 external_port，避免冲突并支持审计

## Impact

- 代码：sitehub.yaml 解析、Nginx 配置渲染与端口冲突扫描逻辑
- 配置：Nginx vhost 模板与 external_port 范围校验
- 运维：新增端口分配记录与冲突阻断策略
