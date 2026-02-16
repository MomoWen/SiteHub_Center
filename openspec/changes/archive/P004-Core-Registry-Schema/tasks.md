## 1. PocketBase 基座

- [x] 1.1 添加 PocketBase docker-compose 本地启动配置
- [x] 1.2 添加初始化脚本并支持 apps collection 创建

## 2. 配置与环境变量

- [x] 2.1 扩展 Settings 支持 PocketBase URL 与鉴权配置
- [x] 2.2 增加 APP_ROOT_DIR 与 dev/prod 根路径选择逻辑

## 3. 应用注册接口

- [x] 3.1 定义 apps 注册请求/响应模型与字段校验
- [x] 3.2 实现 PocketBase 异步客户端封装并接入依赖注入
- [x] 3.3 实现 POST /apps/register 写入 PocketBase
- [x] 3.4 注册时自动解析 sitehub.yaml 并写入 sitehub_config

## 4. 验证与质量门禁

- [x] 4.1 增加接口与 YAML 解析的单元测试覆盖
- [x] 4.2 运行 openspec validate、pytest、flake8 并修复问题
