---
subsystem: SkillEvent 系统
confidence: 高
last_review: 2026-05-10
related_postmortems: []
related_samples:
  - SkillGraph_146003779_【模板】技能短长按持续施法模板.json
  - SkillGraph_30531006_【金宗门】传承心法_标签效果.json
  - SkillGraph_30433001_【水宗门】身法_天阶_潜行水底.json
  - SkillGraph_30534004_【火宗门】标签效果_蓄炎.json
  - SkillGraph_30535000_【土宗门】传承心法_天阶_土系传承心法.json
  - SkillGraph_30531008_【金宗门】标签效果_蓄势.json
  - SkillGraph_30325001_【土宗门】天坠石牢_地阶_神通.json
  - SkillGraph_30214004_【火宗门】人阶多段连击_蓄力.json
  - SkillGraph_30315001_【土宗门】携岩坠地.json
  - SkillGraph_30532001_【木宗门】青藤之力_心法.json
  - SkillGraph_30221000_【金宗门】奇术1_地阶_长CD大招.json
  - SkillGraph_30221120_【金宗门】地阶奇术3.json
  - SkillGraph_308072_青木天葬_法宝.json
  - SkillGraph_400019_法器真诀_纹章叠刃刺.json
  # B-014 R1/R2 (2 训练样本, 2026-05-10) — D-1405 N 对 REG/UNREG 不必成对 candidate / v0.6 D-505 范式边界
  - SkillGraph_2250030【搜打撤】隐身符.json   # 22xxx_7d 道具型 SubType=401 + 2 REG + 2 UNREG 成对范式 / N=2 < 5 不构成核心范式 / 但成对范式存在（v0.6 D-505 范式边界 candidate）
  - SkillGraph_4400001【BUFF】挑战妖王异化buff.json   # 44xxx_7d BUFF 配置 SubType=0 + 6 REG + 0 UNREG 不必成对 / 多形态切换条件不需要 UNREG 反向操作（不需要 UNREG 反向操作的 BUFF 异化形态切换型 范式 candidate）
  # B-015 R1/R2 (6 训练 + 1 holdout, 2026-05-10) — 仅作版本同步 / 无新主张 / candidate_1 独立 audit_session 第 1 批 / fast-path 第 11 次实战 R0 partial → R1 R2 pass / improvement=0.95 / curator 进阶元学习首次记录 / rule_2 永不 silent delete 实战范例第四次完美执行
  - SkillGraph_30073323_【法宝技】小黑棍主动效果_3阶强化.json   # 30xxxxxxx_8d 极简空壳反例 / SkillEntry SkillEffect 子片段（仅版本同步 / 无 SkillEvent 新主张）
  - SkillGraph_30312004_【木宗门】神通-人阶-木傀.json   # 30xxxxxxx_8d / SubType=103 Mode A（仅版本同步 / 无 SkillEvent 新主张）
  - SkillGraph_30615001_【土系低阶本命-混元无极盾】变身.json   # ⭐ 30xxxxxxx_8d / SubType=303 Mode E_dual_nonzero / 90 节点（仅版本同步 / 无 SkillEvent 新主张）
  - SkillGraph_302925_【木宗门】灵光术_老心法.json   # 30xxxx_6d / SubType=0 Mode C（仅版本同步 / 无 SkillEvent 新主张）
  - SkillGraph_31220001_治疗妙药.json   # 31xxxxxxx_8d / SubType=0 Mode A（仅版本同步 / 无 SkillEvent 新主张）
  - SkillGraph_400049_【法器真诀】夺魄燃魂.json   # 400xxx_6d / SubType=501 Mode C（仅版本同步 / 无 SkillEvent 新主张）
  - SkillGraph_720035_灵宠光环_holdout.json   # 720xxx_6d holdout / SubType=701 Mode C（仅版本同步 / 无 SkillEvent 新主张）
mental_model_version: v0.15
---

## 一句话本质

**SkillEvent 系统是 effect 内部的局部事件订阅机制**，与 `SkillConfig.SkillEffectPassiveExecuteInfo`（全局被动入口）并行存在。`TSET_REGISTER_SKILL_EVENT` 在 effect 内监听战场事件（受击 / 命中 / 元素响应 / 短按 / 长按等），事件触发时跑配套的 callback effect。**心法标签效果型技能（模式 C 纯 Passive）的 Passive root 内部典型有 N 个 REGISTER 监听不同战场事件**——这是它们核心机制的运作方式。

---

## 字段语义（B-003 D-303 澄清，必读）

> **关键澄清**：节点 data 顶层 `SkillEffectType` 字段与 `Param[0].Value` 是**不同概念**，B-003 之前的 hold-out 推测把"EvType=68"误当成 Event ID，这里彻底澄清。

- 节点 data 顶层 `SkillEffectType` = **节点类型 ID**（不是 Event ID）
  - **68** = `TSET_REGISTER_SKILL_EVENT` 节点类型 ID
  - **69** = `TSET_UNREGISTER_SKILL_EVENT` 节点类型 ID
- **`Param[0].Value` = 真 Event ID**（全局枚举，下面 §Event ID 字典段列出已知值）
- hold-out 30331000 / 30315001 报"EvType=68"是指 `SkillEffectType=68`（节点类型），不是 Event ID 本身——这是字段命名歧义，AI 闭卷预测时容易混淆

---

## 关键不变量（违反就 100% 出问题）

1. **`TSET_REGISTER_SKILL_EVENT` 是 SkillEvent 注册的统一节点**（`SkillEffectType=68`） — 参数 `[event_id, callback_skill_effect_id, ..., 配套 SkillTag, 触发模式, 触发次数]`：
   - `Param[0]` = Event_ID（**全局枚举，已观察 15 值**：1 / 2 / 3 / 4 / 5 / 6 / 7 / 9 / 11 / 12 / 15 / 38 / 41 / 42 / 47，B-004 累计 11 + 4 = 15 数据点 from 9 样本，详见 §Event ID 字典段）
   - `Param[1]` = `callback_skill_effect_id`（事件触发时跑的 effect，**引用一个外部 SkillEffectConfig.ID** 而非 lambda）
   - `Param[4]` = 配套 SkillTag ID（事件触发标记 / 状态记录）
   - `Param[5-6]` = 触发模式 / 触发次数

2. **callback 不是 lambda，是引用一个外部 SkillEffectConfig** — 必须在 flow 内有该 ID 对应的节点。这是 v0.3 之前最容易误解的点：看到 REGISTER_EVENT 节点后，必须 grep callback ID 找到对应 SkillEffectConfig 节点才能完整理解事件触发后的逻辑链。

3. **REG / UNREG 不平衡是正常现象**（B-002 反直觉）— 30534004 注册 4 个 REG 但只有 1 个 UNREG。可能机制：(a) 多事件共享一次清理时机；(b) 引擎技能销毁时自动清理所有该技能注册的 REG。30534004 rid=1045 UNREG ref=220005337 = rid=1040 的 SkillEffectConfig.ID（用 effect_id 反查目标 REG）。

4. **REGISTER 典型在 Passive root 下**（模式 B 双 root / 模式 C 纯 Passive）— 标签效果型心法的 Passive 入口下挂 N 个 REG（30534004 4 个 REG），与 SkillEntry 模式 B/C 强耦合。Active 入口下也可能 REG（持续施法模板 146003779 在模板内部用 REG 实现短按 / 长按分支），但更少见。

---

## Event ID 字典（B-004 收集 15 数据点，待补完）

观察到的 Event ID 与推测语义（**未读源码确认**）：

| Event ID | 推测语义 | 出处样本 |
|---------|---------|---------|
| 1 | 身法/位移专用事件（结束？衔接？） | 30433001（水身法） |
| **2** | **待源码确认**（B-003 起步，B-004 30532001 强化） | 30535000 / **30532001** |
| **3** | **待源码确认**（B-004 新，强化字典内已有） | **30532001 / 30221120** |
| 4 | 元素响应类事件 | 30534004 / 30531008 |
| **5** | **待源码确认**（B-003 新） | 30535000（土传承心法） |
| **6** | **待源码确认**（B-004 新，B-003 N-1 中频 81 hits） | **30532001 / 308072** |
| 7 | 攻击命中类事件 | 30534004 / 30531008 |
| **9** | **待源码确认**（B-004 新，B-003 N-1 中频 69 hits / 含 UNREG×2 同 ID 反复模式） | **30221000** |
| **11** | **待源码确认**（B-003 新） | 30535000 / 30531008 |
| 12 | 受击类事件 | 30534004 / 30531008 |
| **15** | **待源码确认**（B-004 高频 top miss / B-003 N-1 高频 148 hits） | **30532001（callback_id=225002099）** |
| **38** | **待源码确认**（B-003 新，hold-out 30214004 / 30315001 二阶印证） | 30325001 / 30214004 / 30315001 |
| 41 | 持续施法-按下 | 146003779（持续施法模板） |
| 42 | 持续施法-松开 | 146003779（持续施法模板） |
| 47 | 状态变化类事件 | 30534004 / 30531008 |

完整字典待 grep 源码（候选位置：`Assets/Scripts/Battle/.../EventConfig.cs` 或 `Assets/Scripts/CSGameShare/Hotfix/CSCommon/common.nothotfix.cs` 全局枚举段）。**B-004 强烈建议**：源码 grep 拿完整 Event ID 字典 + 对账 Excel `SkillEvent.xlsx`（B-004_actionable.md 已记录）。

---

## UNREG 节点字段语义（B-003 D-303 新增段）

`TSET_UNREGISTER_SKILL_EVENT` 节点（`SkillEffectType=69`）的字段语义：

- `SkillEffectType` = **69**（节点类型 ID，不是 Event ID）
- `Param[0].Value` = **目标 Event ID**（要解除注册的 Event ID）
- `Param[1].Value` = **目标 callback effect ID**（要解除的具体 callback effect 的 SkillEffectConfig.ID）

证据（B-003）：30531008 1 个 UNREG（5 REG + 1 UNREG）；30534004（B-002 已知）4 REG + 1 UNREG（rid=1045 UNREG ref=220005337 = rid=1040 的 SkillEffectConfig.ID）。

**用法**：审核 callback 链时，UNREG 是反向锚点——找到 UNREG.Param[1] 就能精确定位是哪个 REG 的 callback。这帮助处理 REG/UNREG 不平衡场景的对账。

### UNREG 反复模式（B-004 D-404 起步，B-005 D-505 批量化升级）

> 同一 `event_id` 被 UNREG / REG 多次操作 = 动态 callback 切换（可能是某状态机阶段切换时清旧 callback 再加新 callback）。**B-005 升级**：从"反向操作"概念升级为"实体级 SkillEvent 的事件订阅生命周期管理范式"——是法宝/装备型被动技能的标准实现手法。

**证据数据点**：

| 样本 | 类别 | 模式 | REG / UNREG 数 | 反复细节 |
|------|------|------|----------------|---------|
| 30534004 (B-002) | 火心法标签效果 | 4 REG / 1 UNREG | 异步清理（旧"不平衡"现象，非反复模式）|
| 30221000 (B-004) | 金宗门奇术1 长 CD 大招 | 1 REG / 2 UNREG | 单事件状态机阶段切换（同 event_id=9 反复）|
| **400019 (B-005)** | **法器真诀-纹章叠刃刺 (SubType=501)** | **11 REG / 10 UNREG** | **批量动态订阅管理：5 对 event_id=15 + 5 对 event_id=11 + 1 单 REG event_id=4** |

**v0.6 新主张（B-005 D-505 批量化升级）**：

> **UNREG 不是"反向操作"，是 REG callback effect 内部清理 SkillTag/Buff 的标准范式**——尤其在法宝/装备型被动当 buff_layer 数值变化或 SkillConfigData 比较结果切换时，**动态注册/反注册大量事件 = 实体级 SkillEvent 的"事件订阅生命周期管理"**。

**两类反复模式区分**：

1. **状态机阶段切换型**（30221000 单事件多反复）：技能在不同阶段（蓄力 / 释放 / 命中后）需要不同事件响应行为，通过反复 UNREG/REG 实现"事件钩子的动态切换"。判定信号：单 event_id 在 REG + UNREG 节点出现 ≥ 3 次。

2. **批量动态订阅管理型**（400019 N 对 REG/UNREG 同 event_id）：法宝/装备型被动当属性变化或某 SkillConfigData 比较结果切换时，需要**批量** 注册/反注册多组事件钩子。判定信号：N 对 REG/UNREG 同 event_id（**N ≥ 5 为强信号**），且 callback effect ID 多变（每对都不同）。

**判定信号（v0.6 升级）**：单技能内同 event_id 在 REG + UNREG 节点中出现 ≥ 3 次 = 状态机阶段切换；**N 对 REG/UNREG 同 event_id 且 N ≥ 5 = 批量动态订阅管理（法宝/装备型被动核心范式）**。审核时应特别关注：
- 切换时机和顺序（哪个状态触发批量切换？）
- callback effect ID 的差异化（每组 callback 的语义差别）
- 与 buff_layer / SkillConfigData 比较的耦合（参 [Buff系统.md](Buff系统.md)）

### §UNREG 反复模式 §边界段（v0.13 B-014 R1 D-1405 candidate / N 对 REG/UNREG 不必成对）

> **关键 hedge**（rule_3 v2 单证候选 / B-014 R1 2 例 + v0.6 D-505 ≥5 法宝/装备型被动核心范式的边界 / **不立即升 §UNREG 反复模式 §边界段为正式不变量** / 仅 candidate 注脚）

**B-014 R1 实证 v0.6 D-505 范式边界**（rule_3 v2 单证不升 / 仅 candidate 注脚 / candidate pending B-015+ 多证后才考虑升边界段为正式条款）：

| 样本 | 类别 | 模式 | REG / UNREG 数 | 边界细节 |
|------|------|------|----------------|---------|
| **2250030 (B-014 D-1405)** | **22xxx_7d 道具型 SubType=401** | **2 REG / 2 UNREG** | **N=2 < 5 不构成核心范式 / 但成对范式存在 / v0.6 D-505 范式边界向"小 N 道具型"方向扩展** |
| **4400001 (B-014 D-1405)** | **44xxx_7d BUFF 配置 SubType=0** | **6 REG / 0 UNREG** | **不必成对 / 多形态切换条件不需要 UNREG 反向操作 / v0.6 D-505 范式边界"BUFF 异化形态切换型"反例** |

**candidate 注脚（暂存不升）**：
- **N 对 REG/UNREG 不必成对 candidate**：v0.6 D-505 ≥5 法宝/装备型范式的边界
- **不需要 UNREG 反向操作的 BUFF 异化形态切换型 范式 candidate**：4400001 6 REG + 0 UNREG / 13 BuffConfig 异化形态 / TSCT_AND × 6 + TSCT_SKILL_CONFIG_DATA_COMPARE × 4 形态切换条件不需要 UNREG 反向操作
- rule_3 v2 单证候选 / 多证后才考虑升 §UNREG 反复模式 §边界段为正式条款 / candidate pending B-015+ 加固

**联动**：与模板系统页 §段位字典 v0.13 D-1401 22xxx_7d / 44xxx_7d 数据加固关联 / 与 SkillEntry 系统页 §SubType×Mode 矩阵 SubType=401 + SubType=0 + Mode A 实证关联

**数据来源**：[batch_buffer/B-014_read.json L item[0]](batch_buffer/B-014_read.json)（2250030 N=2 REG/UNREG 成对道具）+ [B-014_read.json L item[1]](batch_buffer/B-014_read.json)（4400001 6 REG + 0 UNREG 不必成对 BUFF 异化）+ [B-014_R1.yaml D-1405](batch_buffer/B-014_R1.yaml) + [B-014_auditor_verdict_r2.md](batch_buffer/B-014_auditor_verdict_r2.md)（auditor R0 ✓ + R2 ✓ 通过 / R1 沿用不动）

---

## 条件类节点 schema（v0.15 / 2026-05-13 memory 升级入库）

### TSCT_VALUE_COMPARE schema v3（终版 / 2026-05-12 校正）

> 来源：[memory/feedback_value_compare_schema.md](../../../memory/feedback_value_compare_schema.md) / 2026-05-12 配 30212018 时连续 3 版踩错。金标 30212010 320359。

**Params 顺序铁律**（V3 终版）：

| P# | 含义 | ParamType | 值 / 示例 |
|----|------|-----------|-----------|
| `P[0]` | 被比较值 NodeRef | **PT=2** (NodeRef) | `V=某 NUM_CALC 节点 ID` |
| `P[1]` | 比较操作符 op | PT=0 | **`1 = ==`** ⚠️ / 其他值待源码验证 |
| `P[2]` | target value | PT=0 | 常量数字 |

⚠️ **反直觉**：原始 v1 v2 都把 P[1]/P[2] 顺序写错（以为 P[1]=target P[2]=op），实际 **P[1]=op P[2]=target**。并且 **op=1 才是 ==，不是 0**。

**30212010 金标参考样本（多样本交叉验证）**：

```
320359 / Desc "判断传入数据 == 0"  ⭐ 最清晰
  P[0] = {Value=32003040, PT=2}    # NodeRef
  P[1] = {Value=1, PT=0}           # op = 1 (==)
  P[2] = {Value=0, PT=0}           # target = 0

320355 / Desc "本关卡 == 1"
  P[0] = NodeRef
  P[1] = {Value=1, PT=0}           # op = 1 (==)
  P[2] = {Value=1, PT=0}           # target = 1

# 30212010 内 320287 Desc 写 "==2" 但 P[1]=2 P[2]=0
# 是 Desc 笔误 / 还是 P[1]/P[2] 互换样本 — 不可信
# 以 320359 / 320355 为准
```

**Sensor**：节点"判断永远 true / 永远 false" → 第一时间 check VALUE_COMPARE Params 顺序对不对（终版：`P[1]=op=1`, `P[2]=target`）。

### ⭐ 配合 "REPEAT body 内 ADD-then-CONDITION" 模式

在 REPEAT 内做"每 N 次的第 K 次"判断（如"每 3 发的第 3 发强化"）的标准模式（按 30212010 镜像）：

```
REPEAT body ORDER Params = [
  ADD_SKILL_TAG (counter += 1),  # ⭐ ADD 在前
  CONDITION (counter % N == 0),  # ⭐ CONDITION 在后
]
```

VALUE_COMPARE target 配合：
- `counter % 3 == 0` → counter=3, 6, 9 时强化 → **第 3, 6, 9 次**强化（1-indexed）

⚠️ **反模式**：如果 body 顺序是 `[CONDITION, ADD]`（CONDITION 在前），counter 是 0-indexed (0..N-1)，target 要改成 N-1（如 N=3 时 target=2）才对。**用 30212010 一致的 ADD-then-CONDITION + target=0 是最稳的。**

### TSCT_VALUE_COMPARE 其他操作符（阶段 2 经验）

| op 值 | 含义 |
|------|------|
| **1** | == |
| **4** | ≥（>=） |
| 其他 | 待源码验证 |

实战范式（[模板系统.md §扇形分层弹幕 阶段 2.1](模板系统.md)）：`P0=count_1, P2=i, P1=4 → count_1 ≥ i → 内层`（反向比技巧 / 不需要猜 "≤" 是哪个值）。

详见 [节点字典.md §TSCT_VALUE_COMPARE](节点字典.md)。

---

## 反直觉点（容易踩的）

1. **callback 不是 lambda，必须 grep 外部节点** — REGISTER_EVENT 的 Param[1] 不能内联推断逻辑，必须在 flow 内反查 SkillEffectConfig.ID 对应节点。AI 闭卷预测时容易把 REG 当成"自包含的事件分支"——这是错的。

2. **REG 数 ≠ UNREG 数** — 30534004 4 REG / 1 UNREG。不要按"对称配对"思维去找 UNREG，引擎可能在技能销毁时自动清理。

3. **SkillEvent 不是 SkillConfig.SkillEffectPassive 的替代** — 二者并行：SkillEffectPassive 是 SkillConfig 顶层的"全局被动入口"；SkillEvent 是 effect 内部的"局部订阅"。一个标签效果型心法可以有 SkillEffectPassive（当 root）+ N 个 REGISTER（监听战场细节）。

4. **同一技能可注册多个 Event** — 30534004 注册 4 个不同 Event ID（4/7/12/47），不是配置错误，是核心机制的常态。一个心法监听 4 类战场事件以累计/响应不同状态。

---

## 与其他子系统的因果关系

- SkillEvent → **控制流子系统**（嵌套关系）：callback 内部跑 ORDER + DELAY + 其他控制原语 → 子系统嵌套
- SkillEvent → **SkillTag 系统**（跨系统读写）：Param[4] 配套 SkillTag 做触发标记；callback 内常 GET / MODIFY tag
- SkillEvent → **SkillEntry 系统**（并行关系）：与 SkillEffectPassive 并行——前者是局部订阅，后者是全局入口；模式 C 纯 Passive 心法靠 SkillEvent 触发
- SkillEvent → **模板系统**（典型耦合）：持续施法模板 146003779 内部用 SkillEvent 实现短按 / 长按分支，是模板内部的事件分支机制

---

## 仍不确定的地方

- **Event ID 完整字典**（B-004 已扩至 15 个值：1 / 2 / 3 / 4 / 5 / 6 / 7 / 9 / 11 / 12 / 15 / 38 / 41 / 42 / 47，B-003 N-1 corpus 顶 15/6/9 已命中，但 8/10/13/14/16+ 未观察值待 grep 源码）
- **每个 Event ID 的精确触发时机**（推测语义未经源码或实测验证）
- **Event 触发时序与 buffer_frame / 帧锚点的关系**
- **多 Event 注册时的执行顺序**（按注册顺序？按 Event ID 优先级？还是引擎并发触发？）
- **REG / UNREG 不平衡的引擎自动清理时机**（技能结束？销毁？切场景？）
- **callback effect ID 命名段位约定（B-004 D-410 新增）** — 4 样本 14+ callback_id 数据点观察：30532001 = 32000xxx（7 个）+ 225002099（1 个）混用；30221000 = 全 225xxx（225002040 / 225002075 / 225001886）；30221120 = 全 225xxx（225002338 / 225003073）；308072 = 440xxx（44011917）。**推测**：(a) **32xxx 段** = 通用 effect 编号（项目早期或公共池）；(b) **225xxx 段** = 与本技能 root（如 30221000 root=2250038）同段位 → 技能内/系列内私有 effect；(c) **440xxx 段** = 法宝/通用 buff 段。**不强制约定**，但"私有 effect 与 root 同段位"是常见做法。审核时如发现段位混用，需对照 effect_id 段位语义判断是引用通用还是私有 effect。

---

## 认知演变

- **v0.3（2026-05-09）首次建立**：B-001 hold-out 观察到 30531006 用 REGISTER_SKILL_EVENT，但样本不足以建页（仅 1 数据点）。B-002 通过 146003779 + 30433001 + 30534004 三样本（共 7 Event ID 数据点）支撑建页：明确 REG 节点字段语义、callback 外部引用规则、REG/UNREG 不平衡反直觉。出处：B-002 D-205（[B-002.yaml F-5](batch_buffer/B-002.yaml)）。
- **v0.3 hold-out 旧表述存档**（搬迁自 B-003 D-303 conflict_flag）：v0.3 hold-out 验证（30331000 / 30315001）阶段曾推测"EvType=68 是 Event ID"——这是把节点 data 顶层 `SkillEffectType=68`（REG 节点类型 ID）误读为 Event ID。**v0.3 字段语义本身不错**（写的是"`Param[0]` = Event_ID 全局枚举"），但 hold-out yaml 推测段落把"EvType"当成了 Event ID 概念。该旧推测属概念混淆，已在 v0.4 通过 §字段语义段彻底澄清。
- **v0.3 → v0.4（2026-05-09）字段语义彻底澄清 + Event ID 字典翻倍 + UNREG 段新建**：B-003 D-303 通过 4 阶证据（30535000 3 REG event_id=11/5/2 全字典外 + 30531008 5 REG + 1 UNREG event_id=12/11/4/7/47 + UNREG SkillEffectType=69 + 30325001 1 REG event_id=38 + 30214004/30315001 hold-out 二阶印证）：(a) 新增 §字段语义段澄清 SkillEffectType=节点类型 ID（68=REG / 69=UNREG）vs Param[0]=真 Event ID；(b) 字典扩 7 → 11 个（新增 2/5/11/38）；(c) 新建 §UNREG 字段语义段（SkillEffectType=69 / Param[0]=目标 Event ID / Param[1]=目标 callback effect ID）。**confidence 中 → 高**（4 阶证据 + 11 数据点 + 字段语义彻底澄清）。出处：B-003 D-303（[B-003.yaml D-303](batch_buffer/B-003.yaml)）。

- **v0.4 → v0.5（2026-05-10）Event ID 字典再扩 11 → 15 + UNREG 反复模式 + callback effect ID 段位约定观察**：B-004 D-404 + D-410 通过 4 阶证据（30532001 8 REG callback_id=32000xxx × 7 + 225002099 × 1 / event_id=15 命中 + 6 + 2 + 3 / 30221000 3 REG callback_id 全 225xxx / event_id=9 + UNREG × 2 反复模式 / 30221120 callback_id 全 225xxx / 308072 callback_id=44011917）：(a) Event ID 字典扩 11 → 15（新增 15 / 6 / 9 + 强化 3/2，命中 B-003 N-1 顶部 top miss 148 hits）；(b) §UNREG 段加"UNREG 反复模式"子段——同一 event_id 被 UNREG/REG 多次 = 动态 callback 切换（推测状态机阶段切换时清旧加新），与单纯 REG/UNREG 不平衡（异步清理）不同；(c) §仍不确定 加 D-410 callback effect ID 段位约定观察（32xxx 通用池 / 225xxx 与 root 同段位私有 / 440xxx 法宝/通用 buff），不强制约定但常见做法。confidence 高 → 高（保持，4 阶证据 + 15 数据点 + 9 样本累计）。出处：B-004 D-404 + D-410（[B-004.yaml](batch_buffer/B-004.yaml)）。

- **v0.5 → v0.6（2026-05-10）UNREG 反复模式批量化升级**：B-005 D-505 通过 400019（法器真诀-纹章叠刃刺，SubType=501，11 REG + 10 UNREG = 5 对 event_id=15 + 5 对 event_id=11 + 1 单 REG event_id=4）：

  **(a) §UNREG 反复模式段批量化升级**：从"反向操作"概念（v0.5 D-404 单观察 30221000 1 REG/2 UNREG）升级为"实体级 SkillEvent 的事件订阅生命周期管理范式"。新主张："**UNREG 是 REG callback effect 内部清理 SkillTag/Buff 的标准范式**——法宝/装备型被动当属性变化或某 SkillConfigData 比较结果切换时，**动态注册/反注册大量事件 = 实体级 SkillEvent 的事件订阅生命周期管理**"。

  **(b) §UNREG 反复模式 两类区分**：
  - 状态机阶段切换型（30221000 单事件多反复）
  - 批量动态订阅管理型（400019 N 对 REG/UNREG 同 event_id，N ≥ 5 强信号）

  **(c) §UNREG 反复模式 判定信号升级**：从"单 event_id 出现 ≥ 3 次"升级到"N 对 REG/UNREG 同 event_id 且 N ≥ 5 = 批量动态订阅管理（法宝/装备型被动核心范式）"。

  confidence 高 → 高（保持，B-005 是对 v0.5 D-404 的批量化升级而非反转）。出处：B-005 D-505（[batch_buffer/B-005.yaml](batch_buffer/B-005.yaml)）。

- **v0.6 → v0.13（2026-05-10）B-014 R1 R2 D-1405 §UNREG 反复模式 §边界段 candidate / N 对 REG/UNREG 不必成对（v0.6 D-505 范式边界 candidate）**：B-014 R1 通过 2 训练样本（2250030 22xxx_7d 道具型 SubType=401 + 2 REG / 2 UNREG 成对范式 / N=2 < 5 + 4400001 44xxx_7d BUFF 配置 SubType=0 + 6 REG / 0 UNREG 不必成对）：

  **(a) §UNREG 反复模式 §边界段 candidate 注脚（不立即升正式 / rule_3 v2 单证候选 / candidate pending B-015+ 多样本加固）**：
  - **N 对 REG/UNREG 不必成对 candidate**：v0.6 D-505 ≥5 法宝/装备型被动核心范式的边界（B-014 4400001 6 REG + 0 UNREG 反例）
  - **小 N 道具型成对范式 candidate**：v0.6 D-505 范式向"小 N 道具型"方向扩展（B-014 2250030 N=2 < 5 道具型 SubType=401 成对范式存在）
  - **不需要 UNREG 反向操作的 BUFF 异化形态切换型 范式 candidate**：4400001 6 REG + 0 UNREG / 13 BuffConfig 异化形态 / TSCT_AND × 6 + TSCT_SKILL_CONFIG_DATA_COMPARE × 4 形态切换条件不需要 UNREG 反向操作

  **(b) 与模板系统 §段位字典 v0.13 D-1401 22xxx_7d / 44xxx_7d 数据加固关联**：22xxx_7d 道具型段位 + 44xxx_7d BUFF 配置段位的 REG/UNREG 模式实证

  **(c) 与 SkillEntry 系统页 §SubType×Mode 矩阵 v0.13 D-1403 实证加固关联**：SubType=401 道具型 + SubType=0 BUFF 配置 + Mode A 实证

  **状态**：仍 candidate pending B-015+ 加固（rule_3 v2 单证 / 不升 §UNREG 反复模式 §边界段为正式条款 / 仅 candidate 注脚 / 多证后才考虑升 / 候选 pending B-015+）

  confidence 高 → 高（保持，B-014 是 v0.6 D-505 范式边界 candidate 不动核心 / D-505 N≥5 强信号判定不动）。出处：B-014 R1 D-1405（[batch_buffer/B-014_R1.yaml](batch_buffer/B-014_R1.yaml)）+ [B-014_auditor_verdict_r2.md](batch_buffer/B-014_auditor_verdict_r2.md)（auditor R0 ✓ + R2 ✓ 通过 / R1 沿用不动）

---

## 引用样本与源码

**真实样本**：
- `{{SKILLGRAPH_JSONS_ROOT}}技能模板/SkillGraph_146003779_*.json` — 持续施法模板内部 REG Event ID 41 / 42（短按 / 松开）
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30531006_*.json` — 金心法标签效果（hold-out）
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30433001_*.json` — 水身法 REG Event ID 1（身法专用）
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30534004_*.json` — 火心法标签效果 4 REG（Event ID 12 / 7 / 4 / 47）+ 1 UNREG
- `{{SKILLGRAPH_JSONS_ROOT}}法宝/SkillGraph_400019_*.json` — **B-005 批量动态订阅管理范式**（11 REG + 10 UNREG = 5 对 event_id=15 + 5 对 event_id=11 + 1 单 REG event_id=4）

**B-014 R1/R2 §UNREG 反复模式 §边界段 candidate 样本（D-1405 / N 对 REG/UNREG 不必成对）**：
- `{{SKILLGRAPH_JSONS_ROOT}}通用模板/搜打撤/SkillGraph_2250030_*.json` — **22xxx_7d 道具型 SubType=401 / 2 REG + 2 UNREG 成对范式 / N=2 < 5 不构成 v0.6 D-505 核心范式 / 但成对范式存在 → v0.6 D-505 范式向"小 N 道具型"方向扩展 candidate**
- `{{SKILLGRAPH_JSONS_ROOT}}通用BUFF/挑战妖王/SkillGraph_4400001_*.json` — **44xxx_7d BUFF 配置 SubType=0 / 6 REG + 0 UNREG 不必成对 / 13 BuffConfig 异化形态 / TSCT_AND × 6 + TSCT_SKILL_CONFIG_DATA_COMPARE × 4 形态切换条件不需要 UNREG 反向操作 → BUFF 异化形态切换型不必成对 candidate**

**源码**（待读 / grep）：
- `Assets/Scripts/Battle/.../EventConfig.cs` 或类似（Event ID 完整枚举字典候选）
- `Assets/Scripts/CSGameShare/Hotfix/CSCommon/common.nothotfix.cs` — 可能含 SkillEvent 相关枚举
- `HEngine/.../` — Event 触发时序的 C++ 实现（参考 PostMortem #026 类似引擎层硬规则）

**Excel 表**（B-003+ 待对账）：
- `{{SKILL_EXCEL_DIR}}/SkillEvent.xlsx` — 技能事件配置表（README §11 等级 2 注明"运行时实际数据可能覆盖编辑器参数"）

**关联文档**：
- [SkillEntry系统.md](SkillEntry系统.md) — 模式 C 纯 Passive 心法靠 SkillEvent 触发；SkillEffectPassive 与 SkillEvent 并行
- [SkillTag系统.md](SkillTag系统.md) — Event Param[4] 配套 SkillTag 触发标记
- [模板系统.md](模板系统.md) — 持续施法模板内部用 SkillEvent 实现短/长按分支
- [控制流子系统.md](控制流子系统.md) — callback 内部跑控制原语
- [节点字典.md](../docs/节点字典.md) — TSET_REGISTER_SKILL_EVENT / TSET_UNREGISTER_SKILL_EVENT 字段
