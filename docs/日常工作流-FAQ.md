# 日常工作流 FAQ — 双仓库同步 / 别人更新 / npm vs GitHub Release

> 给 cipher-wb 的速查手册（中文）/ 解决 4 个核心疑问 / 持续更新
> 创建：2026-05-14 / v1.0

---

## ⚠️ 装本工具前 / 你必须先装的 5 个东西

| # | 软件 | 必装 | 验证命令 |
|---|------|-----|---------|
| 1 | **Node.js ≥ 18** | ✅ 必须 | `node --version` 看到 v18+ |
| 2 | **Python ≥ 3.10**（含 pip）| ✅ 必须 | `python --version` 和 `pip --version` 都成功 |
| 3 | **Git** | ✅ 必须 | `git --version` 看到版本号 |
| 4 | **Claude Code** | ✅ 必须 | 这是核心 / 没它本工具没意义 |
| 5 | **Unity Editor** | ✅ 必须 | 至少有一个 Unity 工程（含 `Assets/`）|

下面是详细装法（**踩坑最多的是 Python**，单独一节说）：

### 🐍 Python 安装指南（专治 `'pip' 不是内部或外部命令` 错误）

#### Windows

**最常见错误现象**：

```
'pip' 不是内部或外部命令，也不是可运行的程序或批处理文件。
'python' 不是内部或外部命令，也不是可运行的程序或批处理文件。
```

**根因**：要么没装 Python，要么装了但没勾 "Add Python to PATH"。

##### Windows 安装步骤

1. 打开 https://www.python.org/downloads/
2. 点黄色按钮 "**Download Python 3.x.x**"（推荐 3.10 / 3.11 / 3.12）
3. 下载完双击 `python-3.x.x-amd64.exe`
4. **⚠️ 关键一步**：安装向导第一页**底部勾上 "Add python.exe to PATH"** / 不勾的话后面 pip 用不了
5. 点 **"Install Now"** → 等几分钟装完
6. 关掉所有 PowerShell / cmd / Claude Code（**必须**关重开 / PATH 才生效）
7. 重开 PowerShell → 跑 `python --version` + `pip --version` 都应该有版本号

**如果你之前装过但没勾 PATH**：去控制面板卸载 Python → 重装时记得勾 → 或手动加 PATH（搜"环境变量"教程 / 但重装更省事）。

##### Windows 如何验证装对了

```powershell
python --version        # 应输出: Python 3.10.x  (或更高)
pip --version           # 应输出: pip 23.x.x ...
where python            # 应输出: C:\Users\YourName\AppData\Local\Programs\Python\Python3xx\python.exe
                         # (有这行说明 PATH 配对了)
```

##### Windows 还是不行？

- PowerShell **重开** 一遍（已开的窗口拿不到新 PATH）
- 重启电脑（极少数顽固情况）
- 用 `py --version`（Python launcher / Windows 安装时一起装的）— 如果 `py` 可以但 `python` 不行 → 用 `py -m pip install ...` 代替

#### macOS

```bash
# 推荐用 Homebrew (https://brew.sh/)
brew install python@3.11

# 验证
python3 --version
pip3 --version

# 如果 python 命令不存在 (只有 python3) / 加个 alias
echo 'alias python=python3' >> ~/.zshrc
echo 'alias pip=pip3' >> ~/.zshrc
source ~/.zshrc
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip

# 同 macOS 加 alias
echo 'alias python=python3' >> ~/.bashrc
echo 'alias pip=pip3' >> ~/.bashrc
source ~/.bashrc
```

### 🟢 Node.js 安装

#### Windows

1. 打开 https://nodejs.org/ → 选 **LTS** 版（推荐 / 比 Current 稳）
2. 下载 `.msi` 安装包 → 双击 → 默认下一步即可（**npm 自带 / 不用单独装**）
3. 装完关重开 PowerShell → `node --version` 看到 v18+

#### macOS

```bash
brew install node@20
```

#### Linux

```bash
# 用 nvm 装 (推荐 / 多版本切换方便)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
```

### 🟣 Git 安装

| OS | 命令 |
|----|------|
| Windows | https://git-scm.com/download/win → 下载安装 |
| macOS | `brew install git` 或装 Xcode Command Line Tools `xcode-select --install` |
| Linux | `sudo apt install git` |

### 🤖 Claude Code 安装

去 https://claude.com/code → 按平台下载安装。

### 🎮 Unity Editor

去 https://unity.com/download → Unity Hub → 装任意版本（推荐 LTS）→ 打开你的 Unity 工程。

### ✅ 全部装完后 / 一键验证

PowerShell（Windows）：

```powershell
Write-Host "─── 依赖检查 ───" -ForegroundColor Cyan
node --version
python --version
pip --version
git --version
Write-Host "─── 如果上面 4 行都有版本号 = OK ✓ ───" -ForegroundColor Green
```

Bash（macOS / Linux）：

```bash
echo "── 依赖检查 ──"
node --version && python3 --version && pip3 --version && git --version && echo "── 全 OK ✓ ──"
```

全 OK 后才能跑 `npx fengshen-skillai@latest init <你的 Unity 工程根>`。

---

## 🗺️ 先看一张图：双仓库结构

```
┌─────────────────────────────────────────────────────┐
│ 🎮 源工程 (你日常工作的地方 / Unity + Claude Code)    │
│ F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/│
│                                                      │
│ ├── doc/SkillAI/                ← 你天天改这里        │
│ │   ├── mental_model/           （15 升正式不变量等） │
│ │   ├── postmortem/             （38 个 PostMortem） │
│ │   ├── tools/                  （13 Python 工具）   │
│ │   ├── docs/                                        │
│ │   ├── samples/                                     │
│ │   └── mental_model/batch_buffer/  ← 学习痕迹       │
│ │                                                    │
│ ├── .claude/                    ← 4 agents 在这      │
│ │   ├── agents/                                      │
│ │   └── skills/                                      │
│ │                                                    │
│ ├── CLAUDE.local.md             ← 工作守则           │
│ └── 其他 Unity 工程内容                              │
└─────────────────────────────────────────────────────┘
                       │
                       │ (1) 你跑 extract-from-source.js
                       │     脚本自动抽 SkillAI 部分
                       │     替换硬编码路径为占位符
                       ▼
┌─────────────────────────────────────────────────────┐
│ 📦 npm 仓库 (给别人用的发布包)                       │
│ F:/fengshen-skillAI/                                │
│                                                      │
│ ├── bin/ lib/                   ← CLI 代码           │
│ ├── templates/                  ← 从源工程抽过来的    │
│ │   ├── _claude/                                     │
│ │   ├── _doc/                                        │
│ │   └── _root/                                       │
│ ├── package.json                                     │
│ └── ...                                              │
└─────────────────────────────────────────────────────┘
                       │
                       │ (2) git push + npm publish
                       │
                       ▼
        ┌──────────────────────────────┐
        │ 🌐 云端 (公开)               │
        │                              │
        │ • GitHub: cipher-wb/fengshen-skillAI│
        │   - 源代码 + GitHub Releases   │
        │                              │
        │ • npm: fengshen-skillai      │
        │   - npx ... 装的就是这里     │
        └──────────────────────────────┘
                       │
                       │ (3) 别人 npx fengshen-skillai@latest init
                       │
                       ▼
        ┌──────────────────────────────┐
        │ 🧑 别人的 Unity 工程         │
        │ D:/TheirProject/             │
        │ ├── .claude/                 │
        │ ├── doc/SkillAI/             │
        │ └── CLAUDE.md                │
        └──────────────────────────────┘
```

**核心理解**：你**永远在源工程改**（自然的工作位置）。`F:/fengshen-skillAI/` 是个"发布中转站"，所有内容**自动从源工程抽**，**你不需要手动 copy 文件**。

---

## 问题 1：我改了源工程 mental_model，怎么同步到云端？

### 一句话答案

跑**一个命令**：`pwsh scripts/quick-release.ps1`（在 `F:/fengshen-skillAI/` 目录下）。

### 它会自动做这些事

```
1. 从源工程 F:/DreamRivakes2/... 抽最新内容到 templates/  (extract-from-source.js)
   ├─ 替换 F:/DreamRivakes2/... → {{PROJECT_ROOT}}
   ├─ 替换 Assets/.../Jsons/ → {{SKILLGRAPH_JSONS_ROOT}}
   └─ 替换 F:/DreamRivakes2/Design/Excel/... → {{SKILL_EXCEL_PATH}} 等
2. 跑 e2e 测试 (test-init.js) — 验证 scaffold 流程
3. 跑 unit 测试 (npm test) — 26 个测试
4. 自动 patch 版本号 (npm version patch — 1.0.0 → 1.0.1)
5. git add + commit + tag v1.0.1
6. git push origin main --tags
7. gh release create v1.0.1
8. npm publish
9. npx fengshen-skillai@latest version 验证
```

### 详细步骤（如果你想手动跑）

```powershell
# 第一步：切到 npm 仓库
cd F:/fengshen-skillAI

# 第二步：抽源（自动从 F:/DreamRivakes2/... 抽 mental_model 等）
node scripts/extract-from-source.js
# 注意：你不需要手动 copy 任何文件 / 脚本会自动抽

# 第三步：验证抽出来的没问题
node scripts/test-init.js   # e2e
npm test                     # unit

# 第四步：版本号 +1
npm version patch --no-git-tag-version
# 1.0.0 → 1.0.1 (mental_model 学习类小升级)

# 第五步：commit + push
git add .
git commit -m "v1.0.1: mental_model 更新 - 描述一下你改了啥"
git tag v1.0.1
# 注意：如果之前临时 unset 过代理，记得：
git -c http.proxy= -c https.proxy= push origin main --tags
# 如果你代理是开着的 / 直接：
# git push origin main --tags

# 第六步：GitHub Release（可选 / 如果你升级了 mental_model 想挂新 tarball）
node scripts/prepare-release-tarball.js   # 生成 fengshen-learning-history-v0.16.XX.tar.gz
gh release create v1.0.1 --title "v1.0.1" --notes-file CHANGELOG.md ./fengshen-learning-history-v0.16.XX.tar.gz ./fengshen-learning-history-v0.16.XX.tar.gz.sha256

# 第七步：npm publish
npm publish --access public

# 验证
npx fengshen-skillai@latest version
```

### AI 怎么识别"要同步"

你下次跟 Claude Code 说类似的话 / AI 就知道要走这个流程：
- "把我刚才的 mental_model 改动发布到 npm"
- "更新 npm 包"
- "发个 patch 版本"
- "quick release"
- "把刚才改的同步到云端"

AI 会切到 `F:/fengshen-skillAI/`，跑 `quick-release.ps1` 或手动 7 步流程。

### 为什么需要"另一个目录"`F:/fengshen-skillAI/`？

不是为了方便 / 是 npm 规范要求的：

| 角色 | 内容 | 不能混的原因 |
|------|------|------------|
| 源工程 `F:/DreamRivakes2/...` | Unity 工程 + 你的 mental_model | 含敏感内容（路径绝对值 / 你的笔记 / Unity 二进制等）/ 太大（几个 G）/ 不适合发到公开 npm |
| npm 仓库 `F:/fengshen-skillAI/` | 只有给别人用的轻量内容 | 占位符替换 / 文件清单严控 / 大小 7.6 MB |

如果直接把源工程发上 npm：
- ❌ 你的 mental_model 里的 `F:/DreamRivakes2/...` 绝对路径会泄露到别人那
- ❌ 体积爆炸（你的 Unity 工程 + Library/ + Temp/ 可能 50+ GB）
- ❌ 含 .keystore 等敏感文件
- ❌ npm 包名规范不符（Unity 工程不是 npm 包结构）

所以**必须**有个"中转站"做转换 + 隔离。

---

## 问题 2：别人怎么收到我的更新？

### 🚦 先搞清楚：什么是 "Unity 工程根" ？

**Unity 工程根 = 含有 `Assets/` 子目录的那一层文件夹**（最关键标志）。

打开你的 Unity 工程，从最外层往里看，**第一个能看到 `Assets/` 的目录就是工程根**。

#### ✅ 正确路径长什么样

| 操作系统 | 真实路径例子 |
|---------|------------|
| **Windows** | `D:\Unity\MyMOBA\` （盘符 + 工程名 / 你打开 Unity Hub 看 "Location" 字段就是这个）|
| **Windows** | `F:\GameProjects\剑灵2\` |
| **Windows**（cipher-wb 的封神项目） | `F:\DreamRivakes2\ClientPublish\DreamRivakes2_U3DProj\` |
| **macOS** | `/Users/yourname/Unity/MyProject/` |
| **macOS** | `~/Documents/Projects/MOBA/` |
| **Linux** | `/home/yourname/unity/myproject/` |

**这层目录下应该能看到**（缺一不可）：

```
D:\Unity\MyMOBA\               ← 这是工程根 ✓
├── Assets/                    ← ★ 关键标志：必须有 Assets/ 子目录
├── Library/                   ← Unity 自动生成（也是工程根的标志）
├── Packages/                  ← Unity 包管理
├── ProjectSettings/           ← Unity 工程配置
├── Logs/
├── Temp/
└── *.sln / *.csproj           ← Visual Studio 工程文件
```

#### ❌ 错误反例（千万别在这些目录跑 init）

| 错误路径 | 为什么错 |
|---------|---------|
| `D:\Unity\MyMOBA\Assets\` | ❌ 太深 / 这是 Assets 子目录 / 工程根在它**外面** |
| `D:\Unity\MyMOBA\Assets\Thirds\NodeEditor\` | ❌ 更深 / 完全错 |
| `D:\Unity\` | ❌ 太浅 / 这是 Unity Hub 的"工程总目录" / 里面可能有几十个工程 |
| `C:\Users\YourName\Desktop\` | ❌ 桌面 / 不是 Unity 工程 |
| `D:\Unity\MyMOBA\Library\` | ❌ 是 Unity 缓存 / 不是工程根 |

#### 🔍 怎么确认我找对工程根了

打开 PowerShell / cmd / 终端 / 跑这个**检测命令**（替换你以为的工程根路径）：

```powershell
# Windows PowerShell
$proj = "D:\Unity\MyMOBA"      # ← 改成你的路径
if (Test-Path "$proj\Assets" -PathType Container) {
  Write-Host "✓ 找对了 / $proj 是 Unity 工程根" -ForegroundColor Green
} else {
  Write-Host "✗ 错了 / $proj 下面没有 Assets/ 目录 / 这不是 Unity 工程根" -ForegroundColor Red
}
```

```bash
# Linux/macOS
proj="/Users/yourname/Unity/MyProject"
if [ -d "$proj/Assets" ]; then echo "✓ 找对了"; else echo "✗ 错了"; fi
```

返回 ✓ 才能继续跑 init。

#### 💡 还不确定？打开 Unity Hub 看

Unity Hub → Projects 标签页 → 找到你的工程 → 右边 "Location" 列显示的路径**就是工程根**。直接复制粘贴用。

---

### 场景 A：别人首次安装（永远跑这个）

**完整路径例子**：

```powershell
# Windows 例子 1（D 盘 Unity 工程）
npx fengshen-skillai@latest init D:\Unity\MyMOBA

# Windows 例子 2（F 盘 / 路径含中文）
npx fengshen-skillai@latest init "F:\GameProjects\剑灵2"
# 注意：路径含空格或中文要用双引号包围

# Windows 例子 3（如果你已经 cd 到工程根了）
cd D:\Unity\MyMOBA
npx fengshen-skillai@latest init .
# 这个 . 代表"当前目录"
```

```bash
# macOS / Linux 例子
npx fengshen-skillai@latest init /Users/yourname/Unity/MyProject
# 或
cd /Users/yourname/Unity/MyProject
npx fengshen-skillai@latest init .
```

**跑完看到这些就成功**：

```
✓ Detected: Unity project at D:\Unity\MyMOBA
? Where are your SkillEditor JSON files relative to project root? ...
...
✓ .claude/agents/ (4 agents)
✓ doc/SkillAI/ (190 files, mental_model v0.16.41)
✓ fengshen.config.json
```

`@latest` 标记会自动拉 npm 上最新版本。别人无需关心你版本号是几。

### 场景 B：别人已经装过 v1.0.0 / 想升级到你刚发的 v1.0.1

**当前 v1.0 你刚发的版本**：还没实现 `update` 命令（这是 v1.1 计划）。临时方案：

```powershell
# 别人在他自己 Unity 工程根执行
# 例：他的工程在 D:\Unity\MyMOBA
cd D:\Unity\MyMOBA

# 1. 备份本地 SkillAI 内容 (PowerShell 版)
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
Move-Item .claude ".claude.bak.$ts"
Move-Item doc\SkillAI "doc\SkillAI.bak.$ts"
Move-Item CLAUDE.md "CLAUDE.md.bak.$ts" -ErrorAction SilentlyContinue

# 2. 重新跑 init 拉新版 (fengshen.config.json 自动保留)
npx fengshen-skillai@latest init . --force

# 3. 手动 diff 本地改动 vs 新版 (用任意 diff 工具)
# 推荐 Beyond Compare / VS Code 的 "Compare with..." 功能

# 4. 把他自己加的 PostMortem / candidate 等本地改动 merge 回新版

# 5. 跑 doctor 验证
npx fengshen-skillai doctor
```

```bash
# macOS / Linux 版（同一个工程根 / 不同 shell 命令）
cd /Users/yourname/Unity/MyProject

ts=$(date +%Y%m%d-%H%M%S)
mv .claude ".claude.bak.$ts"
mv doc/SkillAI "doc/SkillAI.bak.$ts"
mv CLAUDE.md "CLAUDE.md.bak.$ts" 2>/dev/null

npx fengshen-skillai@latest init . --force
diff -r ".claude.bak.$ts" .claude
diff -r "doc/SkillAI.bak.$ts" doc/SkillAI
npx fengshen-skillai doctor
```

### 场景 C：你以后实现 v1.1 后

到 v1.1 发布时，别人只需在他 Unity 工程根（即含 `Assets/` 的目录）：

```powershell
# Windows 例 (别人的工程在 D:\Unity\MyMOBA)
cd D:\Unity\MyMOBA
npx fengshen-skillai@latest update .
# 自动 3-way merge / 保留他的本地改动 / 拉你的新内容
```

### 别人能下载完整学习痕迹吗？

可以。在他的 Unity 工程根：

```powershell
# Windows 例
cd D:\Unity\MyMOBA
npx fengshen-skillai download-history
# 解压到 doc/SkillAI/mental_model/batch_buffer/ 和 doc/SkillAI/samples/
```

或手动下载 https://github.com/cipher-wb/fengshen-skillAI/releases 拖拽 tar.gz 解压。

### 别人怎么知道你发新版了？

3 种方式：

| 方式 | 怎么用 |
|------|--------|
| **GitHub Watch** | 别人在你 repo (https://github.com/cipher-wb/fengshen-skillAI) 点 Watch → 选 "Releases only" → 邮件通知 |
| **手动检查** | 别人跑 `npx fengshen-skillai@latest version` / 跟自己工程里 `fengshen.config.json#fengshen_skillai_version` 对比 |
| **未来 v1.1 自动提示** | CLI 启动时自动 fetch npm latest 提示（待实现）|

### 我（cipher-wb）需要怎么通知别人？

可选：
- 在 GitHub Releases 写好 "Release Notes"（自动从 CHANGELOG.md 拉）
- 在你团队群发个消息
- 不主动通知也行 — npm 用户习惯自己刷 `npx ... version`

---

## 问题 3：7.6 MB vs 44 MB / 上传与不上传的区别？

这是**两个东西**，不要混：

### 📦 npm 包内容（7.6 MB / 实际你发的 1.8 MB 压缩）

| 文件类型 | 含/不含 | 为什么 |
|---------|--------|-------|
| 4 agents (.claude/agents/) | ✅ 含 | 别人装上就要用 |
| 2 skills (.claude/skills/) | ✅ 含 | 同上 |
| mental_model 16 子系统页 | ✅ 含 | 心智模型本体 / 必含 |
| 38 PostMortem | ✅ 含 | 教训沉淀 / 必含 |
| 13 Python 工具脚本 | ✅ 含 | scaffold 后用户跑工具用 |
| docs/ 5 份开发者文档 | ✅ 含 | 必含 |
| **样本（samples/）** | ⚠️ 仅 6 个代表 | 全部 38+ 太大 / 6 个够示范 |
| **batch_buffer 学习痕迹**（B-001 ~ B-061 / 581 文件） | ⚠️ 仅 4 个关键 keep | 完整 batch_buffer 太大（30+ MB）/ 装上的人用不到 |
| node_modules / Library/ | ❌ 不含 | 用户自己装依赖 |
| .git/ | ❌ 不含 | 不需要历史 |
| Unity 二进制资源 | ❌ 不含 | 不是 npm 包 |
| 你的 PoC / 临时文件 | ❌ 不含 | 太杂 |

**npm 包目的**：让别人 `npx ... init` 后**直接能用**。够用就行 / 不要塞太多。

**别人装上后看到的**：
```
D:/their-project/
├── .claude/                    完整 4 agents + 2 skills
├── doc/SkillAI/
│   ├── mental_model/           16 子系统页 + README + learning_log
│   ├── postmortem/             38 个 PostMortem
│   ├── tools/                  13 个 Python 工具
│   ├── docs/                   5 份开发者文档
│   ├── samples/                6 个代表样本（够看怎么用）
│   └── mental_model/batch_buffer/_seed/   4 个分水岭样本（说明文档指向 GH release）
├── CLAUDE.md
├── fengshen.config.json
└── .claude-plugin/plugin.json
```

### 🗂️ GitHub Release tar.gz（理论 44 MB / 实际你发的 3.35 MB）

完整 `batch_buffer/` 学习痕迹 + 完整 `samples/`：

| 文件 | 谁需要 |
|------|--------|
| B-001 ~ B-061 共 581 个学习记录文件 | 想看你**怎么学出来的**人（10% 重度用户）|
| 38+ 完整 samples（含 archived v08 failed 等） | 想看完整调试历史的人 |
| picks/predict/read/diff/yaml 五件套 | 想自己 bootstrap 他们项目的 mental_model 的人 |
| auditor verdict 文件 | 想看 peer review 闭环怎么跑的人 |

**这部分**：
- ✅ **你可以上传**（你已经上传了 / fengshen-learning-history-v0.16.41.tar.gz / 在 GitHub Release）
- ✅ **完全没有安全/隐私问题**（就是你的学习日志 / 不含技能 JSON / 不含敏感代码）
- ❌ **别人不需要也能用**（mental_model 是结论 / batch_buffer 是过程）
- 📥 **想看的人**：`npx fengshen-skillai download-history` 单独下载

### 为什么拆成两块？

| 方案 | 优缺 |
|------|------|
| 全塞 npm 包（约 40 MB） | ❌ 90% 用户用不到 / ❌ npm install 慢 / ❌ 占盘 |
| **拆 npm 轻量（7.6 MB）+ GitHub Release 大块（44 MB）** ⭐ | ✅ 默认体验快 / ✅ 想看研究材料的人有的看 / ✅ 灵活 |
| 全不上传 batch_buffer | ⚠️ 别人看不到学习路径 / 教学价值丢失 |

**你已经选了拆开方案** / **包括 GH release 已上传完整** / 别人可以下载。

### "这部分我可以上传给别人更新吗？"

**已经在云端了**，别人想下载就：

```bash
npx fengshen-skillai download-history
# 或手动 https://github.com/cipher-wb/fengshen-skillAI/releases 下载 tar.gz 解压
```

**下次你升级 mental_model 时**：
- 跑 `node scripts/prepare-release-tarball.js` 重新打包新 tar.gz
- `gh release create v1.0.1 ./fengshen-learning-history-v0.16.42.tar.gz` 挂到新版本
- 别人重新跑 `download-history` 就拿到新的

---

## 🎯 日常更新最常见流程（贴墙速查）

### 你天天做的：

```powershell
# 1. 在源工程 F:/DreamRivakes2/... 里改 mental_model / 加 PostMortem / etc.
#    (Claude Code 直接在源工程跑 / 不动 fengshen-skillAI repo)

# 2. 改完想发版？切到 npm 仓库一键发：
cd F:/fengshen-skillAI
pwsh scripts/quick-release.ps1
# (代理软件开着 / 不开就跑命令前手动设 npm proxy 配置)
```

### 一键发版 quick-release.ps1 内含

| 步骤 | 干啥 |
|------|------|
| 1 | 从源工程抽内容到 templates/ |
| 2 | 跑 e2e + unit 测试 |
| 3 | npm version patch (1.0.x → 1.0.x+1) |
| 4 | git commit + tag |
| 5 | git push origin main --tags |
| 6 | gh release create |
| 7 | npm publish |
| 8 | 验证 npx ... version |

### 几种特殊场景

| 场景 | 用什么命令 |
|------|----------|
| 修了个 bug / 改 CLI 代码 | `pwsh scripts/quick-release.ps1` (默认 patch) |
| 学完一批 mental_model (B-061+) | `pwsh scripts/quick-release.ps1` (patch) |
| 加了新子系统页 / 新升正式不变量 | `pwsh scripts/quick-release.ps1 minor` |
| 重大不兼容改动 (改 config schema) | `pwsh scripts/quick-release.ps1 major` |
| 想看会跑啥不真发 | `pwsh scripts/quick-release.ps1 -DryRun` |

---

## ❓ 常见疑问 FAQ

### Q1: 我直接改 `F:/fengshen-skillAI/templates/` 行吗？

❌ **不行**。templates/ 是从源工程**自动抽的**，下次 `extract-from-source.js` 一跑就被覆盖。

要改：**改源工程 `F:/DreamRivakes2/...` 里的对应文件** → 再跑 extract。

### Q2: 我源工程改了一个文件 / 但 quick-release 失败了怎么办？

按提示看错误：
- `ECONNRESET` → 代理没开 / 跑 `Test-NetConnection 127.0.0.1 -Port 7078` 检查
- `e2e 测试失败` → templates 抽出来有问题 / 看哪个测试 fail
- `npm publish 403` → token 过期 / 重新去 npm 网页生成
- `git push 失败` → 通常是代理问题 / 临时绕开：`git -c http.proxy= -c https.proxy= push origin main`

### Q3: 我可以让别人改 fengshen-skillai 项目吗（PR）？

可以。两条路：

1. **小 PR**（如修 typo / CLI bug）→ 直接接受 / merge → 你下次 release 带上
2. **mental_model 类内容**（如加 PostMortem）→ 建议**他们提到自己项目 / 不要进 fengshen-skillai 仓库**（因为你下次 extract-from-source.js 一跑就覆盖了 / 他们的改动会丢）

如果想接受 mental_model 类 PR：
- 他们改你**源工程**的 mental_model（fork 你的源工程 / 不现实 / 你源工程是私有 Unity 项目）
- 或者你提供个"贡献机制" → 他们提 issue 描述 → 你在源工程加 → 下次 extract → release

### Q4: 我能把 `fengshen-skillai` 改名吗？

可以但要小心：
- 改 `package.json#name` → 但 npm 上一旦发布 `fengshen-skillai`，**名字永远占用 / 不可改**
- 想改名 = 发个新包（如 `fengshenforge`）/ 老包 deprecate

不建议。

### Q5: 我可以删掉 `F:/fengshen-skillAI/` 目录吗？

❌ **不能**！这是 npm 包源码 + 模板 / 删了下次没法 release。

如果你想**整理空间**：
- ✅ 删 `node_modules/`（下次跑 `npm install` 恢复）
- ✅ 删 `.release-staging/`（每次发版临时产物）
- ✅ 删 `fengshen-learning-history-v*.tar.gz`（每次跑 prepare-release-tarball 重新生成）
- ❌ 千万别删 `bin/` `lib/` `templates/` `scripts/` `.git/`

### Q6: 我可以同时维护 `F:/fengshen-skillAI/` 和源工程吗？

✅ **必须同时维护**。这才是正常工作流：
- 99% 时间在源工程做事（配技能 / 学心智模型）
- 1% 时间在 fengshen-skillAI 发版

### Q7: 别人装上后改了内容 / 我升级他们会怎样？

`init --force` 会**备份**他们改的（`.fengshen.bak.<时间戳>`）然后覆盖 / 不会无声丢失。

v1.1 实现的 `update` 命令会做 3-way merge：
- 他们改过且没冲突 → 保留他们的
- 他们改过且有冲突 → prompt 选择
- 他们没改 → 直接更新

### Q8: 我账号 token 不小心泄露了怎么办？

立即去 https://www.npmjs.com/settings/cipher-wb/tokens → 找到 token → 点 **Revoke** → 立刻失效。然后重新生成新 token + 重新 `npm config set //registry.npmjs.org/:_authToken "新token"`。

### Q9: 我能查 npm 上 fengshen-skillai 多少人下载吗？

可以。https://www.npmjs.com/package/fengshen-skillai → 页面右侧有 Weekly Downloads。

或 npm CLI：`npm view fengshen-skillai`。

---

## 🔗 关键链接

- npm 包页：https://www.npmjs.com/package/fengshen-skillai
- GitHub repo：https://github.com/cipher-wb/fengshen-skillAI
- GitHub Releases：https://github.com/cipher-wb/fengshen-skillAI/releases
- npm token 管理：https://www.npmjs.com/settings/cipher-wb/tokens
- 完整发布手册：[PUBLISHING.md](PUBLISHING.md)
- 项目架构：[ARCHITECTURE.md](ARCHITECTURE.md)
- 占位符参考：[PLACEHOLDER_REFERENCE.md](PLACEHOLDER_REFERENCE.md)

---

## 📌 总结：三句话工作流

### 你 (cipher-wb) 的两件事

1. **改东西**：永远在 `F:\DreamRivakes2\ClientPublish\DreamRivakes2_U3DProj\doc\SkillAI\` 改（源工程）
2. **发版**：切到 `F:\fengshen-skillAI\` 跑 `pwsh scripts/quick-release.ps1`

### 别人的一件事

3. **别人收**：在**他自己 Unity 工程根**（含 `Assets/` 那层）跑：

   ```powershell
   # 首次装 (Windows 例 / 他的工程在 D:\Unity\MyMOBA)
   npx fengshen-skillai@latest init D:\Unity\MyMOBA

   # 已装过 / 升级 (v1.0 临时方案)
   cd D:\Unity\MyMOBA
   npx fengshen-skillai@latest init . --force
   ```

   **关键认知**：别人的工程根 ≠ 你的 `F:\DreamRivakes2\...`，他们各自有自己的 Unity 工程路径（如 `D:\Unity\MyMOBA` / `/Users/alice/Unity/X` 等）。

这就完了。

---

> 创建：2026-05-14 / 维护者：cipher-wb (with Claude Code)
> 有新疑问 → 直接问 Claude / 它会更新这份文档
