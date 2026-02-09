---
name: "nginx-hotfix-master"
description: "在生成/更新 Nginx .conf 时强制执行备份、nginx -t 预检与失败自动回滚的原子流程。调用于热修复或替换配置以保障稳定性。"
---

# Nginx-Hotfix-Master（配置安全校验）

目标
- 将“Nginx 配置稳定性”固化为流程化代码逻辑，避免错误配置导致 10.8.8.80 上的站点宕机

触发时机
- 每次生成或替换 .conf 之前
- 执行热修复（Hotfix）需要保证零停机与可回滚

输入参数
- conf_name：配置文件名（必填，如 site_8087.conf）
- new_conf_source：新配置来源（文件路径或内容）
- target_root：配置目录，默认 /etc/nginx/conf.d/
- backup_root：备份目录，默认 /etc/nginx/backups/
- nginx_bin：Nginx 可执行路径，默认 /usr/sbin/nginx
- dry_run：是否仅预检不落盘，默认 false

前置约束
- 遵循 OpenSpec：变更需有 proposal 与 tasks，validate 通过后执行
- 平台中立：路径为 Unix 风格；不使用国内镜像源

原子流程
1) 备份旧配置
- 若 {target_root}/{conf_name} 存在，复制到 {backup_root}/{timestamp}/{conf_name}
- 记录备份索引以便快速回滚

2) 暂存新配置
- 将 new_conf_source 写入 {target_root}/.staging/{conf_name}
- 不直接覆盖活跃配置，确保可验证

3) 预检（nginx -t）
- 执行：{nginx_bin} -t
- 成功：继续第 4 步；失败：进入回滚（第 5 步）

4) 应用与重载
- 原子替换：将 .staging/{conf_name} 移动为 {conf_name}
- 重载：{nginx_bin} -s reload
- 记录成功日志与版本索引

5) 失败自动回滚
- 删除 .staging/{conf_name}
- 若存在备份，恢复 {backup_root}/{timestamp}/{conf_name} 至 {target_root}/{conf_name}
- 保留错误日志并提示人工复核

幂等与校验
- 内容哈希比对：若新旧一致则只记录日志，不重载
- 严格目录存在性检查；缺失时先创建

输出
- 最终配置路径、备份路径、预检结果、重载状态、日志位置

示例
- Nginx-Hotfix-Master(conf_name="site_8087.conf", new_conf_source="/tmp/site_8087.conf")
- 结果：完成备份→预检通过→原子替换→重载成功；失败则自动回滚

架构价值
- 以原子流程保证配置安全，形成“保险丝”机制，系统性降低热修复风险
