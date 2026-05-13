---
type: 复盘页
summary: SkillEditor 节点端口有"固定端口"和"动态端口"两类，AND/OR/ORDER 等多子项聚合型节点用 dynamic port (所有 input edges outPort 都用 "0")。用错 → edge 被自动删 + Params 被清。
date: 2026-05-12
tags: [PostMortem, SkillEditor, edges, outputPortIdentifier, dynamic-port, AND-node, 心智模型核心]
severity: 严重（30212018 强化判断永远 true 反复修不好的真正根因）
---

# PostMortem #034 — SkillEditor dynamic-port vs fixed-port

## 一句话

**ORDER / AND / OR / SELECT_EXECUTE 等"多子项聚合"型节点是 dynamic-port：所有 input edges 的 `outputPortIdentifier` 都必须用 `"0"`（不论 Params 多少项）。我给 AND 第二条 edge 用了 outPort='1' → SkillEditor 不识别 → 自动删 edge + 同步清掉 Params P[1] → AND 退化为单条件 → 强化判断永远 true → 所有子弹强化。**

## 现象

30212018 内 AND 32900169 节点：
- Params 期望 `[320001 HAS_BUFF, 32900168 VALUE_COMPARE]` (两个条件)
- 我加 edges:
  - `320001 → 32900169 outPort='0'`
  - `32900168 → 32900169 outPort='1'` ← 这条错
- SkillEditor 看 AND 节点 — 没有 '1' 端口 → 删 edge 32900168→169 + Params 同步成 `[320001]` 单项
- AND 等价 "只判 HAS_BUFF" → buff 在就 true → 全部强化

用户连续 3 次说"AND 后方应该同时连两个，但只连了一个" — 我没意识到 outPort 用错了，反复修 Params 不解决根本问题。

最后用户提示"理解逻辑但连线出问题"才定位到。

## 根因 / 规则

### SkillEditor 节点端口的 2 种模式

| 模式 | 节点类型 | outputPortIdentifier 规则 |
|------|---------|---------------------------|
| **固定端口** | NUM_CALC / MODIFY_ENTITY_ATTR_VALUE / CHANGE_ENTITY_POSITION / GET_ENTITY_ATTR / CREATE_BULLET 等 | 按 **Params 索引**：`"0"`/`"1"`/`"2"`... 对应 P[0]/P[1]/P[2] |
| **动态端口** ⚠️ | **ORDER_EXECUTE / AND / OR / SELECT_EXECUTE / REPEAT_EXECUTE body 等多子项聚合型** | **所有 input edges 全部用 `"0"`** |

### 判断规则

**Params 可变长（用户能在 SkillEditor 增减项）→ dynamic port → 全用 outPort='0'**

- ORDER 子项可多可少 → dynamic
- AND/OR 条件可 2 个 / 3 个 / N 个 → dynamic
- NUM_CALC Params 固定 7 项 (chain) → fixed port
- CREATE_BULLET Params 固定 15 项 → fixed port

### 30212010 范式参考

```
320357 AND 的两条 input edges:
  edge1: 320358 → 320357  outPort='0'
  edge2: 320359 → 320357  outPort='0'  ← 注意 不是 '1'!
```

## 防再犯

### Sensor

**配 AND / OR / ORDER 等节点时**：
- 所有 input edges 用 outPort='0'
- 千万不要按 P[0]/P[1]/P[2] 用 '0'/'1'/'2'

**症状**：节点 Params 数比 edges 数多（编辑器报"连线数据丢失"或自动清掉某些 Params）→ 怀疑 dynamic port outPort 用错。

### Guide

写 build patch 时：
```python
def add_edge_dynamic(src, dst):  # ORDER / AND / OR
    return edge(src, dst, port='0')  # 永远 '0'

def add_edge_fixed(src, dst, param_idx):  # NUM_CALC / CREATE_BULLET
    return edge(src, dst, port=str(param_idx))
```

## 历史教训链 (5 连发)

本会话用了 5 个 PostMortem 才把 SkillEditor 底层规则搞清楚：

| # | 教训 |
|---|------|
| #032 | BulletConfig.AfterBorn 是出生后一次性 / 要每帧执行必须 REPEAT 包装 |
| #033 | 每个节点 unique-parent（左侧 ID port 只能 1 条 incoming edge）|
| #033b | edge outputFieldName 区分 PackedParamsOutput vs PackedMembersOutput |
| #033c | member edge outputPortIdentifier 用字段路径名（不是数字索引）|
| **#034** | **ORDER/AND/OR 等多子项聚合是 dynamic port，outPort 全用 '0'** |

## 引用

- 30212010 320357 AND 是金标样本
- 30212018 配置 patch 链 (doc/SkillAI/tools/builders/patch_30212018_*.py)
- memory/feedback_skilleditor_unique_parent.md §3b
