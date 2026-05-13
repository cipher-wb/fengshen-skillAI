---
proposal_id: 2026-05-08-019
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py（_make_record_caster_position_nodes 改 Pattern B / _make_get_skill_tag_value_node 去掉 source_skill_id 参数 / expand_return_to_clone 不再依赖 ctx.parent_skill_id）
  - doc/SkillAI/docs/易错点速查.md（待补：SkillTag 实体级 vs 技能级）
related_skill: 30142003 残影火影分身（v2.3.1 → v2.3.2）
ir_version: 2.3.2
---

# SkillTag 实体级 vs 技能级 — Param[1]=0/PT=0 是"挂在人物身上"

## 决策
✅ **入库 v2.3.2**

## 现象（用户最后一条修改要求）

> "记录坐标的这两个 tag，他的技能ID不应该填写技能ID，应该类型是"-"，数值是0，这就意味着这个 tag 是存在人物身上而不是技能身上，写入和读取都要这么改，这样就可以跨技能读取"

## 根因

SkillTag 在引擎里有两种作用域：
| 模式 | Param[1] | 含义 | 跨技能读取 |
|---|---|---|---|
| **技能级** | `<skill_id>/PT=0` 或 `41/PT=5`（初始技能实例） | tag 挂在 (entity, skill_inst) 复合 key 上 | ❌ 必须显式填 source_skill_id |
| **实体级** | **`0/PT=0`（"-" 类型）** | tag 只挂在 entity 上，无技能 scope | ✅ 任何技能都能直接读 |

PostMortem #017 我以为"tag 必须 skill-bound"是硬规则，给 GET_SKILL_TAG_VALUE 写了 `[skill_id/PT=0]`。但回看 30221000/30221002 的 8 个 MODIFY 调用：
- 5 个用 Pattern A `[V=4/PT=5, V=41/PT=5]` — 技能级（绑初始技能实例）
- 3 个用 Pattern B `[V=3/PT=5, V=0/PT=0]` — **实体级**（"-" 类型）

这两个 Pattern 在不同场景用：需要"私有给本技能"的 tag 用 A；需要"跨技能共享"的状态用 B。**位置存储是典型的跨技能场景，应该用 B。**

## 修法（已落地）

### MODIFY（v2.3 → v2.3.2）
```
v2.3:    [V=4/PT=5,  V=41/PT=5,         V=tag,        V=value/PT=2, V=1]   # 技能级
v2.3.2:  [V=3/PT=5,  V=0/PT=0,          V=tag,        V=value/PT=2, V=1]   # 实体级（"-"）
              caster      "-" 类型 = 0
```

### GET（v2.3 → v2.3.2）
```
v2.3:    [V=3/PT=5,  V=<source_skill>/PT=0, V=tag,    V=1, V=0]    # 技能级（需 parent_skill_id）
v2.3.2:  [V=3/PT=5,  V=0/PT=0,              V=tag,    V=1, V=0]    # 实体级
              caster   "-"
```

### 代码层简化
- `_make_get_skill_tag_value_node` 去掉 `source_skill_id` 参数
- `expand_return_to_clone` 不再读 `ctx.parent_skill_id`（虽然 BuildCtx 字段保留兼容其他场景）
- 第二段编译变得更简单：不需要知道第一段的 skill_id

## 验证
```
30142003 (写):
  rid=1014 entity=V=3/PT=5 skill=V=0/PT=0 tag=301420030
  rid=1015 entity=V=3/PT=5 skill=V=0/PT=0 tag=301420031

30142004 (读):
  rid=1005 entity=V=3/PT=5 skill=V=0/PT=0 tag=301420030
  rid=1006 entity=V=3/PT=5 skill=V=0/PT=0 tag=301420031

✓ 写入和读取的 (entity, skill) 完全对称
✓ Lint E=0 W=1 / E=0 W=0
✓ 节点数 23 / 9（与 v2.3.1 持平）
```

## 利
- **真正的跨技能透明读取**：第二段无需知道第一段的 skill_id，编译产物更通用
- 编译器代码减少 ~10 行（去掉 source_skill_id 参数 + 报错分支）
- 与 30221000 真实样本 Pattern B 完全一致

## 弊
- v2.3 PostMortem #017 写"必须填 source_skill_id"是错的（基于不完整观察），需要 **撤回** + 改为"分两种 tag 模式，位置存读用实体级"
- BuildCtx.parent_skill_id 字段保留但本次未使用（可能未来某些场景需要技能级 tag 时再启用）

## 噪音风险
低 — 用户明确告知正确做法，且 30221000 真实样本中 Pattern B 已存在

## SkillTag 两种模式的选用准则（团队级）
| 用途 | 推荐模式 | 例子 |
|---|---|---|
| 跨技能共享状态（位置/计时器/敌人 ID） | **实体级 (Pattern B)** `[3/PT=5, 0/PT=0]` | 残影位置、连招计数、关联敌人 |
| 私有给本技能的内部计算（伤害累计/buff 层数） | 技能级 (Pattern A) `[4/PT=5, 41/PT=5]` | 暂未在 IR 编译器使用 |
| 简化情况：永远是当前 caster 当前 skill | 任意（默认实体级更简单） | — |

**经验法则**：除非明确需要"同 entity 不同 skill 的 tag 隔离"，否则用实体级。

## 历史四轮 Tag 演进表
| 版本 | MODIFY Param[1] | GET Param[1] | 跨技能读 | 备注 |
|---|---|---|---|---|
| v2.0/2.1 | （未实现） | （未实现） | × | 仅 stub |
| v2.2 | 41/PT=5（技能级） | 隐式 PT=3 SKILL_PARAM | × 读不到 | tag 未声明 |
| v2.3 | 41/PT=5（技能级） | source_skill/PT=0（技能级） | ✓ 但需 parent_skill_id | 复杂、tag ID 溢出 int32 |
| v2.3.1 | 同 v2.3 | 同 v2.3 | ✓ 同 v2.3 | 仅修 int32 溢出 |
| **v2.3.2** | **0/PT=0（实体级）** | **0/PT=0（实体级）** | ✓ 透明 | 简化、对称 |

## 推广动作
1. docs/易错点速查.md 加 §"SkillTag 实体级 vs 技能级"，附四轮演进表 + 选用准则
2. memory/feedback_skill_compiler_pitfalls.md 加："位置/状态等跨技能 tag 一律用实体级 Param[1]=0/PT=0"
3. skill_lint.py 新规则 W005：MODIFY/GET_SKILL_TAG_VALUE 的 Param[1] 如果是 PT=0 非 0 / PT=5 = 41，提示"考虑改成实体级 [3/PT=5, 0/PT=0]"

## Unity 实测预期（v2.3.2）
1. ✅ 30142003 第一段：caster 位置 X/Y 写入实体级 tag 301420030/031
2. ✅ 切槽位至 30142004
3. ✅ 30142004 第二段：从同 entity 的 tag 301420030/031 直接读出 X/Y
4. ✅ 飞回到记录的位置（速度 3000）
