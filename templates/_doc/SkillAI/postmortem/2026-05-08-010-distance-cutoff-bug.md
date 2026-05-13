---
proposal_id: 2026-05-08-010
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py (expand_bullet_boomerang LifeFlag=1, MaxDistance×4, LastTime 算够)
  - doc/SkillAI/docs/易错点速查.md §17 (LifeFlag + MaxDistance 双重距离限制陷阱)
related_skill: 30142002 环刃归心 v1.2.4
---

# LifeFlag=3 + MaxDistance 截断 → 子弹回飞途中提前死亡

## 决策
✅ **入库**（v1.2.4 修复）

## 用户反馈（v1.2.3 实测）
1. 飞太近（max_distance=600 不够远）
2. 子弹飞回过早消失，**还没碰到主角就消失了**

## 根因 — 双重距离限制叠加触发提前死亡

### v1.2.3 配置（错误）
```
LifeFlag=3 (时间 OR 距离都触发死亡)
MaxDistance=max_distance + 200 = 800
```

### 实际行为推演
- 子弹飞出 600cm 到达悬停点（累计 600cm）
- 开始回飞 → 累计走到 800cm 时（即回飞 200cm 还没到主角）
- LifeFlag=3 + MaxDistance=800 触发**距离上限死亡**
- 用户看到："还没碰到主角就消失"

### 同步消失的原因
8 颗子弹累计距离同时到 800cm → 同帧触发距离死亡 → 一起消失。

## 解决方式（v1.2.4）

```python
return_frames_estimate = max(15, int(max_distance * 60 / max(return_speed, 1)))
bullet_total_lifetime = flight_frames + hover_frames + return_frames_estimate + 10

bullet_cfg_node = _make_inline_bullet_config_node(
    last_time=bullet_total_lifetime,        # 算足够回飞时间
    max_distance=max_distance * 4,          # ② 巨大余量，避免任何距离截断
    ...
)
bullet_cfg_node.config_payload["LifeFlag"] = 1   # ① 仅时间触发死亡，不让距离截断
```

并 IR 改 max_distance: 600 → 1500（飞远一些）。

## 利
- 距离不再触发死亡，子弹按 LastTime 走完飞出+悬停+回飞全程
- 飞距 1500 视觉显著
- LifeFlag=1 比 3 更稳定（仅时间触发，行为可预测）

## 弊
- 8 颗子弹仍同步消失（这是路径对称性的物理必然，与本 PostMortem 无关；v1.3 #011 引入"碰主角销毁"机制解决）

## 噪音风险
低 — 修复

## 反思
**双重限制叠加**是 SkillEditor 配置常见陷阱：
- `LifeFlag` 控制"按什么触发死亡"
- `MaxDistance` 是距离上限
- 两个一起用时容易一个触发死亡条件没意识到

**沉淀更新**：速查§17 加"LifeFlag + MaxDistance 双重距离限制陷阱"条目（待沉淀）。
