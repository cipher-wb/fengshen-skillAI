# fengshen-skillai

> Claude Code SkillAI 系统 — Unity 策划用自然语言**配 / 审**游戏技能

[![npm version](https://img.shields.io/npm/v/fengshen-skillai)](https://www.npmjs.com/package/fengshen-skillai)
[![mental_model](https://img.shields.io/badge/mental__model-v0.16.41-blue)](https://github.com/cipher-wb/fengshen-skillAI)
[![license MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

把《封神》项目 6 个月内部验证的 SkillAI 工作流打包：4 agent peer review 闭环 + 15 升正式不变量 + 7 道防线 + 39 PostMortem。其他 Unity SkillEditor 项目装上即用。

---

# 🚀 30 秒安装

```powershell
# 1. cd 到 Unity 工程根（含 Assets/ 那一层 / Unity Hub 看 Location 列）
cd D:\Unity\MyMOBA

# 2. 一行 scaffold
npx fengshen-skillai@latest init .

# 3. 跑 Claude Code 开始用
claude
> 配一个木宗门的扇形分层弹幕技能
```

✅ 装完会在你工程下生成 `.claude/agents/` (4 agent) + `doc/SkillAI/` (心智模型 + 工具) + `CLAUDE.md` (工作守则) + `fengshen.config.json` (配置)。

> 💡 **嫌一直点 yes 烦？** Claude 默认每次跑 Bash/Edit/Write 都要你确认。加 `--dangerously-skip-permissions` 一次性授权所有工具：
>
> ```powershell
> claude --dangerously-skip-permissions
> ```
>
> ⚠️ **风险**：AI 能在你工程目录任意跑命令 / 改文件 / 不再问你。**仅在 Unity 工程根用**（cd 后再开）/ 别在 `C:\` 或 `~` 这种根目录开 / 否则 AI 可能改到你不希望改的东西。

**装之前先确认 5 项前置依赖** ↓（缺一个都跑不起来）

| # | 依赖 | 装 | 验证 |
|---|------|---|------|
| 1 | Node.js ≥ 18 | https://nodejs.org/ LTS | `node --version` |
| 2 | Python ≥ 3.10 | https://www.python.org/downloads/ ⚠️ **勾 "Add Python to PATH"** | `python --version` |
| 3 | Git | https://git-scm.com/ | `git --version` |
| 4 | Claude Code CLI | `npm install -g @anthropic-ai/claude-code` | `claude --version` |
| 5 | CC Switch（管 API Key）| https://github.com/farion1231/cc-switch/releases | 桌面图标 |

[👉 详细装法 / 常见坑 / Mac & Linux](#-前置依赖详情)

---

## ✨ 装上后能干什么

```
你：配一个直线飞 8m 的剑气子弹技能
Claude：(派 skill-designer / 9 个 GATE 强制流程)
        → 苏格拉底提问澄清 → mermaid 图给你审 → IR YAML → 编译器输出 JSON
        → 落盘到 Assets/.../Saves/Jsons/宗门技能/AIGen/
```

```
你：审一下 SkillGraph_30122001_坠叶三叠.json
Claude：(派 skill-reviewer / 4 层审核 + 全节点 Desc 重写)
        → 主对话弹 ☑☑☑☑ 4 选项多选框：
          ☑ 写入 Sticky Note  ☑ 批量改 145 个节点 Desc
          ☑ P0 一起修         ☐ 全部不写
你勾选 → designer 6 步真改 JSON → 输出 <APPLY_DONE> diff 摘要
```

---

## 📋 命令速查

| 命令 | 用途 |
|---|---|
| `npx fengshen-skillai init [path]` | Scaffold 到目标工程 |
| `npx fengshen-skillai doctor [path]` | 健康检查（12 项 / Python / Claude / plugin / 等）|
| `npx fengshen-skillai version` | 查版本（你装的 vs npm 最新对比）|
| `npx fengshen-skillai download-history` | 下完整学习痕迹（GitHub Release tar.gz） |

**查版本**：`npx fengshen-skillai version` → 看到 `1.0.x` / 跟 `npm view fengshen-skillai version` 对比 → 落后就升。

**升级**：

```powershell
cd D:\Unity\MyMOBA
npx fengshen-skillai@latest init . --force   # 自动备份现有 .claude/ 后写新版
```

---

## 🤝 4 Agent + 工作流

| Agent | 触发关键词 | 干啥 |
|---|---|---|
| 🔴 **skill-designer** | "配/改 XX 技能" | 自然语言 → mermaid → IR → JSON / **6 步强制规约**防偷懒 |
| 🟢 **skill-reviewer** | "审一下" / "挑刺" | 4 层审核 + Sticky 重写 + **全节点 Desc 重写**（P0/P1/P2 分级）+ **P0 一起修** |
| 🔵 **skill-knowledge-curator** | "学一批样本" | Bootstrap 学习 / Mode B 心智回流 |
| 🟠 **skill-knowledge-auditor** | curator 出 delta 自动触发 | 5 维度独立严审 |

设计哲学：**peer review 闭环**（curator 出 → auditor 严审 → 共识达成才 COMMIT）。基于 10 次 curator 系统性偏差教训演化。

**7 道防线**（mental_model 守则 / 详见装好的 `CLAUDE.md`）：(a) 共识 (b) 阈值 (c) 0 反预测 (d) 不跨级 rule (e) 角色边界 (f) 开放修饰 (g) 工具语义 cross-check + rule_2 永不 silent delete。

---

# 📚 详细文档（按需展开）

<details>
<summary><b>🔧 前置依赖详情</b>（详细装法 + 常见坑 + macOS/Linux）</summary>

#### Python 安装（最容易踩坑）

| 现象 | 原因 + 修法 |
|------|------|
| `'pip' 不是内部或外部命令` | Python 没装 / 或装时没勾 "Add Python to PATH" → 重装 Python 时勾上 |
| `'claude' 命令找不到` | 关重开终端 / 重启电脑让 PATH 生效 |
| `npm install -g` 权限不足 | **管理员身份**打开 PowerShell |
| 切 CC Switch Provider 后 claude 还用旧 Key | 关掉当前终端 / 开新终端再跑 `claude`（环境变量需刷新）|
| `npm` 下载慢 | `npm config set registry https://registry.npmmirror.com` |

**完整一键验证**：

```powershell
node --version; python --version; pip --version; claude --version
# 4 行都有版本号 = OK
```

#### macOS / Linux 装法

```bash
# Python
brew install python@3.11    # macOS
sudo apt install python3 python3-pip   # Ubuntu

# Node.js
brew install node@20        # macOS
# Linux 推荐 nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Claude Code
npm install -g @anthropic-ai/claude-code
```

详见 [docs/日常工作流-FAQ.md](docs/日常工作流-FAQ.md)。

</details>

<details>
<summary><b>🖥️ PowerShell 7 推荐</b>（cmd 中文乱码 / 命令补全弱 → 一行命令换 PS7）</summary>

```powershell
winget install --id Microsoft.PowerShell --source winget
```

装完开始菜单搜 "PowerShell 7"（蓝色图标 / 跟旧 PS5 是两个）。

| 维度 | ❌ cmd | ⚠️ PS5 | ✅ **PS7** |
|------|------|------|------|
| 中文 Unicode | **乱码** | 中（要 `chcp 65001`）| ✅ **完美 UTF-8** |
| `&&` 命令链 | ✅ | **❌ 不支持**（坑！）| ✅ |
| 跨平台 | 仅 Win | 仅 Win | ✅ Win/Mac/Linux |
| 性能 | 慢 | 中 | ✅ **快 30-50%** |
| 错误信息 | 一行 | 多行拥挤 | ✅ 行号定位 |

**进阶**：装 Windows Terminal + PS7（多标签 / 主题）：

```powershell
winget install --id Microsoft.WindowsTerminal --source winget
```

> 不会 PowerShell 语法不影响 / fengshen-skillai 命令在 cmd / PS5 / PS7 / Git Bash 全跑得通。换 PS7 只是更舒服。

</details>

<details>
<summary><b>🤖 CC Switch 模型选择推荐</b>（<b>很重要 / 别图便宜选错</b>）</summary>

**核心认知**：fengshen-skillai 是"工具 + 守则" / 但底层 LLM 能力决定 90% 体验。**弱模型容易跳步偷懒 / 不要图便宜选 minimax**。

| 档位 | 模型 | 适用 |
|------|------|------|
| 🥇 顶级 | Claude **Opus 4.7 / Sonnet 4.6** | 配复杂技能 / 严格遵守 9 GATE |
| 🥈 中上 | **GLM-4.6** / **DeepSeek V3.2** | 国内便宜 / 大部分技能 OK |
| 🥉 中等 | Qwen3-Max | 中文友好 / 复杂偶尔漏读 |
| ❌ 不推荐 | minimax / Yi / 早期 Kimi | 跳读 / 工具调用偷懒 |
| ❌ 绝对避免 | 1 元/百万 token 模型 | 蒸馏量化 / review 100+ 节点必崩 |

#### Provider Base URL 速查（CC Switch 配置用）

| Provider | Base URL |
|----------|----------|
| Anthropic 官方 | 不走 CC Switch / 直接 `$env:ANTHROPIC_API_KEY` |
| 智谱 GLM-4.6 | `https://open.bigmodel.cn/api/anthropic` |
| DeepSeek V3.2 | `https://api.deepseek.com/anthropic` |

#### 验证你的模型够格

```
跑：审一下 <真实技能 JSON>

合格 v1.0.7 工业化输出：
  ☑ 4 层审核完整
  ☑ <PENDING_APPLY> 块完整
  ☑ AskUserQuestion 工具弹 ☑☑☑☑ 4 选项（不是纯文字问）
  ☑ designer 输出 <APPLY_DONE> + diff
  ☑ SkillEditor 节点 Desc 真改了

❌ 任一缺失 = 模型偷懒 → 换强模型
```

["我同事 AI 比较蠢" 4 层差异诊断 →](docs/日常工作流-FAQ.md)

</details>

<details>
<summary><b>⚠️ 在哪跑 claude</b>（必须 Unity 工程根 / 不能任意目录）</summary>

```powershell
cd D:\Unity\MyMOBA    # ✅ 必须在含 Assets/ 那层
claude

# ❌ 桌面 / C:\ / 其他目录跑 → SkillAI 不生效
```

**为什么**：Claude Code 启动时自动加载**当前目录** `.claude/agents/`。fengshen-skillai 把 4 agent 装到 Unity 工程根 → 必须在那跑。

**推荐**：VSCode / Cursor → Open Folder 选工程根 → 内置 Terminal 跑 `claude` / 永远不会跑错。

</details>

<details>
<summary><b>📦 配置文件 + 双模式 + 学习痕迹</b></summary>

#### `fengshen.config.json`（3 项必填）

```json
{
  "project_root": ".",
  "skillgraph_jsons_root": "Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/",
  "skill_excel_path": "F:/MyTeam/Design/Excel/excel/1SkillEditor.xlsx",
  "ai_id_segment": 250
}
```

#### 双模式兼容

- **npm scaffold**：`npx fengshen-skillai init` 把模板渲染并落到工程目录
- **Claude Code plugin**：`.claude-plugin/plugin.json` 注册 4 agent / 兼容 Claude Code 官方 plugin 市场

#### 完整学习痕迹（44MB 可选）

npm 包仅含轻量分水岭样本（7.8MB）。完整 Bootstrap 学习轨迹（B-001~B-061 / 581 文件 / 含 10 次系统性偏差教训链）走 GitHub Release：

```bash
npx fengshen-skillai download-history
```

或手动 [GitHub Releases](https://github.com/cipher-wb/fengshen-skillAI/releases)。

</details>

<details>
<summary><b>📖 更多文档</b></summary>

- [docs/日常工作流-FAQ.md](docs/日常工作流-FAQ.md) — 双仓库工作流 / 别人怎么更新 / 模型差异诊断
- [docs/PUBLISHING.md](docs/PUBLISHING.md) — 给维护者：发版流程
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 架构说明
- [docs/PLACEHOLDER_REFERENCE.md](docs/PLACEHOLDER_REFERENCE.md) — 占位符参考
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — 贡献指南
- 装好后看 `doc/SkillAI/mental_model/README.md` — 认知中枢
- 装好后看 `CLAUDE.md` — 工作守则 / fengshen-skillai 段

</details>

---

## 链接 + License

- 🏠 https://github.com/cipher-wb/fengshen-skillAI
- 📦 https://www.npmjs.com/package/fengshen-skillai
- 🐛 https://github.com/cipher-wb/fengshen-skillAI/issues
- 📄 [MIT](LICENSE) © 2026 cipher-wb

---

> 设计哲学：**harness engineering** — 心智模型（guides）+ lint/curator（sensors）+ steering loop（postmortem 复发 → 加强 guide & sensor）。
>
> "不要在乎 token，我要绝对准确度。" — 项目原话 / 2026-05-10
