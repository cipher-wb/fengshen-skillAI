# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式。
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [1.0.0] - 2026-05-13

### Added — 首版公开发布 ⭐

**封装目标**：把《封神》项目内部验证的 SkillAI 系统打包成可复用的 Claude Code scaffold 包，让其他 Unity SkillEditor 项目能 `npx fengshen-skillai init` 开箱即用。

#### CLI 命令
- `npx fengshen-skillai init [path]` — Scaffold SkillAI 系统到目标工程
- `npx fengshen-skillai doctor [path]` — 健康检查（10 项验证）
- `npx fengshen-skillai download-history [path]` — 下载完整 batch_buffer 学习痕迹（GitHub Release）
- `npx fengshen-skillai version` — 打印版本 + mental_model 信息

#### 4 Agent (fast-path peer review 闭环)
- `skill-designer` (红队) — 自然语言 → mermaid → IR → JSON 配技能
- `skill-reviewer` (绿队) — 4 层审核 + 大白话 sticky note 重写
- `skill-knowledge-curator` (蓝队) — bootstrap 学习 / Mode B 心智回流 / Mode C 一致性巡检
- `skill-knowledge-auditor` (橙队) — 5 维度独立严审

#### Mental Model v0.16.41
- 15 升正式不变量（D-1606 + D-1904 + D-2303 + D-2401 + D-2706 + D-2801 + D-3801 + D-4001 + D-4004 + D-4006 + D-5201 + D-5401 + D-5601-B + 2 项）
- 7 道防线（Gate (a)~(g) v3 / fast-path peer review 闭环 / 角色边界 / 表述开放修饰 / 同质度脚本 / cross-tool 一致 / 工具语义 cross-check / rule_2 永不 silent delete）
- 16 子系统页（含子弹系统 / SkillEditor文件结构 / 工具链 等 v0.16.41 新增）
- 完整 Bootstrap 学习样本范围 521 个 in_scope / 97.9% 学习集

#### 工具链
- skill_compiler.py — IR YAML → SkillGraph JSON
- skill_decompiler.py — SkillGraph JSON → IR YAML
- skill_lint.py — Lint 24+ 规则
- skill_graph_to_mermaid.py — JSON → mermaid 视觉化
- 6+ 其他工具脚本

#### PostMortem
- 38+ 已踩坑沉淀（含 v0.16.41 新增 #039 CREATE_BULLET RefConfigBaseNode 包装 + #040 空子弹 Model=4）

#### 配置参数化
- 3 项核心参数：`project_root` / `skillgraph_jsons_root` / `skill_excel_path`
- Handlebars 模板渲染 + Python 自定义 placeholder（避开 dict `{{}}` 冲突）

#### 双模式兼容
- npm scaffold：`npx fengshen-skillai init`
- Claude Code 官方 plugin：`.claude-plugin/plugin.json`

### Distribution
- **npm 包**: ~7.8 MB（轻量 / 不含完整 batch_buffer 学习痕迹）
- **GitHub Release**: `fengshen-learning-history-v0.16.41.tar.gz` ~44 MB（完整学习痕迹 / 想看的人手动下载）
