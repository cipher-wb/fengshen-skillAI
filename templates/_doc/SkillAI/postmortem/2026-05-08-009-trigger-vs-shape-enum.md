---
proposal_id: 2026-05-08-009
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py (expand_bullet_boomerang collision shape=0 + TracePathParams + LifeFlag=3)
  - doc/SkillAI/docs/易错点速查.md §15 (TTriggerType vs TShapeType 区分)
related_skill: 30142002 环刃归心 v1.2.3
---

# 用错枚举 TShapeType 误以为是 TTriggerType — 1 误为圆形实为矩形

## 决策
✅ **入库**

## 用户反馈（实测）
1. 碰撞依旧是矩形（要圆形 r=500，编辑器显示 5-碰撞范围类型=矩形）
2. 子弹飞回主角后还是过会才消失，没立即消失

## 根因 #1 — 用错枚举（跟字段名匹配错位）

### 我之前的错误对照

| 我用的（错） | 真实生效（对） |
|---|---|
| TShapeType（场景元素形状）：1=圆形 / 2=矩形 / 4=扇形 | TTriggerType（碰撞触发形状）：**0=圆形 / 1=矩形** / 2=扇形 / 3=环形 / 4=直线 |

模板 [1] 字段 RefType=**`TTriggerType`**（不是 TShapeType）。

我之前在 PostMortem #008 修正了 follow_creator 参数，但**形状值依然写的 1**，按 TTriggerType 实际是矩形。所以用户实测看到的就是矩形。

### 问题暴露的深层教训

PostMortem #007: 不能凭字段名猜行为
PostMortem #008: 必须读模板 TemplateParams 中文名定义
**PostMortem #009 新增**: 还要读字段的 **RefTypeName**（如 `TTriggerType`），并查这个枚举的实际取值定义。

不同枚举名字看起来都"形状"，但取值规则完全不同：
- TShapeType: 1=圆形（NULL=0）
- TTriggerType: 0=圆形（直接从 0 开始）
- TTracePathType: 1=直线（NULL=0）

**坑点**：项目里至少 3 个"形状/类型"枚举，**用错一个就会报错却看不出来**（因为整数值合法，只是语义不对）。

## 根因 #2 — TracePathParams + LifeFlag 没用对

### 飞行距离参数被截断

蝴蝶妖原参数：`TracePathParams=[25, 8, 1000, 0, 1500, 0]` + `MaxDistance=3000`
- TracePathParams[2] = 1000 (飞出距离)
- BulletConfig.MaxDistance = 3000 是硬上限（不影响 TracePathParams 的飞出距离）

我之前：`TracePathParams=[25, 8, 1000, 0, 1500, 0]` (蝴蝶妖原值) + `MaxDistance=600`
- **MaxDistance=600 截断了 TracePathParams[2]=1000** → 子弹只飞 600cm 就死亡，没机会回飞
- 用户看到"在自己身边一点点就悬停了"

### LifeFlag 值不对

| 值 | 含义 |
|---|---|
| 0 | 默认 |
| 1 | 达到时间上限（仅时间）— 我之前的值 |
| 2 | 达到距离上限 |
| 3 | 时间 OR 距离（蝴蝶妖同款）|

我之前 LifeFlag=1（仅按时间），子弹**距离已到不消失**，必须等 LastTime 满 → 子弹"飞回主体后还要飞一段才消失"。

## 解决方式（v1.2.3 一次性修 5 处）

```python
# expand_bullet_boomerang
collision_node = make_template_call_node(
    extra_params=[
        ...
        0,                # [1] 碰撞范围类型 = 0 圆形 (TTriggerType.TTT_Circle) ✓修正
        ...
    ]
)

bullet_cfg_node = _make_inline_bullet_config_node(
    trace_path_params=[25, 8, max_distance, 0, return_speed, 0],   # ✓ IR 参数生效
    last_time=flight + hover + 12,                                 # ✓ 紧凑寿命
    max_distance=max_distance + 200,                               # ✓ 加余量不截断
)
bullet_cfg_node.config_payload["LifeFlag"] = 3                     # ✓ 时间 OR 距离触发死亡
```

## 验证结果

```
[碰撞模板]
  [4]碰撞范围类型: 0 (圆形 TTT_Circle) ✓
  [5]半径: 500 ✓
  [12]跟随创建者: 0 ✓

[BulletConfig 32002050]
  LastTime: 82  (30+40+12)
  MaxDistance: 800  (= IR 600 + 200 余量)
  LifeFlag: 3  (蝴蝶妖同款)
  TracePathParams: [25, 8, 600, 0, 2000, 0]  (IR 参数已注入)
```

## 利
- 圆形 AOE 真正生效（不再矩形）
- 飞出距离 = IR max_distance（不再被截断）
- 回飞速度 = IR return_speed（用户参数生效）
- LifeFlag=3：到时间 OR 到距离都立即销毁，子弹回到主体附近立即消失

## 弊
- TracePathParams 6 个参数索引 [0]/[1]/[3]/[5] 含义仍未逆向（[2]=飞出距离, [4]=回飞速度 是猜测，但与蝴蝶妖样本一致）

## 噪音风险
低 — 修复

## 反思 — 字段类型与枚举的"三层校对"

这次失败本质是**字段-枚举校对不严格**。从此对任何模板字段调用强制三层校对：

1. **TemplateParam Name** — 中文名（如"碰撞范围类型"）
2. **TemplateParam RefTypeName** — 枚举类型名（如 `TTriggerType`）
3. **去 common.cs 查这个枚举的实际取值** — 不假设跟"X 字段叫 X 形状"同名的另一个枚举一样

**沉淀更新**：[skill-design SKILL.md GATE-0.5 §3](../../../.claude/skills/skill-design/SKILL.md) 加第三层校对要求。

helper 命令更新：
```bash
# 老命令：只查 TemplateParams 中文名
python -c "...TemplateParams['Name']..."

# 新命令：同时查 RefTypeName + 枚举值
python -c "...
  for tp in TemplateParams:
      ref = tp['RefTypeName']
      print(f'[{i}] {tp[\"Name\"]}  RefType={ref}')
      if ref:
          # 自动查 enums.json 里这个 RefType 的取值
          enum_def = enums.get(ref, {}).get('entries', [])
          for e in enum_def:
              print(f'    {e[\"value\"]}={e[\"cn\"]}')
"
```

这条规则我会立即沉淀到 SKILL.md。
