---
proposal_id: 2026-05-08-015
status: accepted
sediment_target:
  - doc/SkillAI/tools/ir/ir_schema.json (two_stage_skill 升 v2.1 增加 second_stage_skill_id 等字段)
  - doc/SkillAI/tools/skill_compiler.py (KNOWN_TEMPLATES + 修改单位槽位 / expand_two_stage_skill 重写 / compile_ir 改多 SkillConfig 输出)
related_skill: 30142003 残影火影分身（v2.0 失败 → v2.1 重做）
ir_version: 2.1
---

# 两段式按键 ≠ 175_0102 技能连招(2段) — 真机制是 44014633 切槽位

## 决策
✅ **入库 v2.1**：架构级变更（编译器从单 JSON 改多 JSON 输出）

## 现象
v2.0 30142003 用 175_0102 技能连招(2段) 模板做"两段式按键"。用户实测："再次按下技能不能返回"。

## 根因（深度逆向 30221000【金宗门】奇术1 后发现）
175_0102 技能连招(2段) 的 TemplateParam 是这样的：
- [0] 连招 1 段 SkillEffectConfig
- [1] 1-2 间隔时间（帧数）
- [2] 连招 2 段 SkillEffectConfig
- [3] 2-1 间隔时间（帧数）

它的内部实现是 **TSET_ORDER_EXECUTE → DELAY → TSET_ORDER_EXECUTE**——也就是"自动连段"：第一段跑完，等 N 帧，自动跑第二段。**不是按键判断**。

真正的"两段式按键"在项目里是这样实现的（30221000 调用链）：
1. 主技能 30221000 = 第一段（位移 + 召唤残影）
2. 第二段是**独立的 SkillConfig 30221002**（飞回 + AOE）
3. 30221000 末尾调 **44014633 修改单位槽位模板**：把当前槽位（奇术1）的技能 ID 从 30221000 替换成 30221002
4. 玩家**再按同一个按钮**，按下的"奇术1"槽位现在挂的是 30221002，所以触发的是第二段
5. 持续时间到了或第二段释放完，槽位自动还原回 30221000

44014633 模板 7 个 TemplateParam：
- [0] 单位ID
- [1] 技能槽位 (TSkillSlotType: 1=功法 / 2=奇术1 / 3=奇术2 / 4=神通 / 5=额外1)
- [2] 技能ID (替换为哪个 SkillConfig)
- [3] 技能等级
- [4] 持续时间
- [5] 切回原始技能时返还百分比CD
- [6] 显示修改后技能的持续时间UI

## v2.1 架构变更

### 1. IR Schema (step_two_stage_skill)
新增字段：
- `second_stage_skill_id` — 第二段独立 SkillConfig ID（默认 = 主 ID + 1）
- `second_stage_skill_name` — 第二段技能名（用于 JSON 文件名）
- `swap_slot` — 槽位类型枚举（不写则按 sub_type 自动推断：神通→4 / 奇术→2 / 功法→1）
- `swap_cd_refund_pct` — 切回返还百分比CD（默认 100）
- `swap_show_ui` — 显示 UI（默认 true）

`state_tag_id` 字段保留但标注为 v2.0 历史兼容字段，v2.1 不再使用。

### 2. 编译器（skill_compiler.py）
- 新增 `修改单位槽位` 模板到 KNOWN_TEMPLATES（root_effect_id=44014633）
- `expand_two_stage_skill` 重写：first_stage 内联 + 末尾追加 44014633 切槽位调用
- `compile_ir` 从单 SkillConfig 输出改为**多 SkillConfig 输出**：返回 `[(graph, ctx, path), ...]`
- 新增 `_split_two_stage()` 在编译前提取 second_stage 为独立 IR（深拷贝主 IR + 改 meta + 替换 flow）
- main() 循环写盘所有产物

### 3. 30142003 实测产物
```
SkillGraph_30142003_残影火影分身.json:
  14 节点 / 13 边 / 0 孤立 / Lint E=0 W=1
  主流程：cast_anim → ORDER[召唤残影 → 位移 → 切槽位至 30142004]

SkillGraph_30142004_残影火影分身_第二段.json:
  7 节点 / 6 边 / 0 孤立 / Lint E=0 W=0
  主流程：return_to_clone(飞回) + aoe_circle(落地 AOE)
```

44014633 切槽位调用 wired：单位=施法者(3) / 槽位=神通(4) / 第二段ID=30142004 / 持续600帧 / CD返还100%

## 利
- IR 现在支持真正的"两段式按键"——一个 yaml 文件输出两个 JSON
- 这是 PoC → 工业化的拐点：技能内嵌"独立 SkillConfig 关系"被 IR 抽象屏蔽
- 后续类似需求（三段、更复杂的按键变化）可以直接扩展 second_stage_skill_id 为 next_stage_skill_id 链

## 弊
- v2.1 PoC 简化：技能等级写死 1，不读当前等级（30221000 实战用了 GET_INIT_BASE_SKILL_LEVEL 节点）
- swap_slot 默认推断仅支持 5 种 sub_type（功法/奇术1/奇术2/神通/额外1），其余需要显式写
- second_stage 与主 SkillConfig **共享 SkillTags** 假设 SkillTag 是 entity-level（非 skill-scope），需 Unity 实测确认

## 噪音风险
中 — 架构改动比较大，需要后续 5+ 个两段技能验证才能稳定

## v2.2 计划补的局限
| 局限 | v2.2 补法 |
|---|---|
| 等级写死 1 | 加 GET_INIT_BASE_SKILL_LEVEL 引用，编译为 PT=2 effect_return |
| 持续时间写死 | 改 PT=2 effect_return 链接到 GET_SKILL_CD 等节点 |
| 槽位推断不够全 | 完善 _SUB_TYPE_TO_SLOT 表 + 用户白名单 |
| 三段、四段未支持 | second_stage 内嵌另一个 two_stage_skill（递归编译） |

## Unity 实测预期
1. ✅ 直线指示器 type=3 + range=500
2. ✅ 第一段：召唤残影 + 高速位移
3. ⚠️ 切槽位（最大风险点）：施法后玩家"神通"按钮上的图标/技能切换为 30142004？需要 Unity 实测
4. ⚠️ 玩家再按神通按钮触发 30142004（第二段：飞回 + AOE）
5. ⚠️ 600 帧（20 秒）后槽位自动还原为 30142003

实测后预期会有 2~4 处需要调整 → 进入下一轮 PostMortem。

## 推广动作
1. 把"两段式按键 = 44014633 切槽位"写入 docs/易错点速查.md（团队级共享）
2. memory/feedback_skill_compiler_pitfalls.md 加一条："IR 多 SkillConfig 输出已是 v2.1 标配"
3. skill_lint.py 加规则 E021：检查 44014633 调用的 [5] 技能ID 必须指向同目录已存在的 SkillGraph_*.json
