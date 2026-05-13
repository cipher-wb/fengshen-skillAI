---
proposal_id: 2026-05-08-003-A
status: accepted
sediment_target:
  - doc/SkillAI/docs/易错点速查.md §11（重写）
  - doc/SkillAI/PRD.md §4.3.2（同步 explosion 语义）
  - doc/SkillAI/tools/skill_compiler.py（重设计 + _make_quick_damage_node 标 deprecated）
related_skill: 30142001 火焰追踪弹幕（v1.1.1 修正后实测验证）
---

# 提案 A：explosion 设计认知错误 — 子弹通用碰撞模板的 collision_radius 已是 AOE

## 决策
✅ **入库**（自动执行：修正性沉淀，不是新增）

## 新规则
子弹通用-碰撞模板（190016404）的 `collision_radius` 是 **AOE 检测半径**，范围内每个目标都各调用一次伤害模板（**天然多目标**）。**不需要额外的 QUICK_DAMAGE 节点造"AOE 范围伤害"**。

## 现象
战斗策划实测 30142001 火焰追踪弹幕，质问："为什么已经有伤害结算模板了，你还配了一个快速伤害结算节点？"

## 根因
v1.1 设计 explosion 时，AI 未深入理解碰撞模板的工作机制，误以为：
- 直伤模板 = 命中目标的单体伤害
- QUICK_DAMAGE 节点 = AOE 范围伤害

实际机制：
- 碰撞模板的 `collision_radius` 已经是 AOE 检测半径
- 范围内每个目标都各调用一次伤害模板（天然 AOE）
- 加 QUICK_DAMAGE 是冗余 → 一次命中造**双份伤害**（直伤 + QUICK 各一份）

## 解决方式
v1.1.1 设计修正 — explosion 改为"语义糖"：
- `explosion.radius` → 映射到 `collision_radius`（AOE 检测半径）
- `explosion.damage` → **覆盖** hit.damage 的参数（爆炸量取代直伤量）
- 不再生成额外 QUICK_DAMAGE 节点
- `_make_quick_damage_node` 函数标 `[DEPRECATED in v1.1.1]`，保留供其他 builder 直接需要时使用

修正前：节点数 19，命中 ORDER 串 [伤害模板, QUICK_DAMAGE, ADD_BUFF, 表现模板]
修正后：节点数 18，命中 ORDER 串 [伤害模板, ADD_BUFF, 表现模板]

## 利
- 节点数减少（少 1 个 QUICK_DAMAGE）
- 数值评估不会双计
- 正确利用项目模板能力（不画蛇添足）

## 弊
- v1.1 已生成的 IR 文件需要重新理解（hit.damage 优先级低于 explosion.damage）
- _make_quick_damage_node 暂保留（deprecated 但未删），代码冗余 1 个函数

## 噪音风险
低 — 设计修正后语义更直观

---

# 提案 B：单目标指示器 SkillIndicatorParam 应为空数组

## 决策
✅ **入库**

## 新规则
SkillIndicatorParam 按 SkillIndicatorType 分类填值：
| Type | 含义 | Param |
|------|------|-------|
| 0 | 无目标 | `[]` |
| 1 | 单体 | `[]` |
| 2 | 直线 | `[range]` |
| 3 | 圆形 | `[range]` |
| 4 | 扇形 | `[range, angle]` |
| 5 | 矩形 | `[width, height]` |

填错（如单体填 `[800]`）会导致编辑器报指示器异常。

## 现象
30142001 编译产物 SkillIndicatorType=1 SkillIndicatorParam=[800]，用户实测报"指示器类型不对"。

## 根因
`make_skill_config_node` 的 `indicator_param` 推断逻辑过于粗糙：
```python
indicator_param = [skill.get("range", 0)] if indicator_type_int else []
```
所有 type≠0 都填 `[range]`，单体 (type=1) 被错误塞了 800。

## 解决方式
- `make_skill_config_node` 按 type 分类生成 indicator_param（已实施）
- 速查表加 §12（已沉淀）

## 利
- 编译器自动正确
- 团队其他策划手配时知道规则

## 弊
- 速查表多 1 条

## 噪音风险
低 — 项目通用规则，频率高

---

# 提案 C：技能时长规则 cast_frame ≤ base_duration ≤ cd_time + Lint 护栏

## 决策
✅ **入库（速查 + Lint 双重）**

## 新规则
SkillCastFrame（出手帧）≤ SkillBaseDuration（基础时长）≤ CdTime（CD）。否则编辑器报"技能时间不符合规则"。

## 现象
30142001 配置 cast=24/bd=20，编辑器报错。AI 之前不知道这条规则，写了违规配置。

## 根因
SkillEditor 内部时长校验：出手帧不能超出基础时长（不然技能动画结束时还没出手），基础时长不能超 CD（不然技能本身比 CD 长）。

## 解决方式
1. **Lint 护栏**：修正 E013 规则
   - 旧逻辑 bug：检查 `cast > buf_start AND buf_start > 0`，buf_start=0 时跳过 → 漏报
   - 新逻辑：直接检查 `cast > base_duration` 和 `base_duration > cd_time`
   - 反向测试：故意构造 cast=24/bd=20 的 JSON，E013 正确捕捉 ✓
2. **速查表 §13**：写明规则 + 真实样本参考值

## 利
- 自动护栏 + 文档双重防御
- 反向测试证明 lint 能捕捉

## 弊
- Lint 规则增加 — 但 E013 已存在，是修复而非新增

## 噪音风险
低 — Lint 只在违规时报错

---

# 三提案综合

| 提案 | 沉淀位置 | 状态 |
|---|---|---|
| **A** explosion 设计修正 | 速查§11 重写 + PRD§4.3.2 同步 + 编译器 deprecated 标记 | ✅ |
| **B** 指示器 param 按 type 分类 | 速查§12 + 编译器修正 | ✅ |
| **C** 时长规则护栏 | 速查§13 + Lint E013 修正（反向测试通过） | ✅ |
