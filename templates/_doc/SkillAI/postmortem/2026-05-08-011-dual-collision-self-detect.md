---
proposal_id: 2026-05-08-011
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py (expand_bullet_boomerang v1.3 加双碰撞模板)
  - doc/SkillAI/docs/易错点速查.md §16 (target_camp=3 自己/创建者用法)
related_skill: 30142002 环刃归心 v1.3
---

# v1.3 双碰撞模板 — 让每颗子弹独立"碰到主角才销毁"

## 决策
✅ **入库**

## 用户反馈（v1.2.4 实测）
1. 飞太近 — 已修（max_distance 600→1500）
2. 飞回过早消失 — 已修（LifeFlag=1 + MaxDistance 巨大 + LastTime 算够）
3. **8 颗子弹一起消失，不是各自碰到主角才消失**

## 问题 #3 根因
对称路径下 8 颗子弹同帧到达主角 → 同步死亡（LastTime 时间触发）。"分别消失"必须有"碰到主角"这个事件触发，BulletConfig 自身没有该钩子。

## 解决方式：双碰撞模板拓扑（v1.3）

```
Bullet (FlyType=5/TracePathType=3 折返)
  AfterBorn = ORDER:
    ├ 碰撞模板1（target_camp=0 敌方）→ 命中后造伤害（不销毁）
    └ 碰撞模板2（target_camp=3 自己/创建者）→ 命中后 TSET_DESTROY_ENTITY 销毁子弹自身
        - 半径=100（比敌方半径 500 小，避免误触）
        - 侦测冷却 = flight_frames + hover_frames（70 帧）→ 飞出+悬停阶段不触发
        - 只在回飞阶段才开始检测主角
```

### 核心节点
- `TSET_DESTROY_ENTITY` Params=[entity:主体, 0, 0]：销毁主体单位（即子弹自己）
- 第二碰撞模板的"侦测冷却"参数（[11]）= 飞出+悬停帧数 → 子弹刚出生时不会立即误触主角

### 编译产物（30 节点 / 42 边）
| 节点 | 数量 | 用途 |
|---|---|---|
| 碰撞模板调用 | 2 | 敌方造伤 + 主角销毁 |
| TSET_DESTROY_ENTITY | 1 | 销毁子弹 |
| AfterBorn ORDER | 1 | 包两个碰撞模板 |
| 其他 | 26 | 常规子弹链路 |

## 风险点（重要）
- **target_camp=3（自己/创建者）项目内无现成样本**，是未验证路径
- 实测可能行为不符预期（如：完全不触发，或者触发时机异常）
- 如果 target_camp=3 实际不能检测创建者 → fallback 方案待定（用 TSKILLSELECT_CIRCLE 圆形筛选 + 手动比对实体？）

## 利
- 真正实现"每颗子弹独立碰到主角才消失"
- 子弹路径有微小差异时陆续触发 → 视觉上分别消失

## 弊
- 节点数从 27→30（多了 1 个 ORDER + 1 个销毁 + 1 个碰撞模板）
- target_camp=3 是项目内首次使用，可能有未知行为

## 噪音风险
中 — target_camp=3 是新路径，实测要严格验证

## 反思 — 这次踩坑特点
不是"AI 偷懒/健忘"，而是"项目机制本身没有现成方案"。从 SkillEditor 自带能力（target_camp=3 自己）拼接出新功能，**这种创新需要充分实测**。

## Unity 实测预期
1. 飞 1500cm 远（不再"在自己身边一点点就悬停"）
2. 飞回主角附近时，**每颗子弹独立销毁**（不再同步消失）
3. 飞出+悬停阶段不会因为子弹靠近主角而误触销毁

如果 target_camp=3 不生效（子弹依然按 LastTime 同步死亡），降级到 v1.2.4 + 文档明确"对称路径必然同步消失"。
