---
type: 复盘页
summary: BulletConfig.AfterBornSkillEffectExecuteInfo 是「出生后调用一次」的钩子，不是每帧 — OnTick 必须靠 REPEAT 包装
date: 2026-05-11
tags: [PostMortem, BulletConfig, AfterBorn, REPEAT, OnTick, 心智模型核心]
severity: 严重（30212018 子弹不移动 / 多次 fix 失败的根因）
---

# PostMortem #032 — BulletConfig.AfterBorn 语义 + OnTick REPEAT 包装规则

## 一句话

**`BulletConfig.AfterBornSkillEffectExecuteInfo` 是「子弹出生后调用一次」的钩子，不是每帧执行 — 要让 OnTick 每帧跑必须用 REPEAT_EXECUTE 包装。这是底层语义错误导致多次连续修复都失败的根因。**

---

## 现象

30212018 建好后报错 + 子弹生成后停在原地不移动。

我反复尝试修 32900165 (强化子弹 AfterBorn ORDER) 的连线问题，期望 P[0]=32900133 (风车 OnTick body) 触发每帧移动。**但子弹始终不动**。

用户最终指出："**32900133 不应该在 32900165 的 Params 里**，你是不是先刚从 32900133 这个节点连到 32900165？"

---

## 根因

### BulletConfig 钩子的真实语义

| 钩子 | 语义 | 调用次数 |
|------|------|---------|
| BeforeBornSkillEffectExecuteInfo | 子弹出生**之前** | 一次性 |
| **AfterBornSkillEffectExecuteInfo** | **子弹出生之后** | **一次性** ⚠️ |
| DieSkillEffectExecuteInfo | 子弹死亡时 | 一次性 |

**`AfterBorn` 不是 OnTick！它是出生后的 setup 调用。**

### 要让 effect 每帧执行 → 必须 REPEAT 包装

30212017 PoC 的实际正确结构：

```
BulletConfig 320258.AfterBornSkillEffectExecuteInfo
  → 32900044 ORDER (一次性入口)
      └─ P[0] = 32900043 REPEAT_EXECUTE
                  ├─ interval = 1 (每帧)
                  ├─ count = 1000 (≈ 16 秒上限)
                  └─ body = 32900046 ORDER (每帧 OnTick: 旋转 + 加速 + 移动)
```

**REPEAT 是「每帧执行」的载体**。`AfterBorn` 只是「启动」REPEAT 的入口。

---

## 我的错误链

| 错误 | 影响 |
|------|------|
| 1. build patch 时把 32900165 P[0] 直接填 32900133 (OnTick body) | 子弹只移动 1 帧后停止 |
| 2. 清理"孤立节点"时把 REPEAT 32900131 (= 30212017 32900043 reallocated) 当孤立删了 | 删了实际是 BulletConfig.AfterBorn → ORDER → REPEAT 链的关键节点 |
| 3. 反复尝试修 edges、outPort、跨蓝图引用 | 治标不治本 / 没意识到 P[0] 本身就错了 |

---

## 关键认知（写入心智模型）

### 1. BulletConfig 三个钩子都是「一次性」

- AfterBorn 不会自动循环
- 要每帧跑某 effect → REPEAT_EXECUTE 包装

### 2. 标准 OnTick 链结构

```
BulletConfig.AfterBornSkillEffectExecuteInfo
  → ORDER (一次性 / 可放多个 setup + REPEAT)
      ├─ REPEAT_EXECUTE (every-frame loop / interval=1)
      │     body = OnTick body ORDER
      └─ 其他出生时 setup (如碰撞模板调用 / 注册命中 callback)
```

### 3. 不要把 REPEAT 当「孤立节点」删

REPEAT 节点表面"没人调用"是错觉 — 它是 ORDER 的子项（被 ORDER.Params 引用），ORDER 才是被 BulletConfig.AfterBorn 引用的入口。删 REPEAT = 断了每帧循环。

### 4. 跨蓝图 RefConfigBaseNode 不能作为 ORDER 子项（衍生认知）

SkillEditor 严格 lint ORDER 子项的 source 必须**在同蓝图内**（且能 push PackedParamsOutput）。跨蓝图 RefConfigBaseNode 引用 ORDER 会被 SkillEditor 自动清掉 Params 项。**ORDER 子项必须本地化。**

---

## 防再犯措施

### Sensor: 任何"子弹生成后不动 / 行为不发生"现象，第一时间 check

1. BulletConfig.AfterBornSkillEffectExecuteInfo 指向的节点是否 ORDER
2. 该 ORDER 里是否有 REPEAT_EXECUTE 节点
3. REPEAT 的 body 是否指向 OnTick body
4. REPEAT 的 interval/count 不能 0/-1（PostMortem #026 C++ crash）

### Sensor: 清理"孤立节点"前

1. 不要光看 incoming refs。还要看 outgoing：
   - 节点是不是某 ORDER 的 Params 子项 → 被引用
   - 节点是不是 BulletConfig.AfterBorn/BeforeBorn/Die 指向 → 被引用
   - 节点是不是 SkillConfig.SkillEffectExecuteInfo 指向 → 被引用

### Guide: 复制风车技能模板时

直接 copy 30212017 整套结构：
```
BulletConfig.AfterBorn → AfterBorn_ORDER → [REPEAT_OnTick (body=OnTick_body), 其他 setup]
```
不要省 REPEAT 这一层！

---

## 引用

- [BulletConfig.cs](../../../Assets/Scripts/TableDR_CS/Hotfix/Gen/BulletConfig.cs) — AfterBornSkillEffectExecuteInfo 字段定义
- 30212017 PoC: BulletConfig 320258.AfterBorn → 32900044 → REPEAT 32900043 (body=32900046)
- PostMortem #026 — REPEAT interval=0/count=-1 C++ crash
