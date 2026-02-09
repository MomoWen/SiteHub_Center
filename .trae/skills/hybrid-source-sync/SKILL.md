name: "hybrid-source-sync"
description: "智能分流依赖安装策略：优先探测 10.8.8.80 本地缓存，失败则自动通过 Mihomo 代理回退至海外官方源。"

# Hybrid-Source-Sync（源策略执行）

目标
- 统一“海外源 + 本地缓存”策略，屏蔽网络复杂性，让依赖安装稳定、可控且符合规约

触发时机
- 执行 pip install 或 npm install 前
- 需要在不同网络条件下切换源策略时

输入参数（Input Schema）
- package_manager：pip | npm | pnpm（必填）
- CACHE_SERVER：（可选）若缺省则按 package_manager 自动补全：
  - pip: http://10.8.8.80:3141/root/pypi/+simple/
  - npm/pnpm: http://10.8.8.80:4873/
- PROXY_GATEWAY：统一代理入口，默认 http://10.8.8.80:7890 [cite: 2026-02-08]
- prefer_cache：boolean，默认 true

前置约束
- 遵循 OpenSpec：proposal→specs Deltas→validate 后执行
- 禁用国内镜像源；优先 10.8.8.80 缓存；路径统一为 Unix 风格

三阶段处理流（Logic）
阶段一：环境自检与健康探测
- 执行 curl -I -s --connect-timeout 2 ${CACHE_SERVER}
- 返回 200 或 302 → MODE=CACHE
- 否则执行 curl -I -s --connect-timeout 2 ${PROXY_GATEWAY} 通则 → MODE=PROXY；否则网络不可达并报错 [cite: 2026-02-08]

阶段二：分支策略执行（改写逻辑）
分支 A：MODE=CACHE（内网极速模式）
- pip：pip install --index-url ${CACHE_SERVER} --trusted-host 10.8.8.80 <args>
- npm/pnpm：npm config set registry ${CACHE_SERVER} --location project；随后 npm/pnpm install

分支 B：MODE=PROXY（全量海外源模式）
- 环境变量注入：
  - export http_proxy=${PROXY_GATEWAY}
  - export https_proxy=${PROXY_GATEWAY}
  - export all_proxy=socks5://10.8.8.80:7891 [cite: 2026-02-08]
- 安装：
  - pip：强制使用 https://pypi.org/simple 
  - npm：强制使用 https://registry.npmjs.org 

阶段三：规约符合性拦截（Security Guard）
- 扫描 requirements.txt 或 package.json，发现 mirrors.aliyun.com、tsinghua.edu.cn 等国内关键字立即中断并报错 

输出
- 最终采用的源策略（缓存/海外）
- 生效的命令改写片段与代理环境变量
- 健康检查结果与错误信息（如不可达/超时）
 - 可观测性：在 sitehub.log 中记录 [DEPLOY] Strategy: CACHE|PROXY 与 Source 地址 

示例
- Hybrid-Source-Sync(package_manager="pip", CACHE_SERVER="http://10.8.8.80:3141/repository/pypi/simple")
  - 结果：使用缓存改写 pip；不可达时自动启用 Mihomo 代理切海外
- Hybrid-Source-Sync(package_manager="npm")
  - 结果：无缓存配置则设置 Mihomo 代理，使用官方 registry

架构价值
- 将“源稳定性”显式化与自动化，避免 DNS 污染与网络抖动影响构建流程
- 与项目规约一致：优先本地缓存、禁用国内镜像、平台中立
 - 故障隔离：缓存宕机时自动通过代理自愈，不阻塞 deploy.sh 
