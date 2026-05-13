# 技能蓝图工具链 (PoC v0.1)

> 用法速查。详细工程方案见 [PRD-自然语言生成技能蓝图系统.md](../PRD-自然语言生成技能蓝图系统.md)。

## 工具一览

| 工具 | 用途 | 输入 | 输出 |
|------|------|------|------|
| `skill_compiler.py` | **正向**：IR YAML → SkillGraph JSON | `*.skill.yaml` | `SkillGraph_*.json` |
| `skill_lint.py` | 验证 SkillGraph JSON 合法性 | `SkillGraph_*.json` | 控制台报告 + 退出码 |
| `skill_graph_to_mermaid.py` | **反向**：SkillGraph JSON → mermaid + 参数表 | `SkillGraph_*.json` | `*.md` |
| `_extract_enums.py` | 从 TableDR_CS 提取枚举字典（中英整数三向映射） | `common.*.cs` | `skill_editor_enums.json` |

## 依赖

```powershell
pip install pyyaml jsonschema openpyxl
```

## 快速开始

### 1) 编译 IR → JSON

```powershell
cd {{PROJECT_ROOT_WIN}}
python SkillAI\tools\skill_compiler.py `
  SkillAI\tools\samples\test_minimal_bullet.skill.yaml `
  --out SkillAI\tools\samples\SkillGraph_30122900_PoC测试-直线子弹.json -v
```

### 2) Lint 验证

```powershell
python SkillAI\tools\skill_lint.py `
  SkillAI\tools\samples\SkillGraph_30122900_PoC测试-直线子弹.json
```

退出码：0 通过 / 1 有 ERROR / 2 strict 模式有 WARN。

### 3) 反向转 mermaid

```powershell
python SkillAI\tools\skill_graph_to_mermaid.py `
  SkillAI\tools\samples\SkillGraph_30122900_PoC测试-直线子弹.json `
  --out demo.md
```

### 4) Unity 测试

把生成的 JSON 复制到目标目录：

```powershell
Copy-Item `
  SkillAI\tools\samples\SkillGraph_30122900_PoC测试-直线子弹.json `
  Assets\Thirds\NodeEditor\SkillEditor\Saves\Jsons\宗门技能\AIGen\ -Force
```

然后在 Unity 编辑器：

1. **Project 视图** → 切到 [{{SKILLGRAPH_JSONS_ROOT}}宗门技能/AIGen/](../../../../{{SKILLGRAPH_JSONS_ROOT}}宗门技能/AIGen/)
2. **AssetDatabase**：Ctrl + R 或菜单 `Assets → Refresh`
3. **打开 SkillEditor 窗口**：菜单（项目内已有的快捷打开方式）
4. **加载 JSON**：在 SkillEditor 内打开 `SkillGraph_30122900_PoC测试-直线子弹.json`
5. **观察**：节点是否完整、连线是否正确、参数是否合理
6. **保存**：尝试保存（会触发 OnSaveCheck）

## IR 编写指南

最简模板：

```yaml
meta:
  ir_version: "1.0"
  skill_id: 30122900           # 8 位 ID
  skill_name: "技能名"

skill:
  element: 木                   # 金/木/水/火/土/无
  main_type: 功法技
  sub_type: 招式               # 招式/奇术/神通/身法/传承心法
  cd_type: 普通                 # 普通/连招/技能结束/充能
  cd_frames: 60
  range: 800

flow:
  - cast_anim:
      anim_id: 608
      desc: 出招动作
  - delay:
      frames: 5
      then:
        - bullet:
            pattern: 直线子弹
            bullet_id: 320032
            offset_forward: 200
```

### 引用语法

| IR 写法 | 含义 | 编译为 |
|---------|------|--------|
| `entity:主体` | 施法者 | `{V:1, PT:5}` |
| `entity:目标` | 目标单位 | `{V:2, PT:5}` |
| `entity:施法者根` | 施法者根创建者 | `{V:35, PT:5}` |
| `attr:位置X` | 单位属性"位置X" | `{V:59, PT:1}` |
| `attr:面向` | 单位属性"面向" | `{V:91, PT:1}` |
| `tag:320185` | SkillTagsConfig ID 320185 | `{V:320185, PT:3}` |
| `effect_return:32004466` | 引用其他效果的返回值 | `{V:32004466, PT:2}` |
| `5`（数字） | 普通值 | `{V:5, PT:0}` |

完整字段：见 [ir/ir_schema.json](ir/ir_schema.json)。

## 当前 PoC 阶段支持的模式

- ✅ `cast_anim` — 播放角色动作
- ✅ `cast_effect` — 播放特效
- ✅ `delay` — 延迟执行
- ✅ `bullet (pattern: 直线子弹)` — 创建子弹（最简版）
- ✅ `play_sound` — 播放音效
- ✅ `camera_shake` — 镜头抖动
- ✅ `apply_buff` — 添加 Buff
- ✅ `remove_buff` — 移除 Buff
- ✅ `modify_tag` — 修改 SkillTag 值
- 🔜 扇形多发子弹、AOE、突进、Switch、模板调用 — MVP 阶段

## Lint 规则

PoC 实现：
- E001-E007 结构性规则
- E008 REPEAT_EXECUTE 死循环防护
- E012 招式 CD ≠ 0
- E013 时序约束
- E014 入口效果引用合法
- E016 ParamType 取值合法
- W001 节点 Desc 为空
- W002 SkillTagsConfig.Desc 含拷贝后缀
- W003 子弹/特效 急速影响=0
- W009 连招最后段 BaseDuration ≠ 0

详见 [skill_lint.py](skill_lint.py) 和 [PRD §6](../PRD-自然语言生成技能蓝图系统.md)。

## 文件结构

```
tools/
├── README.md                          # 本文件
├── skill_compiler.py                  # 编译器
├── skill_lint.py                      # 验证器
├── skill_graph_to_mermaid.py          # 反向转换器
├── _extract_enums.py                  # 枚举提取器
├── skill_editor_enums.json            # 30 个枚举字典
├── ir/
│   └── ir_schema.json                 # IR JSON Schema
└── samples/
    ├── test_minimal_bullet.skill.yaml # PoC 测试 IR
    ├── SkillGraph_30122900_*.json     # 编译产物
    └── demo_30122900_compiled.md      # mermaid 反向解读
```

## 故障排查

| 现象 | 排查 |
|------|------|
| 编译错误 `IR Schema 校验失败` | 检查 `meta.ir_version` 是否 "1.0"；字段是否拼写错；类型是否匹配 |
| 编译错误 `未知的 entity 引用` | 看引用语法表（上面）；可用：主体/目标/施法者/主体伤害归属/施法者根 |
| Lint E007 `ConfigJson 解析失败` | 编译器 bug，提 issue |
| Unity 加载报 GUID 重复 | 编译器 bug：检查 uuid 生成 |
| Unity 加载后节点显示但连线丢 | 检查 `references.version` 是否 2 |
| 编辑器 OnSaveCheck 报错但 lint 通过 | lint 规则不全，要补；提 issue |

## 下一步路线（参考 PRD §12）

- [ ] PoC 阶段补全：写 3 个金标准样本（30115001 / 30122003 / 30122001）
- [ ] PoC 阶段补全：Skill 封装到 `.claude/skills/skill-design/`
- [ ] MVP 阶段：扇形/AOE/突进/Switch/模板调用 等模式
- [ ] MVP 阶段：Editor 工具 C# 一键导入
- [ ] 稳定版：SkillEditor Window 内嵌 AI 助手面板
