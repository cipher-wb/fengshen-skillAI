---
type: PostMortem
date: 2026-05-14
tags: [SkillCondition, mental_model 盲点, GATE-0, 反例驱动, 用户纠正]
summary: 主对话 GATE-0 时误以为 SkillConditionConfig 必填 Excel / 让用户多绕一轮 / 根因 = mental_model 没记蓝图配置法 + 没主动 grep 样本验证
---

# #042 — SkillConditionConfig 误判 Excel 必填

## 现象

策划任务：给叶散风行加"寻踪术装备时所有子弹命中 +10 条件附加伤害"。

主对话 GATE-0 提问 Q4 时给出选项：
- 方案 A：完全靠 SkillTag 值控制（无 SkillCondition）
- 方案 B：用 SkillConditionConfig 显式判定（**主对话原文**："要在 SkillConditionConfig.xlsx 新增一条 / 策划要配表"）

策划选 B，主对话继续追问 Q5："SkillCondition 这条 ID 你来配 / 还是要我用 xlsx skill 帮你配？"

**策划纠正**："根本不需要配 excel 表！你理解错了，skillcondition 完全可以用蓝图来配。大体个结构和逻辑你可以参考一下 SkillGraph_301104【金宗门】吴波测试"。

读吴波样本闭环：rid=1011 TSCT_VALUE_COMPARE 节点 ID=320510 / TableTash=`ED89F46EAB95F7ACF5C1911A5A375278`（= SkillConditionConfig 表哈希）/ 同蓝图 rid=1010 RUN_SKILL_EFFECT_TEMPLATE.Params[10]={V:320510, PT:0} 直接引用——**蓝图内 TSCT_* 节点 = SkillConditionConfig 表行 / NodeEditor 自动导出 / 不需要 Excel**。

## 根因

1. **mental_model 盲点**：本工程 mental_model 当时（v0.16.41）没有 SkillCondition 子系统页 / SkillTag系统.md §F 只提了 SkillPreConditionConfig（心法注入触发条件 / Excel 配）/ 让主对话误以为所有 "Skill...Condition..." 都是 Excel 表。
2. **GATE-MENTAL-IN 失守**：主对话开工前应该输出"对子系统 X 的当前理解 / 不确定点" / 当时主对话直接跳进 GATE-0 提问环节 / 没显式自问"SkillConditionConfig 怎么配？我有把握吗？" / 也没主动 grep 工程现有 RUN_SKILL_EFFECT_TEMPLATE.ParamUID 8 的实际填法（grep 任一现有 RST 节点的 Params[10] 都能立刻看到是直接填数字 ID = 蓝图配置）。
3. **概念命名混淆**：SkillConditionConfig vs SkillPreConditionConfig 名字相似 / mental_model §F 只描述了后者 / 主对话脑补认为两者同源 / 实际是两套独立机制。

## 影响

- 多绕 1 轮 GATE-0 提问（Q5"谁来配 Excel"是错的方向 / 浪费一次对话往返）
- 用户重新教育成本
- 信任损耗：策划"我记得之前你沉淀过这个知识，怎么忘记了？"（实际本次是 SkillCondition 没沉淀 / 但触发用户对 AI 沉淀质量整体怀疑）

## 修复

1. **新建 mental_model 子系统页** [SkillCondition系统.md](../mental_model/SkillCondition系统.md)：
   - §A SkillConditionConfig = 蓝图 TSCT_* 节点 / NodeEditor 自动导出 / TableTash 一致
   - §C SkillConditionConfig vs SkillPreConditionConfig 严格区分（记忆口诀：含 "Pre" = 心法系统前置 = Excel；不含 = 技能内 = 蓝图）
   - §E 数据流图（叶散风行 30212010 实例锚定）
2. **修订 SkillTag系统.md §F.1**：交叉引用新 SkillCondition系统.md / 防止下次再混淆两表。

## 防御（主对话 GATE-0 流程改进）

| 触发场景 | 必做动作 |
|---------|--------|
| 任务涉及"SkillCondition*"字眼 | 立即 grep 工程现有节点的实际填法（不要凭 mental_model 记忆）/ 再回 mental_model 对照 |
| 任务涉及表名 / 配置项 / 自己说"必须配 Excel"时 | grep 1 个现网样本验证 / 不假设 / 0 grep 不下结论 |
| GATE-MENTAL-IN 输出时 | 显式列"对 X 子系统的当前理解 / 不确定的地方" / 把"不确定的地方"作为 grep 触发条件 |

## 思想史保留

- 主对话 Q4 选项 B 描述里"要在 SkillConditionConfig.xlsx 新增一条" → **保留作反面教材** / 不删除 / rule_2 严守 / 警示后续工作不要凭脑补判断表归属
- 主对话 Q5 提问全文 → 保留 / 警示"问错问题比答错问题代价更大"
