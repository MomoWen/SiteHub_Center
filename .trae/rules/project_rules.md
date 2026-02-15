# 项目规则（SiteHub_Templete）

1) 定位
- 母版仓库，产出需可迁移
- 继承全局规约，不复述

2) 技术与目录
- Python 3.10+、FastAPI；依赖由 .venv 管理
- src/ 业务；scripts/ 运维与 deploy.sh；openspec/ 变更起点

3) 依赖
- 仅用官方 PyPI
- 新库需在 openspec/changes/{id}/proposal.md 说明

4) 环境与路径
- 模拟生产路径 /vol1/1000/MyDocker/web-cluster/sites/
- 环境变量：SITEHUB_ENV=dev|prod；CACHE_SERVER 可为空；启用时 pip 追加 --index-url http://10.8.8.80:3141/...
- 所有依赖安装必须在 proxyon 环境下执行

5) 命令
- Lint：.venv/bin/flake8 src/
- Types：.venv/bin/mypy .（严格模式，提交前必须通过）
- Spec：openspec validate
- Test：.venv/bin/pytest
- Dry-run：bash scripts/deploy.sh --dry-run

6) Mypy 配置
- 基础环境：python_version = 3.10
- 严格约束：disallow_untyped_defs = True；disallow_incomplete_defs = True
- 预检告警：warn_unused_ignores = True；warn_no_return = True
- 兼容策略：ignore_missing_imports = True（第三方库缺失类型存根时不阻塞）

7) 发布与回滚
- deploy.sh 实现 releases/ 与 current 的原子替换

7) 冲突与文档
- 与全局冲突时以本文件参数为准（如端口 8085-8095）
- 修改 sitehub.yaml 时更新 README
