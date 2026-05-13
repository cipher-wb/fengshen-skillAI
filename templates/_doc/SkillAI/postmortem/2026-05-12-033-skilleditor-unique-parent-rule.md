---
type: 复盘页
summary: SkillEditor 强制每个节点 unique-parent（左侧 ID 端口只能有 1 条 input edge），多父引用会被 silently 删一条 + 报「连线数据丢失」
date: 2026-05-12
tags: [PostMortem, SkillEditor, edges, unique-parent, 心智模型核心, 32900165 bug]
severity: 严重（30212018 反复修连线失败的真正根因 / 多次错误尝试的元根因）
---

# PostMortem #033 — SkillEditor unique-parent 强约束

## 一句话

**SkillEditor 严格要求每个节点最多 1 个上游父引用（左侧 ID 端口）。我 30212018 build 时让 32900194 REPEAT 被 32900165 + 32900166 两个 ORDER 共享 → SkillEditor silently 隐藏一条 edge + 报"连线数据丢失" — 用户连续 3 次截图指出后我才意识到。**

---

## 现象

30212018 内 BulletConfig 320262 (强化) 和 BulletConfig 320263 (普通) 各自 AfterBorn ORDER (32900165/32900166)。我为了"节省节点"让它们都 P[0]=32900194 REPEAT 共享。

结果：
- 32900166 视觉上正确连到 32900194
- **32900165 视觉上没显示 32900194 → 32900165 这条 edge**（SkillEditor 把它当 "duplicate parent" 隐藏）
- Console 报 `[SkillEffectConfig:32900165] 连线数据丢失，参数1`

用户连续 3 次指出"32900165 视觉上没看到 32900194 那条线"，我反复修 outPort / GUID / position / computeOrder 都不对症。

---

## 根因

### SkillEditor 的 unique-parent 强约束（用户裁定）

**每个 SkillEffect 节点最多 1 个父引用（即其左侧 "ID" port 只能有 1 条 incoming edge）。**

适用范围（用户裁定 2026-05-12）：
- ⭐ **所有节点都严格**，包括数据节点（NUM_CALC / GET_ENTITY_ATTR / cos / sin 等）
- 不只是控制流（ORDER / REPEAT 子项）

### 视觉表现

如果 JSON 里某节点 N 同时被 A 和 B 两个父节点 Params 引用（A.Params 和 B.Params 都包含 V=N.ID 的项），SkillEditor 行为：
- **视觉**：只显示其中 1 条 edge（哪条是"获胜"的不确定，可能依赖添加顺序）
- **数据**：另一条 edge 仍在 JSON 内但被隐藏
- **Lint**：报 "连线数据丢失，参数N"（指向被隐藏一方的 Params 位置）

### 错误的"省节点"诱惑

人脑/AI 的省节点冲动：

```
错（unique-parent 违反）：
  强化 wrapper ORDER ─┐
                      ├─→ 共享 REPEAT ──→ 共享 OnTick body
  普通 wrapper ORDER ─┘

对（每条链独立）：
  强化 wrapper ORDER ──→ REPEAT 强化 ──→ OnTick body 强化 ──→ [MODIFY/ADD/CHANGE_POS 强化版]
  普通 wrapper ORDER ──→ REPEAT 普通 ──→ OnTick body 普通 ──→ [MODIFY/ADD/CHANGE_POS 普通版]
```

---

## 关键认知（写入心智模型）

### 1. SkillEditor edge 方向语义

| 视觉端口 | 对应 edge 字段 | 语义 |
|---------|--------------|------|
| 左侧 "ID" port | `outputNodeGUID` | 被引用方（**子**） |
| 右侧 "技能效果ID" port | `inputNodeGUID` | 引用方（**父**） |

- edge: `inputNodeGUID = 父, outputNodeGUID = 子`
- 视觉箭头方向："父右侧" → "子左侧"
- 每个子的"左侧 ID port" 只能有 1 条 incoming edge → **unique parent**

### 2. unique-parent 违反时

- 多父引用时 SkillEditor 自动隐藏多余 edges
- Console 报 "连线数据丢失，参数N"
- 修法：**复制被多父引用的节点 + 它所有下游被多次引用的子节点**（递归复制控制流子节点）

### 3. 节省节点 = 反模式

技能蓝图里**不要追求 DRY**。每条独立调用链需要独立节点实例。SkillEditor 的"节点 = 配置条目"模型不是"函数"，不能 reuse。

---

## 防再犯措施

### Sensor: 看到"连线数据丢失" lint 错

**第一时间 check**：
1. 报错节点的 Params[N] 引用了哪个节点 X
2. 节点 X 是否被**多个父节点**的 Params 引用
3. 是 → 不可避免要复制（X + 它的全部下游被多次引用的子节点）

### Sensor: 配「2 种子弹（如强化/普通）共享 OnTick」

**第一时间想**：
- 不能共享 REPEAT
- 不能共享 OnTick body ORDER
- 不能共享 OnTick body 内的 MODIFY/ADD/CHANGE_POS（控制流节点）
- 数据节点（cos/sin/GET）也按 strict unique-parent 处理（用户裁定 2026-05-12）

### Guide: 复制策略

复制时**保留**：
- 节点本身 ID 重分配
- ConfigJson 内 Params 引用 reallocate 到 _normal 版本
- edges 重建

复制 + reallocate 一次性脚本化（避免手动错）。

---

## 引用

- 用户裁定 (2026-05-12)：unique-parent **包括数据节点**
- 此 PoC bug 跟 PostMortem #032 (BulletConfig.AfterBorn 必须 REPEAT 包装) 是连环的两个底层规则错误
- 30212018 修复 patch: doc/SkillAI/tools/builders/patch_30212018_*.py
