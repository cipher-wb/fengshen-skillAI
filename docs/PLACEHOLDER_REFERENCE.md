# 占位符参考 (Placeholder Reference)

> 本文档列出 templates/ 内可用的所有占位符 + 替换语义。

## 两套语法

| 语法 | 用途 | 文件类型 |
|---|---|---|
| `{{X}}` (handlebars) | markdown / yaml / json | `.md` / `.yaml` / `.json` / `.hbs` |
| `<<X>>` (custom) | Python | `.py` |

Python 用自定义语法避开 dict 字面量 `{{}}` 冲突。

## 全部占位符

### POSIX 风格 (默认 / Unity + Python + Bash 都接受)

| 占位符 | 替换值 | 示例 |
|---|---|---|
| `{{PROJECT_ROOT}}` / `<<PROJECT_ROOT>>` | 工程根绝对路径 | `D:/MyUnityProject` |
| `{{SKILLGRAPH_JSONS_ROOT}}` / `<<SKILLGRAPH_JSONS_ROOT>>` | SkillGraph_*.json 根 (相对 project_root) | `Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/` |
| `{{SKILLGRAPH_JSONS_ROOT_ABS}}` | SkillGraph_*.json 根绝对路径 | `D:/MyUnityProject/Assets/Thirds/.../Jsons/` |
| `{{SKILL_EXCEL_PATH}}` / `<<SKILL_EXCEL_PATH>>` | SkillEditor Excel 绝对路径 | `F:/MyTeam/Design/Excel/excel/1SkillEditor.xlsx` |
| `{{DEFAULT_SKILL_SAVE_DIR}}` | AI 生成技能默认目录 | `Assets/Thirds/.../Jsons/宗门技能/AIGen/` |

### Windows 风格 (仅 PowerShell 命令示例用)

| 占位符 | 替换值 |
|---|---|
| `{{PROJECT_ROOT_WIN}}` | `D:\MyUnityProject` |
| `{{SKILLGRAPH_JSONS_ROOT_WIN}}` | `Assets\Thirds\NodeEditor\SkillEditor\Saves\Jsons\` |
| `{{SKILL_EXCEL_PATH_WIN}}` | `F:\MyTeam\Design\Excel\excel\1SkillEditor.xlsx` |

### 元数据

| 占位符 | 替换值 | 示例 |
|---|---|---|
| `{{FENGSHEN_VERSION}}` | 安装时 npm 包版本 | `1.0.0` |
| `{{MENTAL_MODEL_VERSION}}` | 安装时 mental_model 版本 | `v0.16.40` |
| `{{INSTALL_TIMESTAMP}}` | ISO 8601 时间戳 | `2026-05-13T12:34:56.000Z` |
| `{{AI_ID_SEGMENT}}` | AI 生成技能 ID 段位 | `250` |
| `{{PYTHON_EXEC}}` | Python 可执行命令 | `python` / `python3` / `py` |

## Handlebars helpers

| Helper | 用途 | 示例 |
|---|---|---|
| `{{quote X}}` | 用双引号包围 | `{{quote SKILL_EXCEL_PATH}}` → `"F:/.../1SkillEditor.xlsx"` |
| `{{posix X}}` | 强制 POSIX 风格 | `{{posix SKILLGRAPH_JSONS_ROOT}}` |
| `{{windows X}}` | 强制 Windows 风格 | `{{windows SKILLGRAPH_JSONS_ROOT}}` |
| `{{json X}}` | JSON 序列化 | `{{json config}}` |

## 文件后缀约定

- `.md` / `.yaml` / `.json` 文件**含**占位符 → 加 `.hbs` 后缀 (如 `skill-designer.md.hbs`)
- `.md` / `.yaml` / `.json` 文件**不含**占位符 → 保持原名 (直接 copy)
- `.py` 文件 → **始终**用 `<<X>>` 自定义占位符 (即使不含占位符也安全)，**不**加 `.hbs` 后缀

## 渲染时 verification

scaffold 渲染完每个文件后会跑 `findUnresolvedPlaceholders(content)`：

- 如果文件含 `{{XXX}}` 或 `<<XXX>>` (大写英文字符 + 下划线) → **报错**
- 例外：`{{!-- ... --}}` (handlebars 注释)、Python dict 字面量 `{key: value}` 不会误判

## 抽源时怎么生成占位符

`scripts/extract-from-source.js` 在抽源时自动替换：

```javascript
// markdown / yaml / json
content = content
  .replace(/F:\/DreamRivakes2\/ClientPublish\/DreamRivakes2_U3DProj/g, '{{PROJECT_ROOT}}')
  .replace(/Assets\/Thirds\/NodeEditor\/SkillEditor\/Saves\/Jsons\//g, '{{SKILLGRAPH_JSONS_ROOT}}')
  .replace(/F:\/DreamRivakes2\/Design\/Excel\/excel\/1SkillEditor\.xlsx/g, '{{SKILL_EXCEL_PATH}}');

// python
content = content
  .replace(/F:\/DreamRivakes2\/ClientPublish\/DreamRivakes2_U3DProj/g, '<<PROJECT_ROOT>>')
  .replace(/Assets\/Thirds\/NodeEditor\/SkillEditor\/Saves\/Jsons\//g, '<<SKILLGRAPH_JSONS_ROOT>>')
  .replace(/F:\/DreamRivakes2\/Design\/Excel\/excel\/1SkillEditor\.xlsx/g, '<<SKILL_EXCEL_PATH>>');
```

## 新增占位符流程

如果未来加新参数 (如 `{{UNITY_VERSION}}`)：

1. 在 `lib/core/placeholders.js#buildContext()` 加字段
2. 在 `lib/core/config.js#defaultConfig()` 加配置字段
3. 在 `schemas/config.schema.json` 加 schema
4. 在本文件加文档
5. 在 `scripts/extract-from-source.js` 的 `PLACEHOLDER_REPLACEMENTS` 加正则
6. 在用到的 template 文件用新占位符
