# 发布流程 (Release Workflow)

> 本文档面向 fengshen-skillai 的发布者 (cipher-wb)。

## 前置条件

- npm 账号 + `npm login` 完成
- GitHub CLI (`gh`) 已认证
- 源工程 `F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/` 可访问
- mental_model 升级到 v0.16.40 完成 (Step 1)

## T-1 day: 准备

```powershell
cd F:/fengshen-skillAI

# 1. 抽源 (从 F:/DreamRivakes2 抽 templates)
node scripts/extract-from-source.js `
  --source F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj `
  --dest ./templates `
  --include-batch-buffer=false

# 2. 验证占位符
grep -r "F:/DreamRivakes2" templates/  # 应 0 hit

# 3. 安装依赖
npm install

# 4. e2e 测试
node scripts/test-init.js

# 5. dry-run npm pack 看体积
npm pack --dry-run | tail -20
# 期望 ~7.8MB

# 6. 准备完整学习痕迹 tar.gz
node scripts/prepare-release-tarball.js `
  --source F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj `
  --out ./fengshen-learning-history-v0.16.40.tar.gz

# 7. 把 sha256 填到 package.json#fengshenLearningHistorySha256
# (脚本会打印 sha256)
```

## T-0 release day

```powershell
# 1. local smoke test
cd /tmp
mkdir test-fengshen
cd test-fengshen
mkdir -p Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons
node F:/fengshen-skillAI/bin/cli.js init . `
  --non-interactive `
  --skillgraph-root=Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/ `
  --excel-path=$(pwd)/fake.xlsx
node F:/fengshen-skillAI/bin/cli.js doctor .

# 2. version bump (如不是 1.0.0 / 已经在 package.json 写好)
cd F:/fengshen-skillAI
npm version 1.0.0 --no-git-tag-version

# 3. git commit + tag + push
git add .
git commit -m "Release v1.0.0: initial public release"
git tag v1.0.0
git push origin main --tags

# 4. GitHub Release (挂完整学习痕迹 tar.gz)
gh release create v1.0.0 `
  --title "fengshen-skillai v1.0.0 — initial release" `
  --notes-file CHANGELOG.md `
  ./fengshen-learning-history-v0.16.40.tar.gz `
  ./fengshen-learning-history-v0.16.40.tar.gz.sha256

# 5. npm publish
npm publish --access public

# 6. 验证
npx fengshen-skillai@latest version  # 应该打印 1.0.0
```

## 后续 patch release

```powershell
# bug fix 类
npm version 1.0.1 --no-git-tag-version
git add . && git commit -m "1.0.1: fix XXX"
git tag v1.0.1 && git push --tags
npm publish
gh release create v1.0.1 --notes "..."
```

## 后续 minor / mental_model bump release

```powershell
# 1. 先在源工程升级 mental_model (例如 v0.16.40 → v0.17.0)
# 2. 重抽 templates
node scripts/extract-from-source.js

# 3. 更新 package.json#fengshenMentalModelVersion
# 4. 准备新 release tarball
node scripts/prepare-release-tarball.js --out ./fengshen-learning-history-v0.17.0.tar.gz

# 5. npm minor bump
npm version 1.1.0 --no-git-tag-version
git add . && git commit -m "v1.1.0: mental_model v0.17.0"
git tag v1.1.0 && git push --tags
gh release create v1.1.0 ./fengshen-learning-history-v0.17.0.tar.gz
npm publish
```

## 回滚

如果发布有问题：

```powershell
# 1. npm unpublish (有限制 / 仅 72h 内)
npm unpublish fengshen-skillai@1.0.0

# 2. 或 deprecate
npm deprecate fengshen-skillai@1.0.0 "Has known bug, use 1.0.1+"

# 3. GitHub release 删
gh release delete v1.0.0 --yes
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```
