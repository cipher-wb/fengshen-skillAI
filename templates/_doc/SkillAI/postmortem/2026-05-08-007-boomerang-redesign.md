---
proposal_id: 2026-05-08-007
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py (expand_bullet_boomerang v1.2.1)
  - doc/SkillAI/tools/skill_compiler.py (derive_edges 加 BulletConfig 三个生命周期钩子边)
related_skill: 30142002 环刃归心（v1.2.1 单 Bullet 简化）
---

# 双 Bullet 接力重设计 + BulletConfig 边丢失修复

## 决策
✅ **入库**

## 用户反馈（实测）
1. Bullet2 不追施法者，朝远处散开飞去了
2. Die ORDER 节点（32002006）孤立无入边
3. Bullet1 悬停距离太近

## 根因分析

### 问题 #1 + #3：双 Bullet 接力的 Bullet2 配置失败

**v1.2.0 设计**：双 Bullet 接力（Bullet1 飞出+悬停 → Die 触发 Bullet2 追施法者）

**实际表现失败原因**：
- Bullet2 用 FlyType=6 TRACK_TARGET_POINT — 但**目标点没指定**就默认朝面向飞，飞向远处而非追施法者
- Bullet1 用 FlyType=5/TracePathType=4 静态轨迹 — TracePathType=4 STEADY 静态轨迹**不响应 max_distance**，行为不可控
- TracePathParams 11 个参数语义未逆向，乱填 [flight_frames, max_distance, 0, 0, 0, 0] 没起作用

**深层根因**：v1.2.0 设计时**没充分理解 BulletConfig 各种 FlyType 的实际行为**，凭"FlyType 名字直觉"配置：
- FlyType=4 朝向目标点 — 误认为"飞到固定距离悬停"
- FlyType=6 追踪目标坐标点 — 误认为"自动追施法者"

实际行为完全不符。

### 问题 #2：BulletConfig.DieSkillEffectExecuteInfo 引用没建边

**根因**：编译器 `derive_edges` 只为 BulletConfigNode 的 `AfterBornSkillEffectExecuteInfo` 建边，遗漏了 `BeforeBornSkillEffectExecuteInfo` 和 `DieSkillEffectExecuteInfo`。

```python
# v1.2.0 错误代码
ab = n.config_payload.get("AfterBornSkillEffectExecuteInfo", {})  # 只看 AfterBorn
ab_id = ab.get("SkillEffectConfigID", 0)
if ab_id: edges.append(...)  # 只建一条边
# BeforeBorn / Die 都被忽略
```

## 解决方式

### v1.2.1 简化设计：单 Bullet 套蝴蝶妖回旋镖 2200124 配置

**改动**：放弃双 Bullet 接力，改为单 Bullet 直接复用蝴蝶妖回旋镖 2200124 已验证的字段：

```python
# v1.2.1 BulletConfig 字段（蝴蝶妖同款）
FlyType=5 / TracePathType=3                  # 折返轨迹（自带飞出+悬停+追施法者）
TracePathParams=[25, 8, 1000, 0, 1500, 0]    # 蝴蝶妖原参数（不细究语义，整体复用）
Speed=2000 / AcceSpeed=1500 / MaxSpeed=5000  # 蝴蝶妖原参数
ChaseTargetEnemy_FaceToTarget=True           # 关键：自带"追施法者"行为
ChaseTargetEnemy_PitchFaceToTarget=True
LastTime = flight_frames + hover_frames + 60 # 总时长
AfterBorn = 子弹通用-碰撞模板（**全程挂碰撞**）
```

**已知局限**：飞出阶段碰到目标也会造伤害（不严格匹配 LOL 泰隆 R 的"出去无伤"语义）。但视觉效果（一圈飞出+悬停+追施法者飞回）正确。

未来精确做"出去无伤 / 回飞才有伤"需要：
- IR 加 SkillTag 时间条件控制（cast_frame 记起飞帧 + DELAY 后才挂碰撞模板）
- 或直接修改子弹通用-碰撞模板里的"命中后功能"加判断分支

工时投入产出比偏低，**目前不做**。等用户实测后看是否能接受。

### derive_edges 修复

```python
# v1.2.1 修正
for hook_field in (
    "BeforeBornSkillEffectExecuteInfo",
    "AfterBornSkillEffectExecuteInfo",
    "DieSkillEffectExecuteInfo",
):
    hook = n.config_payload.get(hook_field, {})
    hook_id = hook.get("SkillEffectConfigID", 0)
    if hook_id: edges.append(...)
```

## 编译产物对照

| 维度 | v1.2.0 (双 Bullet) | v1.2.1 (单 Bullet) |
|---|---|---|
| 节点数 | 30 | 27（少 Bullet2/Die ORDER/CREATE_BULLET2） |
| 边数 | 41 | 39 |
| BulletConfigNode | 2（Bullet1 + Bullet2） | 1（Bullet 蝴蝶妖配置） |
| 孤立节点 | 1 (Die ORDER 孤立) | 0 |
| 视觉效果 | ❌ 飞向远处 | ✅ 飞出+悬停+追施法者飞回 |
| 出去无伤精确性 | 有 schema 但实际无效 | 无（已知放弃） |

## 利
- **修边丢失 bug**：未来任何 BulletConfig 用 BeforeBorn / Die 钩子的技能都自动建边
- **视觉效果对了**：用户能看到"一圈回旋"，不再是"散开飞远"
- **节点数减少**：27 vs 30，更易维护
- **复用已验证模板**：直接抄蝴蝶妖参数，不冒"FlyType 直觉"风险

## 弊
- 牺牲"出去无伤 / 回飞才有伤"的精确语义
- TracePathParams 11/6 个参数仍未逆向（按需调时还要研究）

## 噪音风险
低 — 这是修正性沉淀，工具本身更稳

## 反思 — "凭直觉配字段"的代价

**这次踩坑的本质**：FlyType=4 / FlyType=6 的字段名翻译看起来"有意义"，我直接按名字猜行为，而**没有去验证实际样本**。

GATE-0.5 要求"非常规模式必须读模板实际行为"，但这次我对"模板"的理解是"读 30212005 木影旋刃的拓扑"，**没意识到** BulletConfig 的字段行为也需要"读样本配置"才能确认（不能只看字段名）。

**沉淀规则更新**：GATE-0.5 第 3 项"非常规模式必须读模板实际行为"应该扩展为：
- ✓ 读相关节点/模板的拓扑结构
- ✓ **新增**：读相关 BulletConfig / ModelConfig / BuffConfig 字段的**真实样本值**（同类型现有技能的具体配置）
- ✓ **新增**：不能凭字段名猜行为（如 FlyType=6 "追踪目标坐标点" 不等于"自动追施法者"）

下次配回旋类需求，AI 应**直接抄真实样本的全部 BulletConfig 字段**，再用 IR 参数覆盖关键字段，而不是从空白配置开始猜。

我会把这条规则写进 skill-design SKILL.md 的 GATE-0.5 §3。
