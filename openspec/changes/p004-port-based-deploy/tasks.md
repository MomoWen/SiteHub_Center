## 1. 模型与校验更新

- [x] 1.1 增加 SiteConfig.external_port 字段与范围校验

## 2. 端口冲突扫描

- [x] 2.1 实现 ensure_external_port_available 端口扫描逻辑
- [x] 2.2 支持同应用更新与错误信息输出

## 3. 模板与部署引擎适配

- [x] 3.1 更新 Nginx 配置模板为 default_server
- [x] 3.2 在重载前加入 nginx -t 预检

## 4. 端到端集成验证

- [x] 4.1 部署 port-test-app 并验证访问 URL
