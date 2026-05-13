---
proposal_id: 2026-05-08-014
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py（indicator_type_map + _scan 默认值修正）
  - doc/SkillAI/docs/易错点速查.md（待补：TIndicatorType 三层枚举）
related_skill: 30142003 残影火影分身（v2.0 → v2.1，指示器从单体修正为直线）
ir_version: 2.0/2.1
---

# 指示器枚举错配 — TIndicatorType vs TShapeType

## 决策
✅ **入库 v2.0 → v2.1 修正**

## 现象
v2.0 的 30142003 残影火影分身 IR 写 `indicator.type: 直线`，编译产物 `SkillIndicatorType=2`。

用户报告："指示器不对，你做的不是直线，而是单目标"。

实测验证 SkillIndicatorType 的真实枚举：
```
TIndicatorType:
  TIRT_NULL = 0      （无目标 — 类似自身 buff）
  TIRT_NULL = 1      （历史保留位）
  TIRT_TARGET = 2    （单目标）       ← v2.0 错误地映射给"直线"
  TIRT_LINE = 3      （直线）          ← 正确值
  TIRT_DOUBLE_CIRCLE = 4  （双圆）
  TIRT_FAN = 5       （多向 / 扇形）
```

我的编译器 indicator_type_map 用的是早期凭空记忆的映射（"直线": 2），实际 2 是单目标。

## 根因
**未做 GATE-0.5 §3 三层校对就用枚举值**。这是 PostMortem #008/#009 同款坑的复发：

1. PostMortem #008/#009 的教训：调用模板前要 dump TemplateParam 的 RefTypeName，再去 common.nothotfix.cs 查实际枚举值
2. 我把规则只应用到"模板调用"层面，没扩展到"SkillConfig 的所有枚举字段"
3. SkillIndicatorType 是 SkillConfig 自己的字段，不是模板参数，但同样需要查 enum

## 修法（已落地）
1. `skill_compiler.py` 的 `indicator_type_map` 改为基于真实 TIndicatorType：
   ```python
   indicator_type_map = {
       "无目标": 1, "单目标": 2, "直线": 3,
       "圆形": 4, "扇形": 5, "矩形": 5,  # 双圆/多向
   }
   ```
2. `_scan` 自动推断默认值修正：
   - bullet step → 3（直线，原来是 2）
   - aoe_circle step → 4（双圆，原来是 3）
3. 30142003 v2.1 编译产物：SkillIndicatorType=3 + SkillIndicatorParam=[500] ✓

## 利
- 修正了与 PostMortem #008/#009 同源但作用域不同的坑（模板参数 vs SkillConfig 字段）
- 编译器现在对 SkillConfig 枚举字段也有"真实枚举值"约束

## 弊
- 全项目还有多少类似的"凭记忆映射"，需要全面扫一次（比如 TBattleSkillSubType / TElementsType / TSkillColdType 是否也有错）

## 噪音风险
低 — 这是数据正确性硬错误，不可能是误报

## 推广动作（待团队评估）
1. 把"GATE-0.5 §3 三层枚举校对"的适用范围从"模板参数"扩到"SkillConfig 全字段"
2. 在 docs/易错点速查.md 加一节列出 SkillConfig 用到的所有枚举类型 + 真实值表
3. skill_lint.py 增加规则 E020：枚举值越界检查
