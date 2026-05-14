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

审技能也是一句话：

```
你：审一下 SkillGraph_30122001_坠叶三叠.json

Claude：[自动派 skill-reviewer agent]
  1. 4 层审核（结构合法 / 业务规则 / 语义合理 / 实现最优）
  2. 引用 15 升正式不变量 + 38 PostMortem 挑刺
  3. 输出大白话 sticky note 重写建议（复制粘贴回去就行）
  4. 列出关键节点 Desc 重写表
```

---

## 命令速查

| 命令 | 用途 |
|---|---|
| `npx fengshen-skillai init [path]` | Scaffold SkillAI 系统到目标工程 |
| `npx fengshen-skillai doctor [path]` | 健康检查（10 项验证）|
| `npx fengshen-skillai update [path]` | 更新到新版本（v1.1）|
| `npx fengshen-skillai download-history [path]` | 下载完整学习痕迹 GitHub Release tar.gz |
| `npx fengshen-skillai version` | 打印版本信息 |

---

## 4 个 Agent (peer review 闭环)

| Agent | 颜色 | 职责 | 触发关键词 |
|---|---|---|---|
| **skill-designer** | 🔴 红 | 自然语言 → mermaid → IR → JSON 配技能 | "配/改/加 XX 技能" |
| **skill-reviewer** | 🟢 绿 | 4 层审核 + 大白话 sticky note 重写 | "审一下"/"挑刺"/"对不对" |
| **skill-knowledge-curator** | 🔵 蓝 | Bootstrap 学习 / Mode B 心智回流 / Mode C 一致性巡检 | "学一批样本"/"刷新心智" |
| **skill-knowledge-auditor** | 🟠 橙 | 5 维度独立严审（替代用户手工裁决） | curator 出 delta 后自动触发 |

设计哲学：**两 AI peer review 闭环**（curator 出 → auditor 严审 → 共识达成才 COMMIT）。基于《封神》项目实战 10 次 curator 系统性偏差教训演化而来。

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
