---
proposal_id: 2026-05-08-008
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py (expand_bullet_boomerang collision params)
  - doc/SkillAI/docs/易错点速查.md §15 (子弹通用-碰撞模板参数详解)
related_skill: 30142002 环刃归心 v1.2.2
---

# 子弹通用-碰撞模板参数语义没读全 — "跟随创建者飞行" 的坑

## 决策
✅ **入库**

## 用户反馈（实测）
1. 碰撞依旧是矩形（要圆形 r=500）
2. 子弹飞回人身边过一会才消失
3. **子弹发射出去后跟随人物移动，应该独立飞行**

## 根因 — `子弹通用-碰撞` 模板第 9 个参数（"是否跟随创建者飞行"）= 1

### 模板真实参数定义（13 个 TemplateParams）

```
[0] 命中后功能          → Params[3]
[1] 碰撞范围类型        → Params[4]   1=圆形 / 2=矩形 / 3=多边形 / 4=扇形
[2] 参数1（圆形:半径）  → Params[5]
[3] 参数2               → Params[6]
[4] 参数3               → Params[7]
[5] 位置偏移右          → Params[8]
[6] 位置偏移前          → Params[9]
[7] 目标单位类型        → Params[10]
[8] 自定义条件          → Params[11]
[9] 是否跟随创建者飞行  → Params[12]  ⚠️ 关键
[10] 侦测间隔           → Params[13]
[11] 侦测冷却           → Params[14]
[12] 侦测次数           → Params[15]
```

### 关键参数 [9]"是否跟随创建者飞行"语义

- **= 1**：子弹的 **AOE 检测范围**绑定在创建者（施法者）身上，子弹本体可能独立飞行，但**侦测范围**永远跟在创建者周围
- **= 0**：AOE 检测范围跟随子弹本体位置，与创建者位置无关

### 视觉与语义错位（用户的"矩形"困惑）

我之前 follow_creator=1，导致：
- 子弹本体一圈飞出（视觉对）
- 但 AOE 圆形范围跟在主角身上（看起来像主角周围有个"矩形跟随框"）
- **用户感知到的"矩形"实际是这个绑在主角身上的圆形 AOE 圈**（在第三人称视角看像扁平的方形跟随区域）

这就是问题 #1 + #3 的真因 — **同一个参数错配导致两个表象问题**。

### 直线子弹的 follow_creator=1 是合理的

为什么 expand_bullet_straight 用 follow_creator=1：
- 直线子弹普攻（如 304006 火宗门普攻）的 AOE 检测确实需要跟创建者绑定，因为子弹很短，主角动了 AOE 也要动
- 这是**直线子弹**的合理设置

但**回旋飞回**子弹是飞出后独立的，AOE 不能再跟主角 — 必须 follow_creator=0。

## 解决方式

```python
# expand_bullet_boomerang 的 collision_node extra_params [9] 改为 0
extra_params=[
    hit_order_node.config_id,    # [0] 命中后
    1,                            # [1] 形状=1 圆形
    collision_radius,             # [2] 半径
    collision_height,             # [3] 参数2
    0,                            # [4] 参数3
    offset_right,                 # [5] 偏移右
    offset_forward,               # [6] 偏移前
    0,                            # [7] 目标单位 = 敌军
    0,                            # [8] 自定义条件
    0,                            # [9] **是否跟随创建者飞行 = 0** ← 修正
    detect_interval,              # [10] 侦测间隔
    0,                            # [11] 侦测冷却
    0,                            # [12] 侦测次数
],
```

LastTime 也调整：60 帧预留 → 25 帧（让子弹飞回主体时立即消失）。

## 利
- 子弹真正独立飞行，AOE 检测跟随子弹本体（不是绑主角）
- 视觉效果对：圆形 AOE 检测，不再有"跟随主角的矩形"错觉
- 子弹回到主体时立即消失（LastTime 收紧）
- **expand_bullet_boomerang vs expand_bullet_straight 的 follow_creator 取值差异有了明确依据**

## 弊
- expand_bullet_straight 的 follow_creator=1 是写死的，未来如果有"独立飞行的直线子弹"需求要做成 IR 字段

## 噪音风险
低 — 这是修复，不是新规则

## 反思 — "读模板字段语义"也要纳入 GATE-0.5

PostMortem #007 已经说过"不能凭字段名猜行为"，但这次踩的是**模板调用参数顺序+语义**的坑，是另一个层面：

| 我做了 | 我没做 |
|--------|--------|
| ✓ 抄了蝴蝶妖 BulletConfig 字段 | ✗ **没读子弹通用-碰撞模板的 13 个 TemplateParams 中文名定义** |
| ✓ 验证了 shape=1 圆形对 | ✗ 没意识到 follow_creator 默认 1 不适合飞出去的子弹 |

**沉淀规则更新**（GATE-0.5 §3 扩充）：
> 用 `make_template_call_node` 调用任何模板前，**必须读模板根节点的 TemplateParams 列表**，逐个 param 确认中文名+实际语义。
>
> 操作命令：
> ```bash
> # 查任意模板的 TemplateParams 定义
> python -c "import json; data=json.load(open('<template_path>')); ..."
> ```
>
> **不能凭字段顺序记忆**（如"我记得[9]是跟随创建者"），因为不同模板字段顺序不同。

我会把这条命令做成 SKILL.md 的 helper script，确保下次配模板调用先跑一遍。
