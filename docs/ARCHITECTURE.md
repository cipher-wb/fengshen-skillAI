# fengshen-skillai — 架构说明（开发者文档）

> 本文档面向**贡献者** / 想理解项目内部架构的人。普通用户看 [README.md](../README.md) 即可。

## 双模式架构

```
                    ┌─────────────────────────┐
                    │  fengshen-skillai npm   │
                    │   (this repository)     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼────────┐       ┌────────▼─────────┐
            │ npm scaffold   │       │ Claude Code      │
            │ 模式           │       │ plugin 模式      │
            │                │       │                  │
            │ npx ... init   │       │ /plugin install  │
            └───────┬────────┘       └────────┬─────────┘
                    │                         │
            ┌───────▼─────────────────────────▼────────┐
            │     templates/ (单一事实源)               │
            │     ├── _claude/  → .claude/             │
            │     ├── _doc/     → doc/                 │
            │     └── _root/    → 工程根              │
            └──────────────────────────────────────────┘
```

**关键洞察**：plugin 模式下 handlebars 不替换（Claude Code plugin spec 限制），所以 agent .md 通过运行时**读 `fengshen.config.json`** 拿路径。两个模式共享同一份 templates / 同一份配置文件。

## 模块依赖图

```
bin/cli.js
   │
   └─ lib/commands/
       ├─ init.js       ──┐
       ├─ doctor.js       │
       ├─ update.js       │
       ├─ download-history.js
       └─ version.js      │
                          │
                  ┌───────▼──────────────────────────────┐
                  │ lib/core/                            │
                  ├──────────────────────────────────────┤
                  │ config.js          读写配置文件      │
                  │ placeholders.js    handlebars + py   │
                  │ template-engine.js 递归遍历 + 渲染   │
                  │ path-utils.js      Win/Unix 互转     │
                  │ conflict-resolver  备份/合并/abort   │
                  │ manifest.js        sha256 + 三方 diff│
                  └──────────────┬───────────────────────┘
                                 │
                  ┌──────────────▼──────────────┐
                  │ lib/utils/                  │
                  ├─────────────────────────────┤
                  │ logger.js (chalk wrapper)   │
                  │ prompt.js (@inquirer)       │
                  └─────────────────────────────┘
```

## 占位符替换两种语法

### Handlebars `{{X}}` (用于 markdown / yaml / json)

```markdown
工作目录：{{PROJECT_ROOT}}/
SkillGraph 根：{{SKILLGRAPH_JSONS_ROOT}}
Excel 路径：{{SKILL_EXCEL_PATH}}
```

### Python 自定义 `<<X>>` (避开 dict `{{}}` 冲突)

```python
SAVES_ROOT = Path("<<PROJECT_ROOT>>/<<SKILLGRAPH_JSONS_ROOT>>")
EXCEL_PATH = "<<SKILL_EXCEL_PATH>>"
```

详见 [PLACEHOLDER_REFERENCE.md](PLACEHOLDER_REFERENCE.md)。

## 抽源流程

```
源工程 (F:/DreamRivakes2/.../DreamRivakes2_U3DProj/)
    │
    │  scripts/extract-from-source.js
    │
    ▼
templates/_claude/, _doc/, _root/
    │  (替换 F:/DreamRivakes2/... → {{PROJECT_ROOT}}/)
    │  (.md/.yaml → .hbs / .py → 用 <<X>>)
    │
    ▼
templates/manifest.json (含每文件 sha256)
```

## scaffold 流程

```
npx fengshen-skillai init D:/MyProject
    │
    │  bin/cli.js → lib/commands/init.js
    │
    ▼
1. 检测 Unity 工程 (Assets/ 目录)
2. 收集 3 个配置参数 (skillgraph_jsons_root / skill_excel_path / ai_id_segment)
3. 验证 config schema
4. 检测 .claude/ 冲突 → 备份/合并/abort 三选一
5. 收集 templates/ 文件 (lib/core/template-engine.js)
6. 构建渲染上下文 (lib/core/placeholders.js)
7. 渲染并写入 (handlebars or python placeholder)
8. 处理 CLAUDE.local.md 特殊合并 (lib/core/conflict-resolver.js)
9. 写 fengshen.config.json + .fengshen-skillai/install.json
10. 输出 post-install hints
```

## install manifest

`.fengshen-skillai/install.json` 记录每个文件的：
- `sha256` 安装时的 hash
- `owner` 谁拥有这个文件 ('fengshen-skillai' / 'user-modified')
- `source_template` 来自 templates/ 哪个文件
- `action` 'rendered' / 'copied'

用于 `update` 时的三方 diff：
- 用户改过的文件 → prompt 用户选 (keep mine / take new / open diff)
- 未改文件 → 直接更新

## 测试

```bash
npm test                # 跑 lib/ 单测
npm run test:e2e        # 跑 scripts/test-init.js 干净工程 init + verify
```

## 发布流程

详见 [RELEASE.md](RELEASE.md)。

简版：
1. memory 升级 mental_model v0.16.40 (一次性 / 在源工程)
2. `node scripts/extract-from-source.js` 抽 templates
3. `node scripts/test-init.js` e2e 测试
4. `node scripts/prepare-release-tarball.js` 准备完整学习痕迹 tar.gz
5. `npm version 1.0.0` + git tag + push
6. `gh release create` 挂 tar.gz
7. `npm publish --access public`
