# fengshen-skillai

> Claude Code SkillAI 系统 — 让 Unity SkillEditor 项目策划用自然语言配/审游戏技能

[![npm version](https://img.shields.io/npm/v/fengshen-skillai)](https://www.npmjs.com/package/fengshen-skillai)
[![mental_model](https://img.shields.io/badge/mental__model-v0.16.41-blue)](https://github.com/cipher-wb/fengshen-skillAI)
[![license MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

把《封神》项目内部验证的 SkillAI 工作流打包成 Claude Code 可复用的 npm scaffold 包：4 agent peer review 闭环 + 15 升正式不变量心智模型 + 7 道防线 + 完整工具链。其他 Unity SkillEditor 项目装上后开箱即用。

---

## ⚠️ 前置依赖（**安装本工具前必须先装好**）

| # | 依赖 | 怎么装 | 验证 |
|---|------|--------|-----|
| 1 | **Node.js ≥ 18** | https://nodejs.org/ → 下 LTS .msi → 默认下一步 | `node --version` |
| 2 | **Python ≥ 3.10**（含 pip） | https://www.python.org/downloads/ → **安装时勾 "Add Python to PATH"** ⚠️ | `python --version` + `pip --version` |
| 3 | **Git** | https://git-scm.com/ → 默认安装 | `git --version` |
| 4 | **Claude Code CLI** | `npm install -g @anthropic-ai/claude-code` | `claude --version` |
| 5 | **CC Switch**（管 API Key / 桌面 GUI） | https://github.com/farion1231/cc-switch/releases → 下最新 `cc-switch-Setup-x.x.x.exe` → 双击装 | 桌面看到 CC Switch 图标 |
| 6 | **Unity Editor** | https://unity.com/download → Unity Hub → 装任意版本 | Unity Hub 能看到你的工程 |

### 一键验证（全部装好后跑）

```powershell
# Windows PowerShell（4 行都有版本号 = OK）
node --version; python --version; pip --version; claude --version
```

### Claude Code + CC Switch 配置（首次使用）

1. **装 Claude Code CLI**：`npm install -g @anthropic-ai/claude-code`
   - 国内慢用淘宝镜像：`npm config set registry https://registry.npmmirror.com`
2. **启动 CC Switch**（桌面图标）→ 添加 Provider → 填 API Key + Base URL → 点 "Apply"
3. **关掉所有 cmd/PowerShell 终端**，重开一个新的（让环境变量刷新）
4. 在 Unity 工程根跑 `claude` → 自动用 CC Switch 配的 Provider（不需要登录 Anthropic 官方账号）

### ❗ 常见坑

| 现象 | 修法 |
|------|------|
| `'pip' 不是内部或外部命令` | Python 没装 / 或装时没勾 "Add Python to PATH" → 重装 Python 时勾上 |
| `'claude' 命令找不到` | 关重开终端 / 或重启电脑让 PATH 生效 |
| 切 Provider 后 claude 还用旧 Key | 关掉当前终端 / 开新终端再跑 `claude`（环境变量需刷新） |
| `npm install -g` 提示权限不足 | 用"管理员身份"打开 PowerShell / cmd |

详细安装指南（含 macOS/Linux）见 [docs/日常工作流-FAQ.md](docs/日常工作流-FAQ.md)。

---

## 🤖 CC Switch 模型选择推荐（**很重要 / 别图便宜选错**）

> **核心认知**：fengshen-skillai 是"工具 + 守则" / 但**底层 LLM 能力决定 90% 体验**。
> 9 个 GATE 工作流 + 6 步 designer 规约 + 4 层 review 审核 — 弱模型容易跳步偷懒 / 强模型严格遵守。
> 不要盲目图便宜选 minimax 等弱模型 / 会让你怀疑 fengshen-skillai 本身的能力。

### 推荐档位（按强度）

| 档位 | 模型 | Provider 选择 | 适用场景 |
|------|------|--------------|---------|
| 🥇 **顶级** | **Claude Opus 4.7 / 4.6** | Anthropic 官方 / Console API | 配复杂技能（扇形分层 / 多段连招 / 状态机） / 严格 9 GATE 工作流 |
| 🥇 **顶级** | **Claude Sonnet 4.6** | Anthropic 官方 / Console API | 日常配审 / 速度比 Opus 快 / 能力 90% |
| 🥈 **中等偏上** | **GLM-4.6** | 智谱 BigModel 官方 | 国内便宜 / 指令遵循中上 / 大部分技能 OK |
| 🥈 **中等偏上** | **DeepSeek V3.2** | DeepSeek 官方 | 国内便宜 / 推理强 / 偶尔 GATE 跳步 |
| 🥉 **中等** | **Qwen3-Max / Qwen3-Plus** | 通义官方 | 中文友好 / 复杂 prompt 偶尔漏读 |
| ❌ **不推荐** | **minimax 系列 / Yi 系列 / 早期 Kimi** | 任何 Provider | 复杂 agent prompt 跳读 / 工具调用偷懒 / 实战中"嘴上说改实际没改"严重 |
| ❌ **绝对避免** | 1 元/百万 token 的"超便宜模型" | 任何 Provider | 多半是蒸馏量化版 / 推理深度不够 / **review 100+ 节点必崩** |

### 怎么选

#### 场景 A：你是个人 / 想要最好体验

→ **Claude Opus 4.7 + Anthropic 官方 Console API**（不走 CC Switch）

```powershell
# 去 https://console.anthropic.com/ 充值 + 拿 API Key
$env:ANTHROPIC_API_KEY = "sk-ant-..."
claude   # 直接用 Opus 4.7
```

成本：~$15/百万 input token / 性价比不算高 / 但能力顶。

#### 场景 B：国内团队 / 性价比优先

→ **GLM-4.6** （智谱 BigModel 官方 / CC Switch 配 Provider）

- 注册 https://open.bigmodel.cn → 拿 API Key
- CC Switch 添加 Provider:
  - 名称：智谱 GLM-4.6
  - Base URL：`https://open.bigmodel.cn/api/anthropic` （智谱兼容 Anthropic API 格式）
  - API Key：填刚拿的
- 切到该 Provider → 跑 claude

成本：~¥30/百万 input token / 能力够用 80% 复杂技能。

#### 场景 C：穷预算 / 学习用

→ **DeepSeek V3.2**（DeepSeek 官方）

- 注册 https://platform.deepseek.com → 拿 API Key
- CC Switch Provider：
  - Base URL：`https://api.deepseek.com/anthropic`
- 注意：DeepSeek 偶尔会跳 GATE / 复杂技能可能需要补提示

成本：~¥5/百万 input token / 适合 review 简单技能 / 配复杂技能勉强。

### 怎么验证你的模型能不能严格遵守工作流

跑这个测试：

```
你：审一下 <某个真实技能 JSON>

预期合格输出（v1.0.7 工业化）：
  ☑ 4 层审核完整（Layer 1-4 每层都有内容）
  ☑ <PENDING_APPLY> 块完整（含 sticky_note + node_desc_patches + p0_patches）
  ☑ 主对话用 AskUserQuestion 工具弹 ☑☑☑☑ 4 选项多选框（不是纯文字问）
  ☑ 你勾选后 → designer 输出 <APPLY_DONE> + diff 摘要
  ☑ 检查 SkillEditor / 节点 Desc 真的改了 / sticky 真的新建了

❌ 任何一项缺失 = 模型偷懒（不是 fengshen-skillai 的锅 / 换强模型解决）
```

### 详细诊断（"我同事 AI 比较蠢" 怎么办）

见 [docs/日常工作流-FAQ.md §模型差异诊断](docs/日常工作流-FAQ.md) / 含 4 层差异源排查（模型 / memory / Provider / 会话历史）。

---

## ⚠️ 在哪跑 `claude`：必须在 Unity 工程根

```powershell
# ✅ 正确：cd 到 Unity 工程根（含 Assets/ 那一层）再跑
cd D:\Unity\MyMOBA
claude

# ❌ 错误：在桌面 / C:\ / 其他目录跑 → SkillAI 不生效
```

**为什么**：Claude Code 启动时自动加载**当前目录**的 `.claude/agents/`。fengshen-skillai 把 4 个 agent 装到你 Unity 工程根的 `.claude/agents/` → 必须在那个目录跑 claude 才能触发"配技能/审技能"等命令。

**验证**：跑 `claude` 后说一句"你能看到 fengshen-skillai 的 skill-designer agent 吗" / 它能回答 = 正确目录。

---

## 30 秒安装

```powershell
# Windows 例（你的 Unity 工程在 D:\Unity\MyMOBA / 含 Assets/ 子目录的那一层）
npx fengshen-skillai@latest init D:\Unity\MyMOBA

# 或者先 cd 进去再跑
cd D:\Unity\MyMOBA
npx fengshen-skillai@latest init .
```

```bash
# macOS / Linux 例
npx fengshen-skillai@latest init /Users/yourname/Unity/MyProject
```

**怎么找你的 Unity 工程根**：打开 Unity Hub → Projects 标签页 → 看 "Location" 列。
工程根 = 含 `Assets/` `Library/` `ProjectSettings/` 子目录的那一层。**不是** Assets 内部 / **不是** Unity Hub 总目录。
详细路径例子 + 错误反例 + 检测命令见 [docs/日常工作流-FAQ.md](docs/日常工作流-FAQ.md)。

交互式 prompt 收集 3 个核心配置（SkillGraph JSON 根 / Excel 配置表绝对路径 / AI 段位），自动生成：
- `.claude/agents/` 4 个 agent（红/绿/蓝/橙）
- `.claude/skills/` 2 个 skill
- `.claude-plugin/plugin.json` Claude Code 官方 plugin manifest
- `doc/SkillAI/mental_model/` 完整心智模型（15 升正式不变量 + 16 子系统页）
- `doc/SkillAI/postmortem/` 38+ 个已踩坑教训
- `doc/SkillAI/tools/` 13 个 Python 工具脚本
- `CLAUDE.md` 项目级 SkillAI 工作守则（若已有 CLAUDE.md → 智能合并 fengshen 段 / 不破坏团队原内容）
- `fengshen.config.json` 用户配置

---

## 🔍 查看当前版本 / 是否需要升级

### 我装的是哪个版本？

```powershell
# 方法 1：在你 Unity 工程根跑（推荐 / 看你工程实际装的版本）
cd D:\Unity\MyMOBA
npx fengshen-skillai version
# 输出: fengshen-skillai npm: 1.0.x  /  mental_model: v0.16.41

# 方法 2：查 fengshen.config.json
cat fengshen.config.json | findstr fengshen_skillai_version
# 或在 PowerShell：Get-Content fengshen.config.json | Select-String version
```

### npm 上最新版是几？

```powershell
# 方法 1：直接拉最新跑（一句话搞定）
npx fengshen-skillai@latest version

# 方法 2：只看版本号不下载
npm view fengshen-skillai version
```

### 两个版本号对比

| 你装的 | npm 最新 | 结论 |
|--------|---------|------|
| `1.0.3` | `1.0.3` | ✅ 已是最新 / 不用升 |
| `1.0.0` | `1.0.3` | ⚠️ 落后 3 个 patch / 建议升 |
| `1.0.x` | `1.1.0` | 🆙 有新功能 / 推荐升 |

---

## 🔄 升级到新版本

### 场景 A：v1.0.x 之间小版本升级（最常见）

```powershell
# 1. cd 到你 Unity 工程根（必须）
cd D:\Unity\MyMOBA

# 2. 强制重新 init / 自动备份你的本地改动
npx fengshen-skillai@latest init . --force
```

`--force` 做的事：
- 备份你现有 `.claude/agents/` 为 `.claude/agents.fengshen.bak.<时间戳>/`
- 写入新版 `.claude/agents/` `doc/SkillAI/` `CLAUDE.md`
- **保留**你的 `fengshen.config.json`（不动你配置）

升完验证：

```powershell
npx fengshen-skillai version   # 看版本对不对
npx fengshen-skillai doctor    # 12 项健康检查
```

### 场景 B：你给 mental_model 加了本地 PostMortem 等 / 想保留

```powershell
cd D:\Unity\MyMOBA

# 升级前手动备份（双保险）
Copy-Item .claude .claude.user.bak -Recurse
Copy-Item doc\SkillAI doc\SkillAI.user.bak -Recurse

# 跑升级
npx fengshen-skillai@latest init . --force

# 用 VSCode / Beyond Compare diff 你的备份 vs 新版
# 把你加的 PostMortem / candidate 等手动 merge 回去
```

### 场景 C：怎么知道有新版发了

| 方式 | 怎么用 |
|------|--------|
| **GitHub Watch**（推荐）| https://github.com/cipher-wb/fengshen-skillAI → 右上 Watch → "Custom" 勾 "Releases" → 你邮箱收新版通知 |
| **手动刷** | 跑 `npx fengshen-skillai@latest version` 对比当前 |
| **看 CHANGELOG** | https://github.com/cipher-wb/fengshen-skillAI/blob/main/CHANGELOG.md |

---

## 这能干什么？

打开 Claude Code，直接说人话：

```
你：配一个木宗门的扇形分层弹幕技能，3 圈层 × 8 弹 = 24 颗叶刃，60° 散射，
    每颗叶刃飞行 6m，命中爆炸造成攻击力 60% 伤害

Claude：[自动派 skill-designer agent / 独立上下文]
  1. 苏格拉底式提问澄清需求（间隔 / 同 BUFF 联动 / 等）
  2. 生成 mermaid 流程图给你校对
  3. 写 IR YAML → 编译器生成 JSON
  4. 落盘到 Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/宗门技能/AIGen/
```

审技能更"工业化"（v1.0.7 / v3.1 强制流程）：

```
你：审一下 SkillGraph_30122001_坠叶三叠.json

Claude：[自动派 skill-reviewer agent / 独立上下文]
  ─── Step 1: 4 层审核 ───
  1. 结构合法（Lint 24+ 规则）
  2. 业务规则（SkillConfig / BulletConfig / TableTash / Config2ID）
  3. 语义合理（拓扑 diff / 数值范围 / 子弹序号→威力 Tag 配对铁律）
  4. 实现最优（模板/SkillTag/节点冗余）
  
  ─── Step 2: 引用 15 升正式不变量 + 39 PostMortem 挑刺 ───
  
  ─── Step 3: 准备 4 个 patch payload ───
  • Sticky Note 重写 (大白话 5 段骨架)
  • 全部节点 Desc 重写 (按 P0/P1/P2 分级 / 145 个节点全员重写 / 不漏)
  • P0 必修一起修 (含 change_json_path / old_value / new_value 完整修法)
  • 全部不写

Claude：[主对话强制弹 ☑☑☑☑ 多选框] AskUserQuestion 工具调用：

  ☑ 写入 Sticky Note   (新增 stickyNotes[0] / 5 段大白话)
  ☑ 批量写入 145 个节点 Desc   (按 guid 真改 / 含 P0 节点警示)
  ☑ P0 一起修   (3 条 patches: 改 Tag 320001→320002 / 等)
  ☐ 全部不写   (仅审完算数)

你勾选 → Claude：[调 skill-designer agent / 6 步强制执行]

  Step 1 Read target_json
  Step 2 解析 user_scope (用户勾的范围)
  Step 3 真改 JSON (≥20 patches 时 Read→Write 整体覆盖 / <20 用 Edit)
  Step 4 双数组一致性 check (nodes[] + RefIds[] / PostMortem #037)
  Step 5 再 Read 验证
  Step 6 输出 <APPLY_DONE> + diff 摘要

Claude：「改了 145 个节点 / 双数组一致 OK / sticky 已覆盖 / P0 3 项已修」
```

⚠️ **防 minimax 偷懒**：v1.0.7 给 designer 加了 6 步强制规约 + 自检清单 / 弱模型不能"嘴上说改实际没改" / 必须真调用 Edit/Write 工具 + 输出 APPLY_DONE。详见 [📖 docs/日常工作流-FAQ.md](docs/日常工作流-FAQ.md)。

---

## 命令速查

| 命令 | 用途 |
|---|---|
| `npx fengshen-skillai init [path]` | Scaffold SkillAI 系统到目标工程 |
| `npx fengshen-skillai doctor [path]` | 健康检查（**12 项验证** / 含 Python / Claude CLI / plugin.json 等）|
| `npx fengshen-skillai update [path]` | 更新到新版本（v1.1）|
| `npx fengshen-skillai download-history [path]` | 下载完整学习痕迹 GitHub Release tar.gz |
| `npx fengshen-skillai version` | 打印版本信息 |

---

## 4 个 Agent (peer review 闭环)

| Agent | 颜色 | 职责 | 触发关键词 |
|---|---|---|---|
| **skill-designer** | 🔴 红 | 自然语言 → mermaid → IR → JSON 配技能 / **6 步强制执行规约**（防偷懒）| "配/改/加 XX 技能" |
| **skill-reviewer** | 🟢 绿 | 4 层审核 + 大白话 Sticky Note + **全部节点 Desc 重写**（P0/P1/P2 分级）+ **P0 一起修** | "审一下"/"挑刺"/"对不对" |
| **skill-knowledge-curator** | 🔵 蓝 | Bootstrap 学习 / Mode B 心智回流 / Mode C 一致性巡检 | "学一批样本"/"刷新心智" |
| **skill-knowledge-auditor** | 🟠 橙 | 5 维度独立严审（替代用户手工裁决） | curator 出 delta 后自动触发 |

设计哲学：**两 AI peer review 闭环**（curator 出 → auditor 严审 → 共识达成才 COMMIT）。基于《封神》项目实战 10 次 curator 系统性偏差教训演化而来。

**v1.0.7 review 工作流升级（工业化 v3.1）**：
1. reviewer **全节点 Desc 重写**（不允许只列关键节点 / 不省辅助节点）
2. 主对话**强制 AskUserQuestion + multiSelect=true 弹 4 选项** ☑☑☑☑（不允许用纯文字问）
3. designer **6 步强制写入**（Read → 解析 scope → Edit/Write 真改 → 双数组一致 → 再 Read 验证 → 输出 APPLY_DONE）/ ≥20 patches 自动切 Read→Write 整体覆盖策略

---

## 7 道防线（mental_model 守则）

| Gate | 守则 |
|---|---|
| (a) | curator + auditor 共识推荐升正式 |
| (b) | 累积闭卷验证密度 ≥ 历史升正式典型阈值 |
| (c) | 0 反预测 |
| (d) v2 | 不修订正式 rule 编号 / 不跨级 rule |
| (e) v2 | curator 角色边界 + 措辞不预判 verdict |
| (f) | 升正式表述强制开放修饰（不用"专属/排他"封闭词） |
| (g) v3 | 同质度脚本验证 + cross-tool 一致 + 工具语义 cross-check |
| rule_2 | 永不 silent delete / 思想史完整保留 |

---

## 配置文件 `fengshen.config.json`

```json
{
  "version": 1,
  "project_root": ".",
  "skillgraph_jsons_root": "Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/",
  "skill_excel_path": "F:/MyTeam/Design/Excel/excel/1SkillEditor.xlsx",
  "ai_id_segment": 250,
  "default_skill_save_dir": "Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/宗门技能/AIGen/",
  "claude_plugin_mode": true
}
```

3 个必填字段：
- `project_root` — Unity 工程根（init 时自动检测）
- `skillgraph_jsons_root` — SkillGraph_*.json 根目录（相对 project_root）
- `skill_excel_path` — SkillEditor 导出 Excel 绝对路径

`ai_id_segment` 决定 AI 生成技能的 ID 段（如 250 = 25xxxxxx）。

---

## 双模式兼容

- **npm scaffold 模式**：`npx fengshen-skillai init` 把模板渲染并落到工程目录
- **Claude Code plugin 模式**：`.claude-plugin/plugin.json` 注册 4 agent + 2 skill / 兼容 Claude Code 官方 plugin 市场（2026 发布）

两个模式共享 `fengshen.config.json` 配置。

---

## 完整学习痕迹（可选下载 / 44MB）

npm 包仅含**轻量分水岭样本**（7.8MB / B-DESIGNER-CHAIN-001 等关键样本）。

完整 Bootstrap 学习轨迹（B-001 ~ B-061 / 581 文件 / 含 10 次系统性偏差教训链 / 升正式分水岭事件 #10 演化过程）走 GitHub Release：

```bash
npx fengshen-skillai download-history
```

或手动：[GitHub Releases](https://github.com/cipher-wb/fengshen-skillAI/releases)

---

## 工程要求

- Node.js >= 18
- Python >= 3.10（工具链 / `pip install -r doc/SkillAI/tools/requirements.txt`）
- Claude Code >= 1.0.0
- Unity（任意版本 / 已有 Assets/ 目录的工程）

---

## 致谢

本项目基于《封神》MOBA 项目 6 个月的 SkillAI 工作流实战演化（v0.1 → v0.16.41），含 50+ 批 Bootstrap 学习、9+10 连发 curator 系统性偏差教训、4 次 Gate 立法事件、15 个升正式不变量入账。

核心设计哲学：**harness engineering** — 心智模型（guides）+ lint/curator（sensors）+ steering loop（postmortem 复发 → 加强 guide & sensor）。

---

## License

[MIT](LICENSE) © 2026 cipher-wb

---

## 链接

- 🏠 主页：https://github.com/cipher-wb/fengshen-skillAI
- 📦 npm：https://www.npmjs.com/package/fengshen-skillai
- 🐛 Issues：https://github.com/cipher-wb/fengshen-skillAI/issues
- 📚 mental_model：装上后看 `doc/SkillAI/mental_model/README.md`（认知中枢）
- 🚦 7 道防线：装上后看 `CLAUDE.md`（工作守则 / fengshen-skillai 段）

---

> "不要在乎 token，我要绝对准确度。" — 项目原话 / 2026-05-10
