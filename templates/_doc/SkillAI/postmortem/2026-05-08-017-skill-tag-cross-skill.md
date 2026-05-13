---
proposal_id: 2026-05-08-017
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py（BuildCtx +parent_skill_id / expand_return_to_clone 用 GET_SKILL_TAG_VALUE 跨技能读 / _split_two_stage 设置 parent_skill_id 并去掉 second_ir.tags）
  - doc/SkillAI/samples/ir/30142003_shadow_phoenix_draft.skill.yaml（显式 tags 声明 + tag ID 改为 skill_id*100 命名约定 + return 速度 3000）
  - doc/SkillAI/docs/易错点速查.md（待补：SkillTag 跨技能读取必填 source_skill_id）
related_skill: 30142003 残影火影分身（v2.2 → v2.3）
ir_version: 2.3
---

# SkillTag 跨技能读取必填 source_skill_id（v2.3）

## 决策
✅ **入库 v2.3**

## 现象（用户实测 v2.2 后反馈 3 个问题）

> 1. 你在第一段储存位置的时候，32003010 和 32003011 这两个节点，你需要存在当前技能的tag中，你需要新建tag！我看你没有新建，自己随便填了一个tagID 是不行的
> 2. 在第二段回来的时候，你要把x和y获取第一段（第一个技能）的tag值，注意 tag 是和技能绑定的！我们所有变量都是和技能绑定的，你获取tag的时候要填写第一个技能的技能ID！
> 3. 回来速度太慢了，回来速度改成 3000

## 根因

### #1 SkillTag 必须显式声明 + 命名约定
v2.2 我用了"320200/320201"两个凭空捏造的 tag ID，**没有生成 SkillTagsConfigNode 声明节点**。运行时引擎按 tag ID 查表，没找到声明节点，可能：
- 写不进去（MODIFY 操作 silent fail）
- 或写到了"未声明区"，第二段读不到

PostMortem #014 同源教训："不能凭记忆映射"——这次扩到 tag ID 命名也一样，**不能凭空选数字**。

### #2 SkillTag 是 skill-bound，跨技能必须显式 skill_id
v2.2 我用 `tag:N` (PT=3 SKILL_PARAM Value=N)，运行时这等价于 `TSET_GET_SKILL_TAG_VALUE([caster, current_skill, tag, ...])`，**会从 30142004（第二段）的 tag 表读取**——但 tag 是写在 30142003（主）的 tag 表上的。第二段的 tag 表里 320200 是空的，读出 0，所以飞回到 (0,0) 位置。

**正解**（参考 30221002 rid=1019 真实样本）：用显式 `TSET_GET_SKILL_TAG_VALUE([3/PT=5 caster, <主技能ID>/PT=0, tag/PT=0, 1, 0])`。Param[1] 必须填**主技能 ID**（30142003），不能省略也不能用 PT=3 简化糖。

### #3 速度太慢
v2.2 写 150（cm/帧 @ 30fps = 4500 cm/秒 = 45m/秒），实测体感慢。用户要 3000（cm/帧 @ 30fps = 90000 cm/秒 ≈ 900m/秒，瞬间到位）。

## v2.3 修法（已落地）

### 1. 显式 SkillTag 声明
```yaml
# IR
tags:
  - {id: 3014200301, name: "残影位置X", default: 0, retain_when_die: false}
  - {id: 3014200302, name: "残影位置Y", default: 0, retain_when_die: false}
```
- 命名约定 `skill_id * 100 + offset`：避开全局已用区（30221000 用 22500xx）+ 一眼识别归属技能
- 编译产物：30142003 多出 2 个 SkillTagsConfigNode（rid=新增）

### 2. 跨技能读 tag — 显式 source_skill_id
```python
# expand_return_to_clone v2.3
source_skill_id = cfg.get("source_skill_id") or ctx.parent_skill_id  # _split_two_stage 已设
get_tag_x = _make_get_skill_tag_value_node(source_skill_id, base_tag,     ...)
get_tag_y = _make_get_skill_tag_value_node(source_skill_id, base_tag + 1, ...)
# 飞回位移 Param[1]/[2] 改用 effect_return 链接到 GET_SKILL_TAG_VALUE
```
- 编译产物：30142004 多出 2 个 TSET_GET_SKILL_TAG_VALUE，Params 形如 `[3/PT=5, 30142003/PT=0, 3014200301/PT=0, 1, 0]`
- 飞回位移 Param[4] X / Param[5] Y 由 PT=3 改为 PT=2 effect_return

### 3. 速度
IR `return_to_clone.speed: 3000`（v2.2 是 150）

### 4. 架构补充：`_split_two_stage` 自动注入 parent_skill_id
```python
# v2.3
results.append(...)  # main
second_ctx = _compile_single(second_ir, second_path, parent_skill_id=main_id)
```
+ `BuildCtx.parent_skill_id: int | None`
+ second_ir 自动 `pop("tags")` —— 第二段不重复声明，只跨技能读

## 验证

```
30142003 v2.3:
  23 节点 / 22 边 / 0 孤立 / Lint E=0 W=1
  ✓ 2 个 SkillTagsConfigNode (3014200301/3014200302)
  ✓ MODIFY tag=3014200301 value=PT=2 (effect_return ← GET_ATTR 位置X=59)
  ✓ MODIFY tag=3014200302 value=PT=2 (effect_return ← GET_ATTR 位置Y=60)
  ✓ 44014633 切槽位 Param[4]=PT=2 effect_return ← GET_SKILL_SLOT_TYPE（动态）
  ✓ 44014633 切槽位 Param[5]=30142004（第二段独立 SkillConfig）

30142004 v2.3:
  9 节点 / 8 边 / 0 孤立 / Lint E=0 W=0 / cd=30
  ✓ 0 SkillTagsConfigNode（不重复声明）
  ✓ 2 GET_SKILL_TAG_VALUE：[3/PT=5, 30142003/PT=0, 3014200301/PT=0, 1, 0] / [3, 30142003, 3014200302, 1, 0]
  ✓ 飞回位移 Param[3]=3000（速度），[4]=PT=2 effect_return X，[5]=PT=2 effect_return Y
```

## 利
- 真正的"跨技能 SkillTag 通信"机制落地（v2.1/2.2 都是错的）
- IR 显式 tags 声明 + 跨技能 source_skill_id 自动推导，用户写两段技能不再需要懂底层
- 30142004 节点数 7 → 9（仅 +2 GET_SKILL_TAG_VALUE，开销可接受）

## 弊
- IR 用户必须知道"tag 命名约定 skill_id * 100 + offset"——文档化，否则其他策划又会乱选 ID
- 当前实现：source_skill_id 必须可推导（在 second_stage 上下文里）；如果用户在普通 flow 里用 return_to_clone（无 two_stage_skill 包裹），会报错"需要 source_skill_id"

## 噪音风险
低 — 三个修复都对应明确 Unity 实测 bug + 用户提供的真实参考实现（30221000/30221002）

## 三轮版本演进表
| 版本 | first_stage 存位置 | second_stage 读位置 | 速度 | 槽位 | CD |
|---|---|---|---|---|---|
| v2.0 | × 不存 | × `attr:位置X/Y`(caster 当前) | 100 | 写死神通 | 继承 360 |
| v2.1 | × 仅 stub | × 同 v2.0 | 100 | 同 v2.0 | 继承 360 |
| v2.2 | ✓ MODIFY tag X/Y（但 tag 未声明 + ID 凭空） | ✗ `tag:N` PT=3（current skill 读不到） | 150 | ✓ 动态 GET_SKILL_SLOT_TYPE | ✓ 30 帧 |
| **v2.3** | ✓ 声明 + MODIFY 完整 | ✓ GET_SKILL_TAG_VALUE 显式 source_skill_id | **3000** | ✓ 同 v2.2 | ✓ 同 v2.2 |

## 推广动作
1. 速查文档加："SkillTag 跨技能读取 = 必须显式 skill_id；同技能内可省略；命名约定 skill_id * 100 + offset"
2. skill_lint.py 新规则：
   - E023：MODIFY/GET_SKILL_TAG_VALUE 引用的 tag_id 必须能在 SkillTagsConfigNode 列表中找到（同 JSON 内）或属于已知声明的其他 skill
   - E024：如果 SkillEffectConfig 中出现 PT=3 SKILL_PARAM（tag:N 引用），警告"建议改用 GET_SKILL_TAG_VALUE 显式 skill_id"

## Unity 实测预期（v2.3）
1. ✅ 第一段：召唤残影 + 高速位移 + **位置存到 30142003 的 tag 3014200301/3014200302**
2. ⚠️ 切槽位至 30142004（动态槽位，应自动适配 caster 当前装备槽）
3. ⚠️ 玩家再按同一按钮触发 30142004（CD=30 帧）
4. ⚠️ 30142004 飞回 — **跨技能读 30142003 的 tag**，速度 3000
5. ⚠️ 落地 AOE PoC（仍 v2.0 单目标简化，等 v2.4 改真 AOE）
