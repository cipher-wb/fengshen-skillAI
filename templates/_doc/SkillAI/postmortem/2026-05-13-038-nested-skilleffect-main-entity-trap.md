# PostMortem #038 — 嵌套 SkillEffect 上下文中"主体 V=1"陷阱

> 日期: 2026-05-13
> 触发: SkillGraph_2500001 链状连线指示器 PoC / 用户口头裁决修订
> 严重度: HIGH (影响所有 BulletConfig/Buff/嵌套 SkillEffect 配技能)
> 状态: 已修复 末端产物 + IR + 编译器 / 等用户拍板升 mental_model 正式不变量

---

## 一句话

`V=1 TCPT_MAIN_ENTITY "主体"` 在嵌套 SkillEffect 调用栈中 **不是**"最初施法的玩家主角"，而是**调用栈最近一层的主体**（在子弹 BornSE 里 = 子弹自身；在 Buff Effect 里 = Buff 携带者）。要拿"最初施法者"必须用 `V=35 TCPT_CREATE_ROOT_CREATOR_ENTITY_ID 施法者-根创建者`。

---

## 现象

链状连线指示器 PoC 任务，AI 在 `BulletConfig.BeforeBornSkillEffectExecuteInfo` 里挂了一个 `TSET_FOLLOW_ENTITY` 节点想让"子弹本体跟随玩家主角"。AI 默认填：

```
FOLLOW_ENTITY (ID=32001000) P[1] = {V=1, PT=5}   // TCPT_MAIN_ENTITY "主体单位实例ID"
注释 = "子弹端绑主体(玩家)"
```

用户审完口头裁决：

> 32001000 里的【被跟随目标单位】，不可以填【常用参数值 -1- 主体单位实例ID】，这个的意义是，主体是谁，它就是谁；但这个节点是从子弹链接出来的，所以主体是子弹；而我们的目的，这个值要填主角，而主角是子弹的上一级，所以这里应该填：**常用参数值 35-施法者-根创建者**

---

## 根因

### "主体" 是相对调用栈的，不是绝对的"玩家主角"

`TCommonParamType` enum（`Assets/Scripts/TableDR_CS/Hotfix/Gen/common.hotfix.cs:3777-3968`）：

| V | 枚举 | 中文 | 嵌套上下文实际指 |
|---|------|------|------------------|
| 1 | TCPT_MAIN_ENTITY | 主体单位实例ID | **调用栈最近一层的主体** |
| 3 | TCPT_CREATE_ENTITY | 施法者实例ID | 直接施法者（易被中间 buff 层覆盖）|
| 33 | TCPT_MAIN_ROOT_CREATOR_ENTITY_ID | 主体-根创建者 | 主体追溯到根创建者 |
| 35 | TCPT_CREATE_ROOT_CREATOR_ENTITY_ID | **施法者-根创建者** | **整条调用链最初的 caster ✓** |
| 37 | TCPT_MAIN_CREATOR_ENTITY_ID | 主体-创建者 | 主体的直接创建者（穿透 1 层）|

### 在不同上下文中"主体"是什么：

| 调用栈位置 | 主体 V=1 实指 |
|-----------|---------------|
| SkillConfig.SkillEffectExecuteInfo (顶层) | 玩家主角 ✓ |
| BulletConfig.BeforeBornSkillEffectExecuteInfo | **子弹自身** ⚠️ |
| BulletConfig.AfterBornSkillEffectExecuteInfo | **子弹自身** ⚠️ |
| BulletConfig.DieSkillEffectExecuteInfo | **子弹自身** ⚠️ |
| BuffConfig.OnAttachEffect / OnTickEffect | **Buff 携带者** ⚠️ |
| RUN_SKILL_EFFECT 嵌套子 effect | 上一层 effect 的主体 |

### 280103 金标本来就避开了 V=1

`SkillGraph_280103_【狮妖】连线.json`：
- FOLLOW_ENTITY (28023955) P[1] = V=**37** TCPT_MAIN_CREATOR_ENTITY_ID
- CREATE_BULLET (28023952) P[4] = V=**37**

AI GATE-0.5 读了 280103 但只复制"形态"没问"金标为什么不用 V=1"，错把 SkillConfig 顶层语义直接外推到 BulletConfig 嵌套上下文。

---

## 修复

| 层 | 文件 | 修改 |
|----|------|------|
| 末端 JSON | `SkillGraph_2500001_链状连线指示器.json` | FOLLOW_ENTITY P[1] V=1→V=35 ✓ / CREATE_BULLET P[4] V=1→V=35 ✓ / Desc/Sticky 同步 |
| IR YAML | `doc/SkillAI/samples/ir/链状连线指示器.skill.yaml` | 新增 bind_master/creator: "施法者根" 字段 + r2 修订注释 |
| 编译器 expander | `doc/SkillAI/tools/skill_compiler.py` `expand_bullet_chain` | 默认 entity:主体 → entity:施法者根 / 顶部 Pattern Expander 注释加陷阱说明 / `_make_chain_follow_entity_node` docstring 加注 |
| Lint | `skill_lint.py` | E=0 W=1（无关）|

---

## 预防

### 心智模型新增条目（D-038 候选 / 已落盘 batch_buffer/D-038-...yaml）

**主张本体**：嵌套 SkillEffect 调用栈中 V=1 "主体" ≠ 玩家主角 / 用 V=35 施法者-根创建者拿最初施法者。

**升正式路径**：待累积 ≥3 例（BulletConfig + Buff + RUN_SKILL_EFFECT 各 1 反例 / 用户拍板或 AI 自决 4-gate）。

### memory 速查条建议（待用户拍板）

`reference_nested_main_entity_trap.md` — **配 BulletConfig.BornSE / Buff Effect / 嵌套 SkillEffect 时 V=1 "主体" = 调用栈最近一层主体，不是玩家主角。拿主角必须 V=35 施法者-根创建者**。

### Lint 规则增强建议（future）

`skill_lint.py` 增加 W 级检查：扫描 `BulletConfig.{Before,After,Die}BornSkillEffectExecuteInfo` 内所有 SkillEffect 节点的 Params，若有 V=1/PT=5 出现 → 报 W "嵌套上下文主体=子弹自身 / 是否本意？"

### 编译器其他位置 grep 扫描

`skill_compiler.py` 内所有 `resolve_ref("entity:主体")` 出现位置：

| 行号 | 上下文 | 是否触发陷阱 |
|------|--------|------------|
| 586 | TSKILLSELECT 主体单位 SkillConfig 顶层 select | 否（顶层 = 主角）|
| 813 | Buff source | **是** ⚠️ 待审 |
| 858 | bullet creator (其他子弹模式) | 视上下文 |
| 1390/1404 | 链状指示器 (已修) | 已修 |
| 1509 | bullet creator (其他模式) | 视上下文 |
| 1623 | Effect target | 视上下文 |
| 1809 | follow target | **可能** ⚠️ 待审 |
| 1841 | follow source | **可能** ⚠️ 待审 |
| 1930 | voice_id | 视上下文 |
| 1983/1984/2011 | Buff host/source/target | **是** ⚠️ 待审 |

→ 待 D-038 升正式后 / 跟随用户决策做编译器全员扫描修订。

---

## 相关

- PostMortem #032 — BulletConfig.AfterBorn + REPEAT 铁律（同样揭示 BulletConfig 嵌套调用栈语义陷阱）
- PostMortem #035 — BulletConfig/ModelConfig ID 全工程唯一
- PostMortem #036 — 模板默认值偏离实战
