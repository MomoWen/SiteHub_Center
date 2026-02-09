---
name: "SiteHub-Project-Scaffolder"
description: "从 SiteHub_Templete 派生新项目：复制目录、重置 Git、改写 sitehub.yaml/openspec.config.json、可选创建并推送 GitHub、执行 openspec init。用户要从模板克隆新项目时调用。"
---

# SiteHub Project Scaffolder

## 适用场景

当用户需要“从 SiteHub_Templete 克隆/派生一个新项目”并希望自动完成目录同步、Git 初始化、端口分配、OpenSpec 激活与（可选）GitHub 首推时调用。

## 输入参数

- project_name: 新项目名称（建议使用字母、数字、下划线或短横线）
- target_port: 预分配端口号（按本工作区规约，要求在 8085-8095 之间）
- description: 项目简述

## 输出

- 在 /home/momo/dev/projects/{project_name} 生成可运行的项目骨架
- 已完成本地 Git 初始化（可选：已创建远端并首推）
- sitehub.yaml 与 openspec.config.json 已完成元数据重塑
- OpenSpec 已初始化，项目可直接进入规范驱动流程

## 逻辑流程（必须按顺序执行）

### 0) 前置校验

1. 确认源模板目录存在：/home/momo/dev/projects/SiteHub_Templete
2. 校验 target_port 在 8085-8095 范围内；不满足则终止并给出可用端口建议
3. 校验目标目录 /home/momo/dev/projects/{project_name} 不存在；若存在则终止，避免覆盖

### 1) Directory Setup（物理目录派生）

目标：从模板创建新项目目录，剔除 .git/.venv 等不可继承内容。

推荐实现（优先）：使用一次性同步命令完成复制与排除（复制完成后再用文件系统能力做精确校验）。

- 执行目录同步（排除 .git、.venv、__pycache__、.pytest_cache、*.pyc）：

```bash
rsync -a --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '*.pyc' \
  /home/momo/dev/projects/SiteHub_Templete/ \
  /home/momo/dev/projects/{project_name}/
```

- 校验目标目录内不存在 /home/momo/dev/projects/{project_name}/.git 与 .venv

如果 rsync 不可用：用文件系统工具遍历模板目录树，逐文件写入到目标目录，并在写入阶段跳过 .git 与 .venv 路径前缀。

### 2) Metadata Update（身份重塑）

目标：把新项目的“身份”与模板彻底解耦。

1. 修改 sitehub.yaml
   - name 设置为 {project_name}
   - port 设置为 {target_port}
   - description（若存在字段）写入 {description}

2. 修改 openspec.config.json
   - 将项目名、展示名、或相关元数据更新为 {project_name}
   - 将任何指向模板路径的字段更新为新项目路径（如存在）

3. 一致性校验
   - 全局搜索 "SiteHub_Templete"，确保不存在残留引用（允许保留在模板说明类文本中，但不应出现在运行配置中）

### 3) Security & Compliance（强制合规检查）

1. 强制剔除国内镜像源配置
   - 搜索并阻断以下常见关键词残留：tsinghua、aliyun、douban、huaweicloud、ustc
   - 重点检查：pip.conf、requirements*.txt、pyproject.toml、poetry 配置、CI 脚本

2. 保持路径平台中立
   - 配置文件中不得硬编码 Windows 路径分隔符
   - 仅使用 Unix 风格路径，并避免写死特定机器的绝对路径（除非该字段是约定部署路径）

### 4) Git Lifecycle（本地 Git + 可选远端联动）

1. 在目标目录执行本地 Git 初始化

```bash
cd /home/momo/dev/projects/{project_name}
git init
```

2. 写入基础忽略规则（确保 .venv、__pycache__ 等不会被提交）
   - 若模板已包含 .gitignore，则只做必要的补全

3. 可选：创建 GitHub 私有仓库并首推
   - 优先使用 GitHub MCP（若该运行环境已提供）创建 {project_name} 私有仓库
   - 若无 GitHub MCP，但存在 gh CLI 且已登录：

```bash
gh repo create {project_name} --private --source=. --remote=origin --push
```

4. 初始提交

```bash
git add -A
git commit -m "chore: scaffold {project_name}"
```

### 5) OpenSpec Activation（规约激活）

在目标目录执行 OpenSpec 初始化：

```bash
cd /home/momo/dev/projects/{project_name}
openspec init
openspec validate
```

如果 openspec init 需要 Trae 预设，按该工作区约定选择 Trae 预设模式执行（如存在相关参数）。

## 失败处理与回滚

- 任何阶段失败时，必须保证：
  - 不污染源模板目录
  - 目标目录要么不存在，要么处于可安全删除的未初始化状态
- 如果失败发生在 Git 初始化之前：直接删除目标目录
- 如果失败发生在 Git 初始化之后但未推送：可保留目录用于排错，同时输出下一步修复建议

## 示例

输入：
- project_name: MyBookmark
- target_port: 8085
- description: "A personal bookmark hub"

期望结果：
- /home/momo/dev/projects/MyBookmark 创建完成
- sitehub.yaml/openspec.config.json 反映 MyBookmark 与 8085
- OpenSpec 已 init 且 validate 通过（若模板已具备基础 specs）
