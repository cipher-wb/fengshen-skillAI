---
type: 心智模型 / 子系统
summary: SkillConditionConfig 用蓝图 TSCT_* 节点直接配，不走 Excel；与 SkillPreConditionConfig 不是同一张表
date: 2026-05-14
tags: [SkillCondition, SkillPreCondition, TSCT, 蓝图配置, 心法注入, 区分铁律]
---

## 概述

**SkillConditionConfig** 是技能内"条件判定"的配置表，用于决定某个 SkillEffect 节点的某个分支或参数是否生效。最常见用例是 `RUN_SKILL_EFFECT_TEMPLATE` 子弹通用逻辑-伤害模板的 `ParamUID 8 = 技能增伤-触发条件`。

**关键反直觉点**：策划**不需要去 Excel 配 SkillConditionConfig.xlsx**——蓝图内的 TSCT_* 条件节点本身就是 SkillConditionConfig 表的一行，NodeEditor 在导出时自动生成表条目。

## 核心概念

### A. SkillConditionConfig = 蓝图内 TSCT_* 节点

| 维度 | 内容 |
|------|------|
| 表 | `SkillConditionConfig.xlsx` |
| TableTash | `ED89F46EAB95F7ACF5C1911A5A375278` |
| 节点 type.class | `TSCT_*`（如 `TSCT_VALUE_COMPARE` / `TSCT_AND` / `TSCT_HAS_BUFF` 等） |
| 节点 data.ID | 该 SkillCondition 在表里的行 ID |
| 节点 data.Config2ID | `SkillConditionConfig_<ID>` |
| 节点 data.SkillConditionType | 节点子类（如 7 = VALUE_COMPARE / 不同类有不同语义）|

**金标样本**：吴波测试 `SkillGraph_301104` rid=1011 / ID=320510 / TSCT_VALUE_COMPARE 节点 + 同蓝图 rid=1010 RUN_SKILL_EFFECT_TEMPLATE.ConfigJson.Params[10]={V:320510, PT:0} 直接引用。

**等效样本**：叶散风行 `SkillGraph_30212010` 新增 rid=1150 / ID=320511 / TSCT_VALUE_COMPARE（2026-05-14 任务）。

### B. RUN_SKILL_EFFECT_TEMPLATE 引用 SkillCondition 的 4 步法

1. 蓝图内新建 1 个 `TSCT_*` 节点（如 TSCT_VALUE_COMPARE 表示"tag X 操作符 op 与 target value 比较"）。
2. TSCT 节点的输入参数（如 P[0] NodeRef → GET_SKILL_TAG_VALUE）通过 **edge 连线** 引入。
3. 在 RUN_SKILL_EFFECT_TEMPLATE 的 ParamUID 8 字段填 `{V:<TSCT 节点 ID>, PT:0}`（注意是字面 ID / 不是 NodeRef）。
4. 用 **RefConfigBaseNode 包装 + edge 连线** 提供视觉跳转（见 §D 铁律 + memory `feedback_skilleditor_refnode_over_id.md`）。

### C. SkillConditionConfig vs SkillPreConditionConfig 严格区分

⭐ **这是两张完全不同的表 / 高频混淆点**：

| 维度 | SkillConditionConfig | SkillPreConditionConfig |
|------|---------------------|------------------------|
| 用途 | 技能内伤害节点增益触发判定 | 心法注入触发条件（决定哪个心法等级注入哪个功法）|
| 引用方 | `RUN_SKILL_EFFECT_TEMPLATE.ParamUID 8 (技能增伤-触发条件)` 等 | `SkillXinfaConfig.ConditionSkills[0] = "条件ID\|心法ID\|心法等级"` |
| 配置方式 | ✅ **蓝图 TSCT_* 节点**（NodeEditor 自动导出）| ❌ **Excel 手动配** |
| TableTash | `ED89F46EAB95F7ACF5C1911A5A375278` | （Excel 表 / 无 TableTash） |

**记忆口诀**：含 "Pre" = "前置" = 心法系统的前置条件 = Excel；不含 "Pre" = 技能内条件判定 = 蓝图。

### D. 配置铁律（综合既有 memory）

1. **TSCT 节点 ID 引用必须包 RefConfigBaseNode**（[memory/feedback_skilleditor_refnode_over_id.md](C:/Users/.../memory/feedback_skilleditor_refnode_over_id.md)）：`RUN_SKILL_EFFECT_TEMPLATE.Params[10]={V:320511, PT:0}` 不能只填数字 / 必须新建 1 个 `RefConfigBaseNode`（`TableManagerName=TableDR.SkillConditionConfigManager` / `data.ID=320511`）+ edge 连到 RST 的 Params[10] 端口。
2. **unique-parent 每个 RefConfigBaseNode 只服务 1 个父**（[memory/feedback_skilleditor_unique_parent.md](C:/Users/.../memory/feedback_skilleditor_unique_parent.md)）：N 个 RST 引用同一个 SkillCondition → N 个 RefConfigBaseNode 包装（不能共享 1 个）。
3. **TSCT_VALUE_COMPARE schema v3**（[memory/feedback_value_compare_schema.md](C:/Users/.../memory/feedback_value_compare_schema.md)）：`P[0]`=NodeRef / `P[1]`=op (1=="==") / `P[2]`=target value。30212010 中 op=1 ("=="); 吴波 301104 中 op=2（不同语义）。
4. **NodeRef (PT=2) 也要 edge 连线**：TSCT_VALUE_COMPARE.P[0]={V:32900281, PT:2} 不能只填数字 / 必须 edge 连线到 GET 节点的 `PackedParamsOutput`。视觉缺连线 = 策划在 SkillEditor 里看不见条件依赖谁。

### E. 数据流图

```
[GET_SKILL_TAG_VALUE 32900281]  读 tag 320957 (寻踪术装备态)
        │ edge (PackedParamsOutput → Params[0])
        ▼
[TSCT_VALUE_COMPARE 320511]    P[0]=NodeRef / P[1]=1 (==) / P[2]=1 (target)
        │ 自身 ID=320511 (= SkillConditionConfig 表行)
        ▼ 通过 RefConfigBaseNode 包装 + edge
[RUN_SKILL_EFFECT_TEMPLATE.Params[10]={V:320511, PT:0}]  ParamUID 8 = 触发条件
```

## 交叉引用

- [[SkillTag系统]] §F 心法注入合并语义 + §F.1 双键映射铁律（涉及 SkillPreConditionConfig 的 Excel 路径，与本页 SkillConditionConfig 是不同表，区分见 §C）
- [[模板系统]] RUN_SKILL_EFFECT_TEMPLATE 子弹通用逻辑-伤害模板 ParamUID 1-13 全字段速查
- [[SkillEditor文件结构]] §A 节点双数组写入铁律 + §C edges 单数组结构

## 源码引用

- 表 schema: `Assets/Scripts/TableDR_CS/Hotfix/Gen/SkillConditionConfigManager.cs`（待 grep 验证字段定义层级）
- 节点 type.class: `Assets/Thirds/NodeEditor/SkillEditor/Nodes/SkillCondition/`（待 grep 验证文件路径）
- 金标样本：`{{SKILLGRAPH_JSONS_ROOT}}宗门技能/废弃（老技能）/SkillGraph_301104【金宗门】吴波测试.json` rid=1010+1011
- 等效样本：`{{SKILLGRAPH_JSONS_ROOT}}宗门技能/木宗门技能/SkillGraph_30212010_【木宗门_AIgen_叶散风行.json` rid=1150 + 1153/1154 (RefConfigBaseNode 包装)

## 待确认 / 疑问

1. **TSCT_VALUE_COMPARE 的 op 编码全集**：schema v3 已知 op=1 (==) / op=2 (吴波样本里在用，但语义不确定，可能是 !=)；其它 op 值如 3/4/5 是否对应 >/</>= 等待源码 grep 验证。
2. **SkillConditionType 枚举全集**：本次实例化 SkillConditionType=7 (VALUE_COMPARE)；其它 type 如 1/2/3/4/5/6/8+ 对应哪些 TSCT_* 类未列表。
3. **是否所有 TSCT_* 节点都自动导出为 SkillConditionConfig 表行**：本次确认 VALUE_COMPARE 是；TSCT_AND / TSCT_OR / TSCT_HAS_BUFF 等其他 TSCT_* 是否同样导出待验证（应该是 / 因为 TableTash 一致）。

## 认知演变

- **v0.1（2026-05-14）首次确立 / B-DESIGNER-叶散风行-寻踪术任务触发**：主对话 GATE-0 时误以为 SkillConditionConfig 必须 Excel 配 / 让用户提出"根本不需要配 Excel 表"反例 / 读吴波样本 SkillGraph_301104 闭环确认蓝图 TSCT 节点 = SkillConditionConfig 表行 / NodeEditor 自动导出机制。
  - 同时澄清 SkillConditionConfig vs SkillPreConditionConfig 区分（高频混淆 / 见 §C）
  - 同时新增 §D 配置铁律 4 条（综合既有 memory）
  - 同时新增 §E 数据流图（叶散风行 30212010 实例锚定）
- 关联沉淀：[postmortem/2026-05-14-042-skillcondition-blueprint-misperception.md](../postmortem/2026-05-14-042-skillcondition-blueprint-misperception.md)（主对话误判根因）+ [postmortem/2026-05-14-043-designer-prompt-iron-rule-burial.md](../postmortem/2026-05-14-043-designer-prompt-iron-rule-burial.md)（agent 选择跟随老惯例 + agent 救场反向 edge）
