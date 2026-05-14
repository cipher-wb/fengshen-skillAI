# CLAUDE.md — fengshen-skillai npm 包源码 / 给 AI 维护者的工作守则

> ⚠️ 这是 **fengshen-skillai npm 包的源代码仓库**（cipher-wb 维护）/ **不是** Unity SkillEditor 工程。
> 任何在此目录跑 Claude Code 的 AI（包括接手维护的新 AI）必须先读完这份。

---

## 一句话定位

这个 repo 把《封神》项目（源工程 `F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/`）的 SkillAI 系统打包成 npm scaffold 包发到 npmjs / GitHub。**用户写代码在源工程 / 发版在这个 repo**。

---

## 🚀 用户最可能让你做的事 → 怎么做

### 1. "把本地改动推到云端" / "发版" / "quick release"

**一行命令**：

```powershell
cd F:\fengshen-skillAI
pwsh scripts/quick-release.ps1
```

quick-release.ps1 v2 自动做：
1. 从 `F:/DreamRivakes2/.../doc/SkillAI/` 抽 templates（`extract-from-source.js`）
2. 检测 mental_model 版本是否变 → 变了自动重打 tarball + 算 sha256 + 写回 package.json
3. 跑 e2e + unit 测试
4. `npm version patch` (1.0.x → 1.0.x+1)
5. git commit + tag + push（自动用代理 7897 if needed）
6. `gh release create` 含 tarball
7. `npm publish` retry 3 次

可选 flags：
- `-BumpType minor` 改 minor bump
- `-ForceTarball` 强制重打 tarball
- `-SkipTarball` 跳过 tarball
- `-DryRun` 只 show 不真发

### 2. "更新 README" / "改文档"

直接 `Edit` 改 → 再跑 `pwsh scripts/quick-release.ps1` 发 patch 版本。

### 3. "改 CLI 代码"（bin/ 或 lib/）

```powershell
# 1. 改代码 (Edit lib/commands/init.js 等)
# 2. 跑测试
npm test
node scripts/test-init.js
# 3. 一行发版
pwsh scripts/quick-release.ps1
```

### 4. "改 agent / mental_model"（源工程内的）

**不要直接改 fengshen-skillAI repo 的 `templates/`**！每次 extract 会被覆盖。

正确做法：去源工程改 `F:/DreamRivakes2/.../doc/SkillAI/...` 或 `.claude/agents/...` → 然后 `pwsh scripts/quick-release.ps1` 自动抽到 templates。

---

## 🗺️ 关键文件指针

| 文件 | 作用 |
|------|------|
| `bin/cli.js` | CLI 入口（commander 注册 5 子命令） |
| `lib/commands/{init,doctor,download-history,version,update}.js` | 5 个子命令实现 |
| `lib/core/{config,placeholders,template-engine,path-utils,conflict-resolver,manifest}.js` | 核心库 |
| `scripts/extract-from-source.js` | 从源工程抽 templates（占位符替换）|
| `scripts/quick-release.ps1` | **一键发版**（你 90% 要用的）|
| `scripts/prepare-release-tarball.js` | 单独生成完整学习痕迹 tar.gz |
| `templates/` | scaffold 模板（**自动生成 / 别手动改**）|
| `.claude-plugin/plugin.json` | Claude Code 官方 plugin manifest |
| `package.json#fengshenMentalModelVersion` | 当前 mental_model 版本（要和源工程同步）|
| `docs/PUBLISHING.md` | **详尽发版手册 v2** |
| `docs/日常工作流-FAQ.md` | 用户面 FAQ |
| `docs/ARCHITECTURE.md` | 架构说明 |

---

## ⚠️ 绝对不能做的事

- ❌ **直接改 `templates/`** — 下次 extract 会覆盖。改源工程。
- ❌ **跳过 `npm test` + `e2e` 直接 npm publish** — v1.0.5 / v1.0.12 都靠 e2e 自动捕获到 bug。
- ❌ **在用户没拍板时主动 bump mental_model 版本** — 这是用户决策。
- ❌ **强制 push 到 main** — 永远 fast-forward。
- ❌ **改 `extract-from-source.js` 占位符正则不加 `(?m)^` 行首锚** — v1.0.12 就是这个 bug（错匹配 `prior_mental_model_version_` 字段）。
- ❌ **手动 `npm publish` 不走 quick-release.ps1** — 漏掉 tarball 检测 + retry / 容易出 v1.0.0~v1.0.10 那种"mental_model 变了但没重打 tar.gz"的隐性 bug。
- ❌ **删 `fengshen-learning-history-v0.16.XX.tar.gz`** — 还在 GitHub Release / 本地副本可删但要确认远端在。

---

## 🛠️ 环境配置（你机器上的）

- **git 代理**：用户 Clash 端口 **7897**（不是常见的 7890 / 7078）。直连 GitHub 容易 SSL_ERROR_SYSCALL。push 失败 → `git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push ...`
- **npm 代理**：发 publish 前确认 `npm config get proxy` 走代理（同 7897）/ 不然 ECONNRESET。
- **npm token**：已配在 `~/.npmrc` `//registry.npmjs.org/:_authToken=...`（Granular Token / All packages / Bypass 2FA enabled）。
- **gh CLI**：已 auth `cipher-wb` GitHub。

---

## 📋 发版完整 checklist（quick-release.ps1 自动包含 / 但你想手动跑也行）

参考 `docs/PUBLISHING.md` Part 2 日常更新流程。

---

## 🎯 你接手时的第一动作

1. 跑 `git status` 看本地脏不脏
2. 跑 `git log --oneline -5` 看最近 5 个 commit / 了解版本节奏
3. 看 `package.json` 当前版本号 + `fengshenMentalModelVersion`
4. 看 `templates/_doc/SkillAI/mental_model/README.md` 顶部 mental_model_version 是否和 package.json 同步
5. 如果用户说"发版" → 直接 `pwsh scripts/quick-release.ps1`

---

## 历史 bug 沉淀（防止再踩）

| 版本 | bug | 修法 |
|------|-----|------|
| v1.0.0~v1.0.10 | tar.gz 不自动重打 / 只挂 v1.0.0 那份 | v1.0.11 引入 quick-release.ps1 v2 自动检测 |
| v1.0.5 | extract 后丢 plugin.json（emptyDir 清空）| v1.0.6 extract-from-source.js 末尾自动 copy |
| v1.0.12 | mental_model 正则错匹配 `prior_mental_model_version_` | v1.0.13 改 `(?m)^` 行首锚 |

---

## 你不是配技能的 AI

如果用户在这个 repo 里跑 Claude Code 后说 "配一个木宗门技能" — **请提醒他**：

> "这个 repo 是 fengshen-skillai npm 包源码 / 不是 Unity 工程。配技能请去你的 Unity 工程根（如 `F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/`）/ 在那里跑 claude 才能用 skill-designer agent。"

---

> 设计者：cipher-wb / Claude Opus 4.7 / 2026-05-14
