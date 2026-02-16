## 1. 同步引擎

- [x] 1.1 创建 deploy_service.py 并定义 SyncEngine 结构
- [x] 1.2 实现 rsync 优先、scp 回退与默认排除列表
- [x] 1.3 实现远端目录存在性校验与 SSH 参数复用
- [x] 1.4 实现同步后权限修正与属主一致
- [x] 1.5 实现权限修正日志输出
- [x] 1.6 实现 rsync chmod 权限策略

## 2. Nginx 配置与推送

- [x] 2.1 实现 sitehub.yaml 远端解析与缺失告警流程
- [x] 2.2 实现 Nginx 配置生成与预览输出
- [x] 2.3 实现 use_sudo 推送与失败备份逻辑
- [x] 2.4 实现 NginxEngine 推送与 docker exec 重载

## 3. 验证与演示

- [x] 3.1 增加同步与 Nginx 预览的最小验证脚本
- [x] 3.2 运行 lint 与 typecheck 并修复问题
- [x] 3.3 运行测试与演示同步输出
