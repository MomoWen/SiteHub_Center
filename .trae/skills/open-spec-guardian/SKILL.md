---
name: "open-spec-guardian"
description: "在 apply 代码前强制运行 openspec validate，比对实现与 proposal.md/specs。用于执行或审核改动前的规范拦截。"
---

# OpenSpec-Guardian（规范守门员）

目标
- 在 Trae 准备 apply 代码之前，强制执行 openspec validate，确保实现未偏离 proposal.md 与 specs 的定义

触发时机
- 任何执行代码修改（Apply）或合并前的审核环节
- 计划完成、Spec 锁定且 tasks.md 已分解，但尚未执行改动时

输入参数
- change_id：变更标识（必填），对应 openspec/changes/{change_id}/
- project_root：项目根路径，默认当前仓库
- strict_mode：布尔，默认 true；开启时验证失败直接阻断 Apply

前置约束
- 规范驱动开发（SDD）：Proposal → Specs Deltas → Validate → Apply → Archive
- 必须存在 openspec/changes/{change_id}/proposal.md 与 specs/ 下的增量差异

执行步骤
1) 结构检查
- 校验 proposal.md、tasks.md、specs/ 是否存在；缺失即阻断并输出缺项列表

2) 规范校验
- 运行 openspec validate
- 成功：记录“可执行”结果并允许进入 Apply
- 失败：输出冲突/偏离信息，阻断 Apply 并提示回到 Definition 修正

3) 证据与日志
- 将校验结果与版本信息写入 sitehub.log，保留审计轨迹
- 建议在 CI 中作为前置步骤运行以实现强制门禁

幂等与冲突处理
- 多次运行仅更新最新验证结果；不修改业务代码
- strict_mode=false 时给出警告但不阻断（不推荐）

输出
- PASS/FAIL 状态
- 缺失项列表与偏离报告（若有）
- 审计日志路径：sitehub.log

示例
- OpenSpec-Guardian(change_id="feat-login", strict_mode=true)
- 结果：validate 通过则进入 Apply；失败则阻断并提示修正

架构价值
- 将 SDD 落为强制工序，防止“先写代码、后补规范”的风险
- 保障所有改动均以规范为锚点，提升一致性与可审计性
