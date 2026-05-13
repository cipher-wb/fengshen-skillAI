# 上传 + 持续更新流程（Publishing Guide）

> 这是你（cipher-wb）日常维护 fengshen-skillai 的**操作手册**。
> 因为你会持续训练 mental_model 并发新版本，所以这份文档涵盖**首次上传 + 后续 N 次更新**全流程。

---

## 总览：发版三大场景

| 场景 | 触发条件 | 用什么版本号 | 频率预估 |
|---|---|---|---|
| **首次发布** | v1.0.0 / 第一次上 GitHub + npm | `1.0.0` | 1 次 |
| **mental_model 学完一批 / 修了 bug / 加 PostMortem** | 心智模型 patch 升级 | `1.0.x` (patch) | 高频（每周 1-2 次）|
| **新增子系统页 / 升正式不变量** | 知识结构变化 | `1.x.0` (minor) | 中频（每月 1-2 次）|
| **break 改动**（API/schema 不兼容） | major bump | `x.0.0` (major) | 罕见（半年/年级别）|

---

## Part 1：首次上传到 GitHub + npm（一次性）

### 1.0 预备 (5 分钟)

```powershell
# 1. 注册 npm 账号（如还没有）
# https://www.npmjs.com/signup

# 2. 本地登录 npm
npm login
# 输入 username / password / 2FA OTP

# 3. 安装 GitHub CLI（如还没有）
# https://cli.github.com/
gh auth login
# 选 github.com / SSH / web 登录

# 4. 验证
npm whoami            # 应打印 cipher-wb
gh auth status        # 应显示 ✓ Logged in
```

### 1.1 把 fengshen-skillAI 本地 repo 关联到 GitHub (1 分钟)

```powershell
cd F:/fengshen-skillAI

# 关联 remote
git remote add origin https://github.com/cipher-wb/fengshen-skillAI.git

# 或用 SSH (推荐 / 不用每次输密码)
# git remote set-url origin git@github.com:cipher-wb/fengshen-skillAI.git

# 验证
git remote -v
```

### 1.2 准备首版 templates 内容 (15 分钟)

```powershell
# 1. 先确保源工程 mental_model 是 v0.16.40 (memory 升级完成)
# 检查：F:/DreamRivakes2/.../doc/SkillAI/mental_model/README.md 头部 version

# 2. 抽源
node scripts/extract-from-source.js `
  --source F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj `
  --dest ./templates

# 3. 验证占位符无残留
node scripts/extract-from-source.js --validate

# 4. 安装依赖
npm install
```

### 1.3 e2e 测试 (5 分钟)

```powershell
# 1. 跑 e2e (干净工程 init + 验证)
node scripts/test-init.js
# 应看到 ✓ 全绿

# 2. 验证 npm pack 体积
npm pack --dry-run | findstr "package size"
# 期望 ~7-9 MB
```

### 1.4 准备完整学习痕迹 tar.gz (5 分钟)

```powershell
# 准备 GitHub Release 资产 (44MB tar.gz 含完整 batch_buffer)
node scripts/prepare-release-tarball.js `
  --source F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj `
  --out ./fengshen-learning-history-v0.16.40.tar.gz

# 把脚本打印的 sha256 复制粘贴到 package.json#fengshenLearningHistorySha256
# (用编辑器手动改 / 或用下面命令)
node -e "
  const fs = require('fs');
  const crypto = require('crypto');
  const tarPath = './fengshen-learning-history-v0.16.40.tar.gz';
  const sha = crypto.createHash('sha256').update(fs.readFileSync(tarPath)).digest('hex');
  const pkg = JSON.parse(fs.readFileSync('package.json'));
  pkg.fengshenLearningHistorySha256 = sha;
  fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
  console.log('✓ Updated package.json fengshenLearningHistorySha256 to', sha);
"
```

### 1.5 首次 commit + push 到 GitHub (2 分钟)

```powershell
# 加全部文件
git add .

# 检查 staged (确认 node_modules 没进去 / templates/ 已 ok)
git status

# 首次 commit
git commit -m "Release v1.0.0: initial public release

- 4 agent peer review 闭环 (skill-designer/reviewer/curator/auditor)
- Mental model v0.16.40 (15 升正式不变量 + 7 道防线)
- 双模式: npm scaffold + Claude Code plugin manifest
- 3 项可配置: project_root / skillgraph_jsons_root / skill_excel_path
- 38+ PostMortem 教训沉淀
- 13 Python 工具链

🤖 Generated with Claude Code"

# 推到 GitHub
git push -u origin main

# 创建 v1.0.0 tag
git tag v1.0.0
git push origin v1.0.0
```

### 1.6 创建 GitHub Release + 挂学习痕迹 tar.gz (2 分钟)

```powershell
# 用 gh CLI 一行搞定
gh release create v1.0.0 `
  --title "fengshen-skillai v1.0.0 — initial release" `
  --notes-file CHANGELOG.md `
  ./fengshen-learning-history-v0.16.40.tar.gz `
  ./fengshen-learning-history-v0.16.40.tar.gz.sha256
```

如果不用 gh，可以在网页操作：
1. 打开 https://github.com/cipher-wb/fengshen-skillAI/releases/new
2. Tag = v1.0.0 / Title = "v1.0.0 — initial release"
3. 描述粘贴 CHANGELOG 内容
4. 拖拽 `fengshen-learning-history-v0.16.40.tar.gz` 上传
5. 拖拽 `.sha256` 上传
6. Publish release

### 1.7 publish 到 npm (1 分钟 / **关键一步**)

```powershell
# 最后检查
npm pack --dry-run | head -50
# 看一遍清单 / 确认 templates/ 内容 ok / 不要发错

# 真发布
npm publish --access public

# 验证 (新开 powershell 窗口)
npx fengshen-skillai@latest --version
# 应该输出: 1.0.0 (mental_model v0.16.40)
```

🎉 完成！现在别人能用了：

```bash
npx fengshen-skillai@latest init D:/their-project
```

---

## Part 2：日常更新流程（你会重复 N 次）

> 这是**最重要的部分**——你会一直训练系统、修 bug、加 PostMortem，每次都按这个流程走。

### 场景 A：训练新一批 mental_model（最常见）

例：B-060 学了一批新样本 / D-NSCT-002 升正式 / 加了几个 PostMortem。

```powershell
# === 在源工程做完学习后 ===

# 1. 切到 fengshen-skillai 仓库
cd F:/fengshen-skillAI

# 2. 拉一下最新 (如果有从别处推过)
git pull origin main

# 3. 重新抽源 (会拉到最新 mental_model)
node scripts/extract-from-source.js
# 看输出 / 应该提示 X files extracted / 没有 hardcoded path issue

# 4. 跑 e2e 确认没坏
node scripts/test-init.js

# 5. 如果是 mental_model bump (如 v0.16.40 → v0.16.41)
#    改 package.json#fengshenMentalModelVersion
node -e "
  const fs = require('fs');
  const pkg = JSON.parse(fs.readFileSync('package.json'));
  pkg.fengshenMentalModelVersion = 'v0.16.41';  // ← 改这里
  fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
"

# 6. patch bump (默认场景 / mental_model 学习/教训类小升级)
npm version patch --no-git-tag-version
# 1.0.0 → 1.0.1

# 7. 准备新版完整学习痕迹 tarball (44MB / mental_model bump 时才要做)
node scripts/prepare-release-tarball.js --out ./fengshen-learning-history-v0.16.41.tar.gz

# 8. 更新 package.json#fengshenLearningHistorySha256
node -e "
  const fs = require('fs');
  const crypto = require('crypto');
  const sha = crypto.createHash('sha256').update(fs.readFileSync('./fengshen-learning-history-v0.16.41.tar.gz')).digest('hex');
  const pkg = JSON.parse(fs.readFileSync('package.json'));
  pkg.fengshenLearningHistorySha256 = sha;
  fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
  console.log('✓ sha256:', sha);
"

# 9. 更新 CHANGELOG.md (手动加一段 ## [1.0.1] - YYYY-MM-DD)
# 我建议你直接抄 mental_model learning_log §4 当批的 summary

# 10. commit + tag + push
git add .
git commit -m "v1.0.1: mental_model v0.16.41 - B-060 enforce 第 3 批

- D-NSCT-001 跨 subdir 加固 (新增 3 picks)
- 新增 PostMortem #041
- 累积闭卷验证密度 25 例

🤖 Generated with Claude Code"
git tag v1.0.1
git push origin main --tags

# 11. GitHub Release 挂 tarball
gh release create v1.0.1 `
  --title "v1.0.1 — mental_model v0.16.41" `
  --notes-file CHANGELOG.md `
  ./fengshen-learning-history-v0.16.41.tar.gz `
  ./fengshen-learning-history-v0.16.41.tar.gz.sha256

# 12. npm publish
npm publish

# 验证
npx fengshen-skillai@latest --version
```

**预估时间**：第一次熟悉走 30 分钟，熟练后 **10 分钟**走完。

### 场景 B：仅修 bug / 改 CLI / 改 doc（不动 mental_model）

```powershell
cd F:/fengshen-skillAI

# 1. 改完代码 / 跑测试
node scripts/test-init.js

# 2. patch bump
npm version patch --no-git-tag-version

# 3. 改 CHANGELOG ## [1.0.2] - YYYY-MM-DD: fix XXX

# 4. commit + push + publish (**不需要重生成 tarball**)
git add .
git commit -m "v1.0.2: fix doctor command miss --json output"
git tag v1.0.2
git push origin main --tags
gh release create v1.0.2 --notes-file CHANGELOG.md
npm publish
```

**预估时间**：**3-5 分钟**。

### 场景 C：新增大块功能 / 新子系统页（minor bump）

```powershell
# 1. 同场景 A 流程
# 但用 minor bump:
npm version minor --no-git-tag-version
# 1.0.x → 1.1.0

# 2. CHANGELOG 写大段更新说明 (mental_model_version 也 bump 到 v0.17.0)
# 3. 同场景 A 后续步骤
```

---

## Part 3：用户如何收到更新

### 用户 A：之前没装过 → 直接装最新

```bash
npx fengshen-skillai@latest init .
# 永远拉最新
```

### 用户 B：已经装了老版本 → 升级

**当前 v1.0 暂不支持自动 update**（v1.1 计划）。临时升级方案：

```bash
# 1. 备份 .claude/ 和 doc/SkillAI/
cp -r .claude .claude.bak
cp -r doc/SkillAI doc/SkillAI.bak
cp CLAUDE.md CLAUDE.md.bak  # 如果有

# 2. 重新跑 init (强制覆盖)
npx fengshen-skillai@latest init . --force

# 3. 手动 diff 自己之前对 mental_model 的 patch
diff -r .claude.bak .claude
diff -r doc/SkillAI.bak doc/SkillAI
diff CLAUDE.md.bak CLAUDE.md

# 4. 把自己的本地改动 merge 回来 (用户的 PostMortem / candidate 等)

# 5. 跑 doctor 验证
npx fengshen-skillai doctor
```

**v1.1 之后**：

```bash
npx fengshen-skillai@latest update .
# 自动 3-way merge / 保护用户改动
```

### 用户怎么知道有新版？

1. **手动**：用户跑 `npx fengshen-skillai@latest --version` 对比当前
2. **CLI 自动提示**（v1.1 计划）：每次 init / doctor 时 fetch latest npm version 提示
3. **GitHub watch**：用户在你 repo 点 Watch → Releases

---

## Part 4：版本号策略详解

### 何时 patch (1.0.0 → 1.0.1)

- 修 bug
- 更新 mental_model（学了新批 / 加了 PostMortem / candidate enforce 批）
- 改文档
- mental_model 版本 patch bump (v0.16.40 → v0.16.41)

### 何时 minor (1.0.x → 1.1.0)

- 新加 CLI 子命令（如 v1.1 的 update / migrate）
- 新 mental_model 子系统页
- 新升正式不变量入账
- mental_model 版本 minor bump (v0.16.x → v0.17.0)
- 加新配置字段（向后兼容）

### 何时 major (1.x.0 → 2.0.0)

- `fengshen.config.json` schema 不兼容
- CLI 命令签名 break (如 `init` 参数顺序变)
- templates/ 大改组织
- 移除某子系统页
- mental_model 主张本体撤回（rule_2 严守 / 概念反转）

### 两套版本号关系

```
fengshen-skillai npm version          mental_model_version
─────────────────────────────────────────────────────────
1.0.0  ← 首发                          v0.16.40
1.0.1  ← B-060 学完                    v0.16.41 (patch)
1.0.2  ← bug fix CLI                   v0.16.41 (不变)
1.0.3  ← B-061 学完 + 升 candidate    v0.16.42 (patch)
1.1.0  ← B-070 升正式 D-X (第 16 项)   v0.17.0  (minor)
1.1.1  ← bug fix doctor                v0.17.0  (不变)
...
2.0.0  ← config schema break           v1.0.0   (major)
```

---

## Part 5：回滚 / 应急

### 发了带 bug 的版本 → 怎么办

```powershell
# Option 1: 24h 内 → npm unpublish (有限制)
npm unpublish fengshen-skillai@1.0.5

# Option 2: 已经超 24h → npm deprecate
npm deprecate fengshen-skillai@1.0.5 "Has critical bug, use 1.0.6+"

# Option 3: GitHub release 删除
gh release delete v1.0.5 --yes
git push origin :refs/tags/v1.0.5

# Option 4: 立刻发 patch 修复 (推荐)
# 改完 bug → npm version patch → publish 1.0.6
```

### tarball sha256 算错了 → 用户下载校验失败

```powershell
# 重算 + 重传
sha256sum fengshen-learning-history-v0.16.40.tar.gz > correct.sha256

# 更新 package.json#fengshenLearningHistorySha256
# patch bump 重发 npm + 重传 GitHub Release asset
```

### 用户安装路径写错了 → 怎么帮排查

让用户跑：

```bash
npx fengshen-skillai doctor --json > diagnosis.json
```

让他贴 `diagnosis.json` 给你 / 你能看到他的：
- 配置路径
- 缺失文件
- Python 依赖状态
- mental_model 版本

---

## Part 6：FAQ

**Q1: 我能不能不公开发到 npm，只挂 GitHub？**

可以。用户用：
```bash
npx github:cipher-wb/fengshen-skillAI init .
# 或
npm install -g github:cipher-wb/fengshen-skillAI
fengshen-skillai init .
```

但这样用户拿不到 `npx ...@latest` 体验，每次都拉最新 main 分支。

**Q2: GitHub release tarball 体积越来越大怎么办？**

batch_buffer 每批 ~0.5MB。50 批后 ~25MB（当前），100 批后 ~50MB。

策略：
- 每个版本只挂**该版本的增量** + 上版本快照链接
- 或：只挂"分水岭"版本（如 v0.16/v0.17/v0.18 主版本）/ 中间 patch 不挂
- 或：把 batch_buffer 拆成独立 GitHub repo (用 submodule)

**Q3: 别人 fork 后他怎么发布自己版本？**

他改 `package.json#name` 为他自己的 npm 名（如 `@his-org/skillai`），改 GitHub owner 字段，重走 Part 1 流程。

**Q4: 我能不能让别人 commit 回来贡献 mental_model 升级？**

可以但要小心：
- 别人改 templates/ 内容 → PR
- 你 merge 前用 `node scripts/extract-from-source.js --validate` 验证
- 但 templates/ 是从你源工程抽出来的 / 别人的改动可能与你的下次抽源冲突
- 建议：mental_model 改动只接受 PostMortem 类（在 templates/_doc/SkillAI/postmortem/ 加新 .md）/ 不接受改既有 mental_model 子系统页

**Q5: 用户在 macOS / Linux 能用吗？**

Node + Python 都跨平台。但当前抽源默认假定 `F:/DreamRivakes2/...` Windows 路径。用户的 fengshen.config.json 用 POSIX 风格也能在 macOS / Linux 跑。Python 工具脚本里如有 backslash 路径需要 `os.path.normpath()` 处理（已做）。

**Q6: Claude Code 官方 plugin 市场什么时候能上？**

按 Claude Code roadmap，2026 Q2 开放公开 plugin 市场。届时你的 `.claude-plugin/plugin.json` 直接可以提交申请，零改动。

**Q7: 我每次抽源都覆盖整个 templates/ 怎么办？**

scripts/extract-from-source.js 默认会 `fs.emptyDir(templatesDir)`。如果你想保留部分手改：
- 改 `templates/`**之外**的文件（如 templates 同级的 `templates_overrides/`）
- 在抽源脚本里加 merge 逻辑

---

## Part 7：完整 cheat sheet

贴墙速查（最常见 patch 流程）：

```powershell
cd F:/fengshen-skillAI

# 抽源 + 测试 + bump + 发布
node scripts/extract-from-source.js && `
node scripts/test-init.js && `
npm version patch --no-git-tag-version && `
git add . && `
git commit -m "v$(node -p 'require(\"./package.json\").version'): mental_model 学习更新" && `
git tag v$(node -p 'require("./package.json").version') && `
git push origin main --tags && `
gh release create v$(node -p 'require("./package.json").version') --notes-file CHANGELOG.md && `
npm publish
```

把上面 chain 存为 `scripts/quick-release.ps1` / 一键发版。

---

## Part 8：心理建设

> 你说"我会一直训练这个系统，所以会经常上传方便别人更新"——
>
> 一周 1-2 次 patch 发布完全正常。npm 上千万的包都这么做。
> 不要怕"发太频繁"——每次 patch = 学到了新东西。
> 心智模型 v0.16 → v1.0 应该经过几十次 patch + 5-10 次 minor。
>
> rule_2 严守：每次发版的 CHANGELOG 写清楚学到了什么，思想史完整保留。

加油 🚀
