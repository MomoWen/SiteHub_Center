# Trae 全局规则

1) OpenSpec（强制）
- 提案：openspec/changes/{id}/proposal.md，含用户故事、验收、安规/性能影响
- 定义：在 specs/ 生成 Deltas；先通过 openspec validate
- 应用：Spec 锁定且 tasks.md 完成后改代码
- 归档：上线经 SiteHub 验证后合并与清理

2) 环境与网络
- 兼容 FnOS 的 Nginx/PM2
- 禁用国内源；proposal 标注海外源；优先 10.8.8.80 缓存
- 统一 Unix 路径，保证 Ubuntu/FnOS 可迁移

3) 部署与回滚
- releases/ 时间戳 + current 软链
- 部署前执行 opencode check
- sitehub.yaml 必含回滚路径

4) AI 指令
- /openspec:new 开提案
- /openspec:apply 按 Spec 生成
- /openspec:validate 校验与 specs 一致

5) 协作约束
- 任务清单跟踪；先跑类型检查/规范
- 禁止记录或提交密钥；仅在用户要求时提交
- 编辑用补丁；前端用预览验证
- 记忆仅保稳定事实与偏好
