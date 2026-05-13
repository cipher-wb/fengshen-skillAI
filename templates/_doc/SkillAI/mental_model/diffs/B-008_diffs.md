# B-008 9 样本闭卷 vs 开卷 DIFF + sample_score

> 4 维度评分（每维 0-1，加权平均 = sample_score）：
> - **节点数**（0.20）：估算 vs 实际节点数 误差
> - **拓扑**（0.30）：核心 mermaid 形态命中
> - **模板/类型**（0.30）：predicted_classification 与 actual 编码命中
> - **子系统覆盖**（0.20）：touched_subsystems 命中

---

## 样本 1: 301903【金宗门】须弥功法

### Predicted vs Actual

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 2 | 2 (refs=2) | ✓ 满分 |
| 拓扑 | SkillConfig + 单节点 | SkillConfig + TSET_ORDER_EXECUTE | ⚠ 部分（不是 Buff/Tag 是 ORDER_EXECUTE 空容器） |
| 类型 | deprecated_old_xinfa_skeleton (type C 极简占位) | Mode C 极简 + passive_root=94000995 → 外部 buff_id | ✓ 完全命中（passive_root 真不为 0） |
| 子系统 | SkillEntry, Buff | SkillEntry（passive_root 指向外部 buff，本文件无 buff 实体） | ✓ 满分（修正：本文件无 buff 实体，外部引用） |

**关键发现 1**：passive_root=94000995 但本文件**只有 1 个 ORDER_EXECUTE 空容器**，无 BuffConfig 节点。
→ 印证我的假说：deprecated 老心法 = passive_root 指向外部 buff_id，本文件仅 SkillConfigNode 占位。

**sample_score**: 0.20×1.0 + 0.30×0.7 + 0.30×1.0 + 0.20×1.0 = **0.91**

---

## 样本 2: 303921【水宗门】鱼灵法

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 3 | 3 | ✓ 满分 |
| 拓扑 | SkillConfig + Buff + tail | SkillConfigNode + TSET_ADD_BUFF + BuffConfigNode | ✓ 满分 |
| 类型 | deprecated_old_xinfa_with_buff_skeleton | Mode C + passive_root=108024555 + 含 buff 实体 | ✓ 命中 |
| 子系统 | SkillEntry, Buff | SkillEntry, Buff | ✓ 满分 |

**关键发现 2**：303921 与 301903 不同——本文件**含**完整 buff 实体（BuffConfig + ADD_BUFF），passive_root 指向 108024555 是技能内部 buff。
→ Mode C 心法两种亚态：(a) 仅占位 (301903) (b) 含 buff 实体 (303921)。

**sample_score**: 0.20×1.0 + 0.30×1.0 + 0.30×1.0 + 0.20×1.0 = **1.00**

---

## 样本 3: 720001 灵宠光环-猪1

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 3 | 3 | ✓ 满分 |
| 拓扑 | SkillConfig + Buff + effect/attr | SkillConfigNode + TSET_ADD_BUFF + BuffConfigNode | ✓ 满分（与 303921 同形态） |
| 类型 | lingchong_aura_xinfa（极简光环型） | Mode C + passive_root=72000002 + buff 实体 | ✓ 命中 |
| 子系统 | SkillEntry, Buff | SkillEntry, Buff | ✓ 满分 |

**关键发现 3**：720001（活的灵宠光环）与 303921（废弃宗门心法）**节点完全同构**！
→ "废弃 vs 活" 路径不影响形态结构，passive_root + buff 实体是 Mode C 心法核心范式。

**sample_score**: 0.20×1.0 + 0.30×1.0 + 0.30×1.0 + 0.20×1.0 = **1.00**

---

## 样本 4: 350011 神位技能-1

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 1 | 1 | ✓ 满分 |
| 拓扑 | 仅 SkillConfigNode | 仅 SkillConfigNode | ✓ 满分 |
| 类型 | test_placeholder_subtype_1101 / type1 候选 | refs=1 + 全空 + SubType=1101 测试占位 | ✓ 命中 |
| 子系统 | SkillEntry | SkillEntry | ✓ 满分 |

**关键发现 4**：refs=1 = 文件**只有 SkillConfigNode 1 个节点**！这种"极简骨架"在 corpus 仅 350011/350012 两例。
→ type1_pure_empty_shell 阈值 refs ≤ 2 涵盖该样本（1 ≤ 2 ✓）

**sample_score**: 0.20×1.0 + 0.30×1.0 + 0.30×1.0 + 0.20×1.0 = **1.00**

---

## 样本 5: 1860213【BUFF】训练场无敌buff

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 3 | 3 | ✓ 满分 |
| 拓扑 | SkillConfig + Buff（无 effect_list）+ attr | SkillConfigNode + 2× BuffConfigNode（无任何 effect） | ⚠ 部分（实际是 2 个 buff 不是 1 + attr） |
| 类型 | type9_buff_meta_only（候选新主轴） | Mode E + 2× buff 实体（refs=3）+ 无外驱 | ✓ 命中（buff 元数据型成立） |
| 子系统 | SkillEntry, Buff | SkillEntry, Buff | ✓ 满分 |

**关键发现 5**：1860213 含 **2 个 BuffConfigNode**，无 ADD_BUFF 引用、无 effect_list。
→ 这是"buff 数据容器型"——文件作为 buff 配置数据库，不主动调用，可能被外部技能 ADD_BUFF 引用。

**sample_score**: 0.20×1.0 + 0.30×0.7 + 0.30×1.0 + 0.20×1.0 = **0.91**

---

## 样本 6: 940068【天命气运】伙伴同心

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 9 | 9 | ✓ 满分 |
| 拓扑 | SkillConfig + Buff + 数个 attr_modify/SkillTag | ORDER_EXECUTE + SkillConfig + DELAY_EXECUTE + SELECT_CIRCLE + ADD_BUFF + RUN_SKILL_EFFECT + GET_PLAYER + GET_ATTR + Buff | ⚠ 部分（含 SELECT_CIRCLE 选择 + DELAY 延迟 + GET_ATTR 是中等流程，不是单纯 buff_meta） |
| 类型 | type9_buff_meta_with_attrs (候选 type9 中等变体) | 不像 type9_meta，更像 type5 边缘大型 OR type-new "buff 触发流程型" | ✗ 错（不是 buff_meta） |
| 子系统 | SkillEntry, Buff, SkillTag | SkillEntry, Buff（无 SkillTag） | ⚠ 部分 |

**关键发现 6**：940068 不是预测的"buff_meta_with_attrs"——而是**有完整流程的中等技能**（ORDER → 选择圆形 → 延迟 → 加 buff → 运行 effect → 获取属性）。is `flow chain w/ buff` 形态，refs=9 < type5 阈值 30，不命中 type5；不命中现有 type1-8。**真 UNKNOWN**。

→ 揭示：`min_buff_no_drive` 组（has_buff + 无外驱事件）实际**含两类**：
- (a) 真 buff_meta（1860213 类纯数据容器）
- (b) 主动流程加 buff（940068 类，有选择/延迟/属性获取链）
→ 预测 type9 偏差，分组太粗。

**sample_score**: 0.20×1.0 + 0.30×0.4 + 0.30×0.3 + 0.20×0.6 = **0.53**

---

## 样本 7: 940058【天命气运】九转还魂丹

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 3 | 3 | ✓ 满分 |
| 拓扑 | SkillConfig + 2 不识别低层节点 | ORDER_EXECUTE + SkillConfigNode + TSET_LJ_RESIST_PLAYER_DIE | ⚠ 部分（有特殊节点 TSET_LJ_RESIST_PLAYER_DIE 抗死亡） |
| 类型 | type10_pure_placeholder | 实际是 "**抗死亡复活效果**" 单功能型（不是占位，是真功能） | ✗ 错（功能性错位） |
| 子系统 | SkillEntry | SkillEntry, 死亡复活子系统？ | ⚠ |

**关键发现 7**：TSET_LJ_RESIST_PLAYER_DIE 是论剑玩法专属"抗死亡"节点 —— 这不是占位，是**单功能型 Mode E**：有特殊业务节点直接做事，不需要 buff/事件包装。
→ 揭示 `small_no_signals` 组（全 0 flag）含一类"**单业务节点直接执行型**"，flags 检测漏（因 LJ_RESIST_PLAYER_DIE 不在 flag 列表）。

**sample_score**: 0.20×1.0 + 0.30×0.5 + 0.30×0.2 + 0.20×0.6 = **0.49**

---

## 样本 8: 1750104【测试】玩家训练场关卡效果

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 13 | 13 | ✓ 满分 |
| 拓扑 | SkillConfig + 数个 REGISTER + callback 容器 | SkillConfig + 4× ORDER_EXECUTE + REGISTER + ENTITY_REBORN + DELAY + ADD_SKILL_TAG + CREATE_EFFECT + ModelConfig + 2× GET_ATTR | ✓ 满分（命中 REGISTER 链 + 多分支） |
| 类型 | type11_event_only_listener (候选) | Mode E + REGISTER + 复活/特效/Tag 注册多功能链 | ✓ 命中（事件监听 + 多副作用） |
| 子系统 | SkillEntry, SkillEvent | SkillEntry, SkillEvent, （特效/Tag） | ✓ 满分 |

**关键发现 8**：1750104 验证 type11_event_only_listener 候选：has_reg_event=true + 无 buff 包裹（与 type3b 区分）+ 多种副作用（复活/Tag/特效）。
→ type11 候选可成立，差异于 type3b（必有 buff 包裹）。

**sample_score**: 0.20×1.0 + 0.30×1.0 + 0.30×1.0 + 0.20×1.0 = **1.00**

---

## 样本 9: 1290141【模板】抛物线锁敌目标

| 维度 | 闭卷预测 | 开卷实测 | 命中 |
|------|---------|---------|------|
| 节点数 | 121 | 121 | ✓ 满分 |
| 拓扑 | type7 边缘 OR template_body | TSCT_VALUE_COMPARE×24 + GET_ATTR×24 + NUM_CALC×21 + GET_ANGLE×16 + AND×14 + CONDITION_EXECUTE×8 + MODIFY_ATTR×8 + REPEAT 1 | ⚠ 部分（不是属性批量计算 type7，是**条件筛选/角度评估矩阵**） |
| 类型 | type7 边缘 (modify_attr 8 + num_calc 21 = 29 接近阈值 30) | 真实形态：**目标筛选评估器**（用条件树 + 角度 + 属性 评判候选目标） | ✗ 错（不是 type7） |
| 子系统 | SkillEntry, 模板系统 | SkillEntry, **目标筛选/条件子系统**（新候选） | ⚠ |

**关键发现 9**：1290141 IsTemplate=False（虽然名字含"【模板】"和路径含"通用模板"！）—— 这是关键反例：
1. **路径/名字含"模板"≠ IsTemplate=True**（模板可能是技能实例引用）
2. 真实形态是**目标筛选评估矩阵**：通过角度 + 属性 + 条件 AND 树 决定哪些目标"中弹"
3. corpus large_refs_unknown 组 3 例（1290141 / 1290148 / 1860215）极有可能是同类——target selector / condition evaluator 模板
4. 这是新候选 type12_target_selection_evaluator

**sample_score**: 0.20×1.0 + 0.30×0.5 + 0.30×0.2 + 0.20×0.6 = **0.49**

---

## 批次平均 sample_score

| 样本 | score |
|------|-------|
| 301903 | 0.91 |
| 303921 | 1.00 |
| 720001 | 1.00 |
| 350011 | 1.00 |
| 1860213 | 0.91 |
| 940068 | 0.53 |
| 940058 | 0.49 |
| 1750104 | 1.00 |
| 1290141 | 0.49 |

**batch_accuracy = (0.91+1.00+1.00+1.00+0.91+0.53+0.49+1.00+0.49) / 9 = 7.33 / 9 = 0.814**

学习曲线：…→ 0.969 → 0.823 → 0.861 → 0.778 → **0.814**

---

## 4 RQ 答案（验证后）

### RQ-B8-1 Mode C/E 切换条件 — 闭环答案 ✓

**答案**：Mode C/E 不是切换关系，是**正交字段定义**。
- Mode C 定义：`SkillEffectExecuteInfo.SkillEffectConfigID == 0` AND `SkillEffectPassiveExecuteInfo.SkillEffectConfigID != 0`
- Mode E 定义：两者都 == 0（fallback）
- v0.7 D-603-R1 corpus refs 完全重叠的真因：**Mode C 不是单一形态**，含至少 4 亚态：
  1. **deprecated 老心法占位**（301903 类，passive_root 指外部 buff，本文件 ≤ 2 节点）
  2. **完整心法 + 内嵌 buff 实体**（303921 类，passive_root 指本文件 buff，refs 3-30）
  3. **灵宠光环型**（720001 类，与亚态 2 同构但活的）
  4. **法宝/装备被动**（已学样本 400019/400035 大型，refs > 50）

→ Mode C "极小 refs 重叠 Mode E" 是**因为亚态 1 + 亚态 3 集中在 refs 2-7**，与 Mode E 的真技能 19 例 refs 跨度重叠是表象，本质上 Mode C 是 passive 入口形态，Mode E 是双 0 fallback，**两者从字段定义就互斥**。

### RQ-B8-2 长尾 SubType 形态 — 部分答案

**SubType=1101**：跨形态泛用（4 例 = 化身实战 309000/309001 Mode A + 神位测试 350011/350012 极简 refs=1）
**SubType=1001**：corpus 仅 1 例 940107（已学），无新候选样本可调研 → 真 deprecated 长尾，未来 B-009+ 视新增样本再决定
**结论**：SubType 长尾本身不是问题，每个 SubType 内部按 Mode + flags 进一步分形态。

### RQ-B8-3 70 例 UNKNOWN 形态扩展 — 部分答案

| 候选新 type | 样本验证 | corpus 估计 | rule_4 状态 |
|------------|---------|-----------|-----------|
| type9_buff_meta_only | 1860213 ✓ | 5-10 例 | 待 .py 编码 has_buff + 无 effect_list + 无 reg_event + refs ≤ 5 + buff_count ≥ 1 |
| type10_pure_placeholder | 350011 ✓ + 940058 ✗ | 极少 | 940058 显示"全 0 flag"组实际是异质混合，需细分子型 |
| type11_event_only_listener | 1750104 ✓ | 3-8 例 | 待 .py 编码 has_reg_event + 无 has_buff + 多副作用节点（与 type3b 区分） |
| type12_target_selection_evaluator | 1290141 ⚠ | 3-5 例（large_refs_unknown 组） | 候选新型：TSCT_VALUE_COMPARE + GET_ANGLE/ATTR 大量 + CONDITION_EXECUTE 链 |
| type-new_business_node_direct | 940058 ⚠ | 难估（特殊业务节点白名单依赖） | LJ_RESIST_PLAYER_DIE 等特殊节点单独执行型；需扩 flag 白名单 |
| type-new_active_buff_chain | 940068 ⚠ | mid_refs UNKNOWN 中含 buff 子集 | "选择 + 延迟 + ADD_BUFF + 副作用" 完整流程，refs 9-15 |

**结论**：70 例 UNKNOWN 中至少 4 类候选成立，但需要 `_skill_config_extractor.py` 工具链扩展 flag 白名单（业务节点 / 节点 sequence 模式识别）才能达到 rule_4 .py 可重现。**保守估计 B-008 后能再编码 15-25 例**，覆盖率 65.7% → **70-75%**。

### RQ-B8-4 candidate-0.5 整体收敛评估 — 部分收敛

**已完成**：
- B-006 R1：5 类编码 60.3%（type1-5 主轴）
- B-007 R1：7 主轴 + 2 罕见 65.7%（type1-6 + type7/8）
- B-008：揭示 type9-12 候选 + Mode C 4 亚态 + Mode C/E 字段定义本质

**未完成**：
- type9-12 需 _skill_config_extractor.py 工具链扩展（业务节点白名单 / sequence 识别）
- 70 例 UNKNOWN 中可能仍有"业务专属节点"型（940058 LJ_RESIST_PLAYER_DIE 类）—— 形态分散难以统一编码

**建议**：candidate-0.5 **建议收尾**进入 main，B-009 转**工具链强化批次**（合并 _skill_config_extractor.py + 加 type9-12 启发式），不再纯样本调研。
