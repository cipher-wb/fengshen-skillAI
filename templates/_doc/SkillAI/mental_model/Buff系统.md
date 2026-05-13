---
subsystem: Buff 系统
confidence: 高
confidence_history: [v0.2 初建=中, v0.2 hold-out 后=低（仅 1 样本范化，反例已现）, v0.3 B-002 后=中（4 样本反直觉 3 精准化让认知收敛）, v0.4 B-003 后=高（不变量 1 修订让 BuffConfigNode 必填误解被修正 + ADD_BUFF.Params 字段语义初探）, v0.5 B-004 后=高（关键不变量 3 加注 buff_layer 不限心法跨 SubType 通用）, v0.11 B-012 R1 R2 后=高（候选 §Z Buff 层数化机制候选段加注脚 30524001 灼伤单证实证 / rule_3 v2 单证不升字典 / 候选 pending B-013+ ≥3 多样本加固 / 不升正式不变量 / 不建独立子系统页）]
last_review: 2026-05-10
related_postmortems: []
holdout_v0.2_findings: 已在 B-002 D-204 解决（详见认知演变段）
related_samples:
  - SkillGraph_30531005_【金宗门】传承心法_强化普攻3.json
  - SkillGraph_30431000_【金宗门】枪影阻敌_身法_天阶.json
  - SkillGraph_30234006_【火宗门】炎龙噬天_天阶_蓄炎流.json
  - SkillGraph_30222002_【木宗门】落木遁形_奇术.json
  - SkillGraph_30215001_【土宗门】奔岩突进_人阶_奇术.json
  - SkillGraph_30433001_【水宗门】身法_天阶_潜行水底.json
  - SkillGraph_30134001_【火宗门】天阶功法_普攻.json
  - SkillGraph_30214004_【火宗门】人阶多段连击_蓄力.json
  - SkillGraph_30531008_【金宗门】标签效果_蓄势.json
  - SkillGraph_30324002_【火宗门】焚天_地阶_焚骨流.json
  - SkillGraph_30325001_【土宗门】天坠石牢_地阶_神通.json
  - SkillGraph_30535000_【土宗门】传承心法_天阶_土系传承心法.json
  - SkillGraph_30532001_【木宗门】青藤之力_心法.json
  - SkillGraph_30221000_【金宗门】奇术1_地阶_长CD大招.json
  - SkillGraph_308072_青木天葬_法宝.json
  - SkillGraph_1750087_招魂台胜利Buff.json
  # B-007 R0 (BUFF 反例 + 反例邻样本，2026-05-10)
  - SkillGraph_1900111_剧情BUFF触发.json   # type3b ∩ type6 复合（multi_overlap 反例 / sample_score=0.688）
  - SkillGraph_1900093_剧情BUFF特效.json   # type3b 子型 b2 effect_anim（sample_score=0.875）
  - SkillGraph_1860234_剧情BUFF碰撞控制.json  # type3b 子型 b3 collision（sample_score=1.000 ⭐ / SET_COLL×12 + UNREG 范式）
  - SkillGraph_940107_全死气死气版本.json   # type3a 阈值放宽证据 + SubType=1001（buff_with_effect_list=True / refs=66）
  # B-008 R1 (active_buff_chain 罕见模式 / D-805-R1 跨子系统定位收敛，2026-05-10)
  - SkillGraph_940068_天命气运_伙伴同心_流程加buff.json    # active_buff_chain 罕见模式（refs=9 单例 / 中等流程 + ADD_BUFF + 副作用 / 与 type4/7/8 范式一致 / 不升 §6 第三独立轴）
  # B-012 R1/R2 (D-1204 层数化 Buff 候选首次实证，2026-05-10)
  - SkillGraph_30524001_火宗门标签效果灼伤.json  # SubType=0 Mode C / 91 节点 / 8 GET_BUFF_LAYER_COUNT + 8 ADD_BUFF + 8 VALUE_COMPARE + 6 NUM_CALCULATE + 2 REPEAT_EXECUTE + 1 REGISTER_SKILL_EVENT 灼伤范式（攻击触发增层 + 周期掉血 + 层数到伤害公式）/ 单证候选不升字典
mental_model_version: v0.11
---

## 一句话本质

Buff 系统是与 [SkillTag 系统](SkillTag系统.md) **并列**的状态/计层系统，不应混入 SkillTag。**buff 真实定义在 Excel 表 `Buff/BuffConfig.xlsx`（运行时寻址，权威定义）**；flow 内 `BuffConfigNode` 仅是编辑器侧的元数据快照 / 调试占位；`buff_layer` 是叠层数；`EnhanceSkillBuffConfigID` 是心法→buff 的反向引用（"我是哪个 buff 触发的派生技能"）。**心法用 buff 计层；身法用 buff 串联控制效果**——两种典型用法都不是"挂一个有时长的 debuff"那么简单。

---

## 关键不变量（违反就 100% 出问题）

1. **buff 权威定义在 Excel 表，flow 内 BuffConfigNode 是元数据快照**（B-003 D-304 重写）：
   - **`TSET_ADD_BUFF.Params[2].Value` = 全局 BuffConfig 表 ID（运行时寻址，权威定义）** — buff 真实定义在 Excel 表 `Buff/BuffConfig.xlsx`
   - **`BuffConfigNode`（flow 内）= 编辑器侧的 buff 元数据快照 / 调试占位**（含 BuffNameKey / EffectID / Icon / IsShowIcon 等编辑器字段，方便编辑器 inspector）
   - **flow 内 BuffConfigNode 可选**：
     - 本技能新建的 buff（44xxxx / 22xxxx 段）通常会加节点（方便编辑器 inspector）
     - 引用通用/已有 buff（如 10000 / 跨技能 220xxxx）→ 不在 flow 内加节点
     - 同一 buff 多次 ADD_BUFF 加层 → 仅一个 BuffConfigNode 节点（30531008 4 ADD_BUFF 同 buff 2250124 / 1 BuffConfig）
   - **比例约束**：
     - flow 内独立 buff 种类数 ≤ BuffConfigNode 数（每本技能新建 buff 应有 BuffConfigNode）
     - ADD_BUFF 节点数 ≥ 独立 buff 种类数（同一 buff 可多次触发加层）
   - **v0.7 B-006 R1 注脚（D-605-R1）**：BUFF 类 Mode E 真技能（type3, corpus 9 例 / 4.4%）入口**至少 2 子模式**——见 §仍不确定 待验证项 + [SkillEntry系统.md §仍不确定 §7](SkillEntry系统.md) type3 编码描述。Buff 系统主不变量本身不动；判定 Mode E 入口子模式时需 cross-check BuffConfigNode 字段 + REGISTER_SKILL_EVENT 节点。
   - **v0.8 B-007 R1 注脚（D-702 闭环）**：v0.7 "至少 2 子模式 a/b 互斥" 软化为"**两独立轴 + 重叠常见**"——
     - **轴 a（内驱）**：buff_with_effect_list=True（BuffConfig.SkillEffectListOnStart/Loop/End 任一非空），corpus 13 例（v0.8 阈值放宽 50→300 + 4 例新增）
     - **轴 b（外驱）**：has_register_skill_event=True（外部 SkillEvent 订阅触发回调），corpus 18 例（v0.8 阈值放宽 50→300）
     - **两轴可同时为 True**（剧本战斗常见）— corpus a∩b 真重叠 6 例（auditor R0 验证补强）：940086 / 1750001 / 1750087 / 1860401 / 1900097 / 30522011
     - **核心修订**：BUFF 入口 = 两独立轴的并集而非互斥子类。判定 Mode E 入口子模式时不应将 a/b 视为互斥分类。
     - 详见 §仍不确定 §6 v0.8 闭环 + [SkillEntry系统.md §仍不确定 §7 v0.8 进展段](SkillEntry系统.md)。

2. **核心三件套节点**：
   - `TSET_GET_BUFF_LAYER_COUNT` — 读 buff 层数
   - `TSET_ADD_BUFF` — 添加 buff
   - `TSET_REMOVE_BUFF` — 移除 buff

3. **心法判定铁律：OR 两类**（B-003 D-307 修订，B-004 D-405 加注 buff_layer 跨 SubType 通用 ≠ 心法标志）：
   - **(a) 替换型普攻心法**：CdType=4 + EnhanceSkillBuffConfigID ≠ 0 + 文件名含"心法/功法-普攻"（30531005 = 2250099）
   - **(b) 标签效果型心法 / 被动型功法**：CdType=0 + Mode C 纯 Passive + **EnhanceID 通常 = 0** + 文件名含"心法/传承/标签效果"（30534004 / 30531006 / 30535000 / 30531008）

   **判定原则**：心法判定不能仅看 `EnhanceSkillBuffConfigID`！需 OR 两个条件——非 0 是替换型；CdType=0 + Mode C 纯 Passive + 文件名含心法关键字 = 被动型（EnhanceID=0 也是合法的心法）。**单条件硬判会漏掉所有标签效果型心法**（4 阶证据：30534004 / 30531006 / 30535000 / 30531008 全 EnhanceID=0）。

   **B-004 D-405 加注（buff_layer ≠ 心法标志）**：`buff_layer` 操作（GET_BUFF_LAYER_COUNT / 计层逻辑）**跨 SubType 通用**，不能反推心法身份：
   - 30221000（**SubType=102 主动技 / CdType=1 长 CD 大招**）— has_get_buff_layer=true，buff_id 串 2250064~2250099 + 660033
   - 308072（**SubType=303 法宝召唤型**）— has_get_buff_layer=true，buff_id 440526
   - 30531005（心法 / B-001 已学）— buff_layer 计层（已知用法）
   - 30532001（SubType=701 / 木宗门青藤之力 / B-004）— 6 ADD_BUFF + 7 REMOVE_BUFF（按 buff 增减驱动而非 buff_layer）

   **结论**：buff_layer 操作只表明"按状态计层修正数值"是常用范式，**不是心法判据**。主动技 / 法宝 / 普攻都可用 buff_layer，B-003 N-5 corpus 全扫 4.7% 占比印证（不是少数派）。**心法判定仅用上面 OR 两类条件**。

   与 [SkillEntry系统.md](SkillEntry系统.md) 反直觉 4（"心法也可能纯 Passive，模式 C"）双向引用。

4. **心法与 buff 的双向关系**：
   - SkillConfig.EnhanceSkillBuffConfigID = 心法引用 buff（"我替换的是哪个 buff 关联的普攻"）
   - buff 在表里通过 buff trigger / on-hit 反过来触发心法 SkillID（运行时方向）

5. **Buff 串联是控制类技能的标准实现** — 30431000 身法用 4 个 BuffConfig + 4 ADD_BUFF 实现"减速 + 破甲 + 硬直 + 其他"，不是某种特殊"控制 buff 机制"，就是简单粗暴的 4 个独立 buff（[diffs/30431000.md](diffs/30431000.md) 教训 5）。

---

## ADD_BUFF Params 字段语义初探（B-003 D-304 新增段）

`TSET_ADD_BUFF` 节点 Params 字段语义（**B-003 6 样本归纳，未源码确认**）：

| Param | 推测语义 | 已观察值 | 备注 |
|-------|---------|---------|------|
| `Params[0].Value` | 目标选择 / 属性 | 多种 | 待源码确认 |
| `Params[1].Value` | buff 类型 | **3**（多数）/ **35**（少数） | 推测：3=普通 buff / 35=特殊类（待源码） |
| **`Params[2].Value`** | **buff_config_id（全局 BuffConfig 表 ID）** | 440501 / 2250124 / 2250102 / 2200026 / 10000 / 220xxxx 等 | **关键字段——运行时寻址 buff 真实定义的入口**，对账 `Buff/BuffConfig.xlsx` |
| `Params[3].Value` | duration（时长） | 0 / 数百 / **-1**（永久） | 0 = 默认/即时；-1 = 永久 buff |
| `Params[5].Value` | 来源标识 | 1 / 实体 uid 字面量 | 推测：1=技能来源 / uid=具体实体 |

**用法**：审核 ADD_BUFF 节点时，**先抓 Params[2] 找 buff 真实定义**（不是看 BuffConfigNode），再看 Params[3] 时长 / Params[1] 类型确认行为。**B-003 强烈建议**：对账 Excel `Buff/BuffConfig.xlsx`（README §11 等级 2 - 运行时实际数据，可能覆盖编辑器参数）。

---

## 反直觉点（容易踩的）

1. **心法计层用 `TSET_GET_BUFF_LAYER_COUNT`，不是 `TSET_GET_SKILL_TAG_VALUE`** — 30531005 出现 5 次 GET_BUFF_LAYER_COUNT + 0 次 GET_SKILL_TAG 用于计层。把"计层"全归到 SkillTag 系统是错的（[diffs/30531005.md](diffs/30531005.md) 教训 2）。

2. **"心法"在 flow 层与普攻同构** — 心法不是"挂在普攻上的被动 buff"，而是**用 buff 触发后变成"这个普攻 ID"**。CdType=4（连招）+ Icon=Pugong + EnhanceSkillBuffConfigID 非 0 = 替换型普攻（[diffs/30531005.md](diffs/30531005.md) 教训 1）。

3. **SubType 名字不映射到具体机制——同 SubType 102（奇术）有四种以上不同实现**（v0.3 D-204 修订）：
   - **buff 串联型**（30431000 金奇术）— 4 BuffConfig + 4 ADD_BUFF，**无 ADD_FORCE / 无 SET_COLL**
   - **真位移型**（30215001 土奇术-奔岩突进）— ADD_FORCE 物理位移 + SET_COLL × 2 + ADD_BUFF × 2（位移 + buff 协作）
   - **隐身型**（30222002 木奇术-落木遁形）— APPLY_ENTITY_EFFECT 透明 + SET_COLL × 4 + DESTROY
   - **替身型 / 复合型**（30433001 水身法 SubType=901-潜行水底）— SET_COLL × 4 + APPLY × 2 + CREATE_ROLE 替身 + REMOVE_ENTITY_AI

   **铁律：不能用 SubType 名字（奇术/身法）推机制**——必须查 flow 内 class_counts（看是否有 ADD_FORCE / SET_COLL / APPLY_ENTITY_EFFECT / CREATE_ROLE 等节点）才能知道具体实现是哪一种。Buff 串联只是其中一种（30431000）。

4. **Buff 不只是"有时长的 debuff"** — EnhanceSkillBuffConfigID 反向引用、buff_layer 计层、buff 串联控制效果都是 buff 的合法用途，把 buff 想成"减速 / 中毒"那种简单状态会漏看大量场景。

5. **罕见 active_buff_chain 形态（v0.9 B-008 R1 注脚 / D-805-R1 落地 / 与 type4/7/8 范式一致）**：
   - 主导原语：中等流程（ORDER → DELAY → SELECT_CIRCLE）+ ADD_BUFF + 副作用（GET_ATTR / 数值修正）
   - refs 9-15（< type5 阈值 30）/ has_buff=T 但既非 type3a（buff_with_effect_list=F）又非 type3b（has_reg_event=F）
   - **corpus 实证 1 例**：940068（天命气运-伙伴同心 / refs=9 / 9 节点 / `ORDER → DELAY → SELECT_CIRCLE → ADD_BUFF → GET_ATTR` 完整链 / alias_filename_id=146000835）— **真 UNKNOWN**
   - **跨子系统定位收敛（B-008 R1 cross_delta_consistency 字段 / 响应 auditor 元发现 3）**：
     - SkillEntry 系统视角：active_buff_chain 是 type9-12 同级**候选 type 假说**（[SkillEntry系统.md §仍不确定 §7 v0.9 进展段](SkillEntry系统.md) / D-802-R1 / hypothesis py_rule_pending）
     - **BUFF 系统视角**：仅作 §反直觉点 罕见模式（与 v0.7 D-604-R1 type4 / v0.8 D-703-R1 type7-8 范式一致）— **不升 §6 第三独立轴**
   - rule_3 自警：单/双例不升独立轴是 v0.7 D-604-R1（type4 / 3 例）+ v0.8 D-703-R1（type7-8 / 1-2 例）已建立的范式；B-008 R1 严格遵守
   - 撤回 R0 D-805 主张："BUFF 入口 ≥ 3 独立轴 + 第三类 active_buff_chain 与 type3a/b 并列"被 auditor R0 元发现 1 + 27 反例（has_buff=T+a=F+b=F 异质群体：16 other_with_internal_buff + 11 other_unknown）+ rule_3 v2 反向警告（"未被数据反驳就凭空建立独立轴" 镜像反例）推翻 → R1 撤回（思想史保留 §认知演变 v0.9 段 + [SkillEntry系统.md §思想史迁移 v0.9 段 HM-9-β](SkillEntry系统.md)）
   - 待 B-009 工具链按 ADD_BUFF count / SELECT 节点 / SELF_REG 等子型扫描后再决定是否升 type / 升 §6 第三独立轴 / 留 §反直觉点
   - **联动**：[batch_buffer/B-008_R1_counter_example_scan.py](batch_buffer/B-008_R1_counter_example_scan.py) → [B-008_R1_counter_example_scan.json](batch_buffer/B-008_R1_counter_example_scan.json)（rule_6 实施证据 / 27 反例机械可复现）+ [B-008.yaml R1 D-805-R1](batch_buffer/B-008.yaml) + [B-008_auditor_verdict_r2.md](batch_buffer/B-008_auditor_verdict_r2.md)

## SubType 字典（B-002 D-204 收集，待补完）

`SkillConfig.SkillSubType` 是机制偏向的子类型容器，但**不直接映射到代码层实现**：

| SubType | 名字 | 已观察实现 | 样本 |
|---------|------|-----------|------|
| 0 | 标签效果型 | 无主动施放骨架，靠 SkillEvent 触发 | 30534004 |
| 102 | 奇术 | buff 串联 / 真位移 / 隐身 三种 | 30431000 / 30215001 / 30222002 |
| 901 | 身法-水属性 | 隐身 + 替身 + 位移 复合 | 30433001 |
| 3/4/5 等 | 待 B-003+ 补 | — | — |

**该字典与 [SkillEntry系统.md](SkillEntry系统.md) §SubType 字典 双向引用**——SkillEntry 视角的"入口模式 4 类"与 Buff 视角的"机制不固定"是同一现象的两面。

---

## 与其他子系统的因果关系

- Buff 与 **SkillTag 系统并列**（不是包含）：两套状态系统按用途分工。
- Buff → **SkillEntry 系统**：心法的 EnhanceSkillBuffConfigID 是 SkillConfig 顶层字段，与 Active/Passive 入口并列。
- Buff → **模板系统**：模板内常嵌入 ADD_BUFF / REMOVE_BUFF（30531005 8 次 RUN_TEMPL 串联 buff 计层）。
- Buff → **控制流子系统**：buff_layer 读出后送入 VALUE_COMPARE / CONDITION_EXECUTE，驱动分支。

---

## 仍不确定的地方

1. **Buff 与 SkillTag 的边界规则** — 什么时候用 buff 计层，什么时候用 SkillTag 计数？目前观察是"心法计层用 buff，蓄力计层用 SkillTag"，但是否有更深的规则？
2. **`buff_layer` 与 `buff_stack` 是否同概念？** 命名差异是否暗示不同语义？
3. **Buff 在 flow 中的生命周期** — ADD_BUFF / REMOVE_BUFF 与 buff 自身时长 / 层数衰减如何协作？
4. **EnhanceSkillBuffConfigID 是否还有 Active/Passive 两侧的版本？**（B-001 只观察到 SkillConfig 顶层一个）
5. **buff_layer 在 102 主动技 vs 心法用法差异（B-004 D-405 新增）** — 30221000（SubType=102 主动技 / 长 CD 大招）和 30531005（心法）都用 buff_layer，但用法可能不同：心法常用"按 buff 层数取阶段值"（10 层不同伤害系数），主动技可能用"按 buff 层数取数值"（如蓄势状态值修正）。两者数学结构差异待深入：是否一个走 LookupTable 阶梯函数 / 另一个走线性叠加？需对账 ADD_BUFF.Params 各位含义 + Excel BuffConfig.xlsx 表的 buff 类型字段。

6. **BUFF 类 Mode E 入口子模式判定（v0.7 B-006 R1 提出 / v0.8 B-007 R1 闭环 D-702）** —

   **v0.7 旧表述（已迁移到 §认知演变 v0.8 段 HM-8-1，作思想史保留）**：
   v0.7 D-605-R1 当时主张"BUFF 类 Mode E 入口至少 2 子模式 a 6/9 互斥 vs b 3/9 互斥"。

   **v0.8 闭环（D-702 R1 落地）**：a/b 不互斥，是**两个独立轴**：
   - **轴 a（内驱）**：buff_with_effect_list=True（BuffConfig.SkillEffectListOnStart / OnLoop / OnEnd 任一非空），BUFF 引擎周期 tick 内驱触发（不一定要有 REGISTER_SKILL_EVENT）。
     - **corpus 13 例**（v0.8 阈值放宽 50→300 + 4 例新增 / rule_4 .py 可重现 / [batch_buffer/B-007_corpus_full_recode.json](batch_buffer/B-007_corpus_full_recode.json)）
     - **样本**：1750087（B-006 直读）/ **940107（B-007 直读 / refs=66 阈值放宽证据）** / 660009 / 1860401 / 1750033 / 940086 / 940043 等
   - **轴 b（外驱）**：has_register_skill_event=True 且 BuffConfig 字段全空，外部 SkillEvent 订阅触发回调，回调切换 BUFF / 特效 / 碰撞 / 动画。
     - **corpus 18 例**（v0.8 阈值放宽 50→300 / type3b 与 type3a 独立轴软化后正式编码）
     - **样本**：**1900111 / 1900093 / 1860234（B-007 直读 3 反例 / sample_score 0.688/0.875/1.000）**
   - **两轴可同时为 True**（剧本战斗常见）：
     - corpus a∩b 真重叠 6 例（auditor R0 验证补强）：**940086 / 1750001 / 1750087 / 1860401 / 1900097 / 30522011**
     - multi_class_overlap 跳升 5.4% → 14.7%（rule_5 触发实例 / 已合并到 README §AI 工作守则 rule_3 v2 反向警告示例）
   - **type3b 子型按主导 effector 软分（人类视角，rule_4 暂不写死编码）**：
     - **b1 ADD_BUFF 联动型**（含 ADD_BUFF ≥ 1 + 多 BuffConfig）—— **1900111**（type3b ∩ type6 复合 / 含 GuideConfigNode + ROLE_DIALOGUE）
     - **b2 特效/动画型**（CREATE_EFFECT + PLAY_ROLE_ANIM ≥ 2）—— **1900093**（REG×2 + ADD_BUFF×2 + CREATE_EFFECT×4 + PLAY_ROLE_ANIM×2）
     - **b3 碰撞控制型**（SET_ENTITY_COLLISION ≥ 5）—— **1860234**（SET_COLL×12 + REG×1 + UNREG×1 / sample_score=1.000 ⭐ / 含 REG/UNREG 范式 N 对管理在 type3b 出现）
   - **核心修订**：BUFF 入口 = 两独立轴的并集而非互斥子类。判定 Mode E 入口子模式时不应将 a/b 视为互斥分类。
   - **Buff 系统 confidence 高保持**（D-702 §6 闭环 / 不升级）— 开放问题闭环但 confidence 不动（rule_3 自警：14.7% multi_overlap 揭示设计层非互斥，框架软化是认知精化非升级）。
   - **联动**：[SkillEntry系统.md §仍不确定 §7 v0.8 进展段](SkillEntry系统.md) + [batch_buffer/B-007.yaml D-702 R1](batch_buffer/B-007.yaml) + [B-007_auditor_verdict.md](batch_buffer/B-007_auditor_verdict.md) + [README §AI 工作守则 rule_3 v2 反向警告示例](README.md)

   ---

   **v0.9（B-008 R1 进展段 / D-805-R1 落地 / 不闭环 / 27 反例待 B-009 子型扫描）**：

   v0.8 §6 闭环（type3a/b 两独立轴 + multi_overlap 14.7%）**保持不动**；v0.9 仅在本段加进展记录（不撤回 v0.8 闭环）。

   **B-008 R1 实测（auditor R0 元发现 1 / rule_1 corpus_full_scan 真跑 / [B-008_R1_counter_example_scan.py](batch_buffer/B-008_R1_counter_example_scan.py) 可机械复现）**：

   - has_buff=T + 既非 type3a（buff_with_effect_list=T）又非 type3b（has_reg_event=T）共 corpus **27 例反例**
   - **morph_breakdown 异质群体细分**：
     - 16 other_with_internal_buff：含内嵌 BuffConfig 但非典型 trigger 模式（含 BUFF 数据容器型 + 流程链型 + 业务节点型 等异质子型）
     - 11 other_unknown：未分类异质群体
   - 其中 940068 类 active_buff_chain 是候选 type（中等流程 + ADD_BUFF + 副作用），证据强度 1/27 = 3.7% **严重不足升独立轴**
   - 27 反例并非同一形态 / 不能直接等于"第三独立轴" / 含至少 2 子型（with_internal_buff + unknown）

   **不升级独立轴的原因（rule_3 v2 反向警告 / 与 type4/7/8 范式一致）**：

   - 单/双例不升独立轴是 v0.7 D-604-R1（type4 / 3 例 → §反直觉点 罕见模式）+ v0.8 D-703-R1（type7-8 / 1-2 例 → §反直觉点 罕见模式）已建立的范式
   - 940068 单例升 §6 第三独立轴违此范式（B-008 R0 D-805 错误）
   - rule_3 v2 反向警告："未被数据反驳就凭空建立独立轴 / 多类框架" = 镜像反例（非数据驱动新建独立轴）
   - 软化为 §反直觉点 罕见模式（active_buff_chain 见 §反直觉点 5）

   **B-009 工具链子型扫描任务（D-803 衍生）**：

   待 B-009 工具链按 ADD_BUFF count / SELECT 节点 / SELF_REG 等子型扫描后再决定：
   - 子型 1 升 SkillEntry type9-12 同级 type（需 corpus ≥ 3 例 / type4 阈值）
   - 子型 2 升 BUFF §6 第三独立轴（需 corpus ≥ 多少例 + multi_overlap 多少 % / 待 B-009 数据驱动）
   - 子型 3 留 §反直觉点 罕见模式（与 type4/7/8 范式一致）

   **撤回 R0 D-805 主张**："BUFF 入口 ≥ 3 独立轴 + 第三类 active_buff_chain 与 type3a/b 并列" → 思想史保留 §认知演变 v0.9 段（与 [SkillEntry系统.md §思想史迁移 v0.9 段 HM-9-β](SkillEntry系统.md) 同源）。

   **联动**：[SkillEntry系统.md §仍不确定 §7 v0.9 进展段 active_buff_chain hypothesis](SkillEntry系统.md) + [batch_buffer/B-008.yaml R1 D-805-R1](batch_buffer/B-008.yaml) + [B-008_auditor_verdict_r2.md](batch_buffer/B-008_auditor_verdict_r2.md)（cross_delta_consistency 范式推广建议 / R2 三处独立 cross-check 全过）+ [B-008_R1_counter_example_scan.py](batch_buffer/B-008_R1_counter_example_scan.py)（rule_6 实施证据）

7. **§Z Buff 层数化机制候选（v0.11 B-012 R1 D-1204 新增 / rule_3 v2 单证不升字典 / 候选 pending B-013+ ≥3 多样本加固）** —

   > **关键 hedge**（rule_3 v2 范式 + auditor R0 D-1204 ✓ 直接通过 / 良性应用范例）：本进展是 30524001（火宗门标签效果_灼伤）首次在 30xxxxxxx_8d 段位实证 **层数化 Buff** 系统，**单证不升字典** / 仅 §仍不确定 候选段 / **不建独立《Buff层数化机制》子系统页**（README §维护原则 §1 不为强而写 / 1 实证不足以建页）。

   **30524001 灼伤实证数据**（auditor R0 grep 100% 验证 / [batch_buffer/B-012_read.json](batch_buffer/B-012_read.json) 30524001 signals）：

   | 节点 class | 出现次数 | 范式角色 |
   |-----------|----------|---------|
   | `GET_BUFF_LAYER_COUNT` | 8 | 高频读取层数 |
   | `ADD_BUFF` | 8 | 重复添加增层 |
   | `VALUE_COMPARE` | 8 | 层数判定 |
   | `NUM_CALCULATE` | 6 | 层数到数值的转换公式 |
   | `REPEAT_EXECUTE` | 2 | 周期触发跳 |
   | `REGISTER_SKILL_EVENT` | 1 | 攻击触发增层 |

   **范式**：**攻击触发增层 + 周期掉血 + 层数到伤害公式** = 灼伤标签效果的层数化 Buff 内核。

   **状态**：rule_3 v2 单证候选 pending B-013+ ≥3 多样本数据加固（建议 B-013+ 选样：中毒 / 流血 / 寒冰 等其他层数化标签效果）

   **B-007 D-7xx 候选呼应**：v0.7 B-006 R1 D-605-R1 BUFF 类 Mode E 入口子模式段已存在但无足够实证，本批 30524001 单证 + B-013+ 加固后可考虑联动升级。

   **不升正式不变量** / **不升 §6 第三独立轴**（rule_3 v2 单证不升字典良性应用范例）/ **不建独立子系统页**

   **数据来源**：[batch_buffer/B-012_read.json](batch_buffer/B-012_read.json) 30524001 signals node_classes 全集 + auditor R0 独立 grep 验证 100% 一致 + B-007 D-7xx Buff 层数管理候选段呼应 / [batch_buffer/B-012.yaml D-1204](batch_buffer/B-012.yaml) + [B-012_auditor_verdict_r2.md](batch_buffer/B-012_auditor_verdict_r2.md)（auditor R0 ✓ 直接通过 / R2 重维持质量未变）

---

## 认知演变（错→对的轨迹）

- **v0.2（2026-05-09）首次确立**：B-001 前心智里把 buff 当成"有时长的 debuff/buff"。30531005 让 AI 第一次注意到"心法计层用 buff_layer 不用 SkillTag"，30431000 让 AI 注意到"身法是 buff 串联不是位移"，由此建立 Buff 系统独立子页（[diffs/30531005.md](diffs/30531005.md) / [diffs/30431000.md](diffs/30431000.md)）。
- **v0.2 hold-out 暴露过度泛化**（2026-05-09）：把"30431000 身法 = buff 串联"过度泛化为"所有奇术/身法 = buff 串联"，落木遁形 30222002 实测是 APPLY_ENTITY_EFFECT 隐身 + SET_COLL × 4，与 buff 串联完全不同。confidence 中 → 低。
- **v0.2 → v0.3（2026-05-09）反直觉 3 精准化**：B-002 D-204 通过 4 个 SubType 102/901 样本（30431000 / 30222002 / 30215001 / 30433001）把"奇术 = buff 串联"修订为"SubType 名字不映射机制——同 102 至少 3 种实现 + 901 第 4 种"。新增 SubType 字典段。confidence 低 → 中（多样实现已收敛归类，认知不再过度归纳到单一模式）。出处：B-002 D-204（[B-002.yaml F-4](batch_buffer/B-002.yaml)）。
- **v0.3 旧表述存档**（搬迁自 B-003 D-304 conflict_flag）：v0.3 原不变量 1 写"`BuffConfigNode` 是 buff 实体定义"——这个表述把 flow 内 BuffConfigNode 当成 buff 的权威定义，是错的。真相是 **buff 真实定义在 Excel 表 `Buff/BuffConfig.xlsx`，flow 内 BuffConfigNode 仅是编辑器侧的元数据快照 / 调试占位**（含 BuffNameKey / EffectID / Icon / IsShowIcon 等编辑器字段）。该旧表述被 B-003 4 阶证据（30134001 / 30214004 hold-out / 30531008 / 30324002 / 30325001 / 30535000）反例推翻。
- **v0.3 → v0.4（2026-05-09）不变量 1 重写 + ADD_BUFF Params 字段语义初探 + 不变量 3 心法判定 OR 两类**：B-003 D-304 + D-307 通过 4 阶 + 6 样本证据：(a) 不变量 1 重写为"buff 权威定义在 Excel 表，flow 内 BuffConfigNode 是元数据快照"+ 比例约束（flow 内独立 buff 种类数 ≤ BuffConfigNode 数 / ADD_BUFF 数 ≥ buff 种类数）；(b) 新增 §ADD_BUFF Params 字段语义初探段（关键字段 Params[2]=buff_config_id 等）；(c) 不变量 3 心法判定从单条件"EnhanceSkillBuffConfigID ≠ 0"升级为 OR 两条件——替换型 EnhanceID≠0 OR 标签效果型 CdType=0 + Mode C + 文件名含心法关键字（4 阶证据：30534004 / 30531006 / 30535000 / 30531008 全 EnhanceID=0 但都是合法心法）。**confidence 中 → 高**（不变量 1 修订让 BuffConfigNode 必填误解被修正 + ADD_BUFF.Params 字段语义初步揭示）。出处：B-003 D-304 + D-307（[B-003.yaml D-304/D-307](batch_buffer/B-003.yaml)）。

- **v0.4 旧表述存档（B-003 D-307 思想史迁移自 conflict_flag）**：v0.4 D-307 心法判定 OR 两类条件中，曾有"buff_layer 操作 = 心法核心"的隐含暗示——B-001 D-4 当时是从 30531005 心法用 buff_layer 一例归纳出"心法计层用 buff_layer 不用 SkillTag"，并将 buff_layer 操作与心法身份强关联。**v0.5 B-004 D-405 修正**：B-004 30221000（SubType=102 主动技 / CdType=1 长 CD 大招）和 308072（SubType=303 法宝召唤型）双证 + B-003 N-5 corpus 全扫 4.7% 占比统计 → buff_layer 操作 **跨 SubType 通用**，不限心法。永不 silent delete，思想史保留：v0.4 旧暗示 = "buff_layer 操作是心法核心" / v0.5 新表述 = "buff_layer ≠ 心法标志，主动技 / 法宝也可用 buff_layer 按状态计层修正数值"。心法判定 OR 两类条件本身不变（替换型 + 被动型），仅在不变量 3 加注 buff_layer 通用性提醒。

- **v0.4 → v0.5（2026-05-10）关键不变量 3 加注 buff_layer 跨 SubType 通用**：B-004 D-405 通过 2 阶强证 + 历史样本印证（30221000 SubType=102 长 CD 大招 has_get_buff_layer=true / 308072 SubType=303 法宝 has_get_buff_layer=true / 30531005 心法已知用 buff_layer / 30532001 SubType=701 心法走 ADD/REMOVE 而非 buff_layer / B-003 N-5 corpus 4.7% 占比）：在不变量 3（心法判定 OR 两类）末尾加注："buff_layer 操作跨 SubType 通用，不能反推心法身份"——主动技 / 法宝 / 普攻都可用 buff_layer 按状态计层修正数值；§仍不确定 加 "buff_layer 在 102 主动技 vs 心法用法差异（按层数取数值 vs 按层数取阶段）"。confidence 高 → 高（保持，加注只是边界精化，不动核心判定逻辑）。出处：B-004 D-405（[B-004.yaml](batch_buffer/B-004.yaml)）。

- **v0.5 → v0.7（2026-05-10）BUFF 类 Mode E 入口子模式新增 §仍不确定 §6 + 不变量 1 v0.7 注脚**：B-006 R1 D-605 通过 1 真实样本（1750087）+ auditor R1 corpus type3 9 例反例验证（buff_with_effect_list True 6/9 + False 3/9）：在不变量 1 末尾加 v0.7 注脚（联动 SkillEntry §仍不确定 §7 type3 编码）+ §仍不确定 加 §6 "BUFF 类 Mode E 入口子模式判定"——子模式 a BuffConfig 字段入口 6/9 / 子模式 b REGISTER_SKILL_EVENT 入口 3/9 / B-007 扩样验证。**Buff 系统 confidence 高保持**（67% 不足以升极高 + 3 反例需 B-007 验证子类边界）；旧 R1 主张"corpus 9 例 type3 一致模式"已迁移到 SkillEntry系统.md §思想史迁移 v0.7 段 HM-7-4（永不 silent delete）。出处：B-006 R1 D-605（[B-006.yaml](batch_buffer/B-006.yaml)）+ auditor R2 verdict=pass（[B-006_auditor_verdict_r2.md](batch_buffer/B-006_auditor_verdict_r2.md)）。

- **v0.7 → v0.8（2026-05-10）BUFF type3 a/b 互斥 → 独立轴软化 + §6 闭环（D-702 R1 落地）**：B-007 R0 通过 3 BUFF 反例直读（1900111 / 1900093 / 1860234，sample_score 0.688/0.875/1.000）+ 1 BUFF 内驱型直读（940107 type3a 阈值放宽证据）+ corpus 13+18 例（rule_4 .py 可重现 [B-007_recode_full_scan.py](batch_buffer/B-007_recode_full_scan.py)）+ **a∩b 真重叠 6 例**（auditor R0 验证补强：940086 / 1750001 / 1750087 / 1860401 / 1900097 / 30522011）：
  - **不变量 1 加 v0.8 注脚（D-702 闭环）**：v0.7 "至少 2 子模式 a/b 互斥" 软化为"两独立轴 + 重叠常见"。BUFF 入口 = 两独立轴的并集而非互斥子类。
  - **§仍不确定 §6 闭环**：a/b 不互斥，是两独立轴（buff_with_effect_list 轴 + has_reg_event 轴），可同时为 True（corpus 真重叠 6 例 / multi_overlap 14.7%）。type3b 子型按主导 effector 软分（人类视角，rule_4 暂不写死编码）：b1 ADD_BUFF 联动 / b2 特效动画 / b3 碰撞控制。
  - **阈值修订**：旧 (B-006) 3 ≤ refs ≤ 50 → 新 (B-007) 3 ≤ refs ≤ 300（剧本战斗 refs 200+ 常见）。
  - **multi_class_overlap 跳升 5.4% → 14.7%**：rule_5 触发实例（curator 元守则升级候选）→ auditor 反馈采纳合并选项 B → 已落到 README §AI 工作守则 rule_3 v2 反向警告示例段落（"互斥框架被数据反驳后软化为独立轴 ≠ 概念框架不存在 / 凭空复活"）。
  - **Buff 系统 confidence 高保持**（D-702 §6 闭环 / 不升级 — rule_3 自警：14.7% multi_overlap 揭示设计层非互斥，框架软化是认知精化非升级）。
  - 旧 R1 主张"a 6/9 互斥 vs b 3/9 互斥" 已迁移到本段下方 §认知演变 v0.8 思想史保留段 HM-8-1（永不 silent delete）。
  - 出处：[B-007.yaml R0 → R1 D-702](batch_buffer/B-007.yaml) + [B-007_auditor_verdict.md](batch_buffer/B-007_auditor_verdict.md)（partial verdict / a∩b 6 例 corpus 实测验证补强）+ [B-007_recode_full_scan.py](batch_buffer/B-007_recode_full_scan.py) + [B-007_corpus_full_recode.json](batch_buffer/B-007_corpus_full_recode.json)。

- **v0.8 → v0.9（2026-05-10）B-008 R1 §反直觉点 5 罕见模式 active_buff_chain + §仍不确定 §6 v0.9 进展段（不闭环 / D-805-R1 落地 / 撤回 R0 第三独立轴）**：

  B-008 R0 D-805 主张"BUFF 入口 ≥ 3 独立轴 + 第三类 active_buff_chain（940068）与 type3a/b 并列" → 升 BUFF §6 第三独立轴。auditor R0 元发现 1 + R1 内部审 rule_3 v2 反向推翻——单例升独立轴前未跑反例（rule_1 走形式），auditor R1 实测 has_buff=T + 既非 type3a 又非 type3b 共 corpus **27 例反例**（16 other_with_internal_buff + 11 other_unknown 异质群体），940068 单例证据强度 1/27 = 3.7% 严重不足；与 v0.7 D-604-R1（type4 / 3 例）+ v0.8 D-703-R1（type7-8 / 1-2 例）单/双例不升独立轴范式不一致。

  - **§反直觉点 5 新增（v0.9 注脚）**：罕见 active_buff_chain 形态（940068 类 / 中等流程 + ADD_BUFF + 副作用 / refs 9-15 / 与 type4/7/8 范式一致）。**跨子系统定位收敛**（cross_delta_consistency 字段 / 响应 auditor 元发现 3）：SkillEntry 系统下 type9-12 同级候选 type 假说（D-802-R1）+ BUFF 系统下仅 §反直觉点 罕见模式（D-805-R1）/ **不升 §6 第三独立轴**。
  - **§仍不确定 §6 v0.9 进展段（不闭环）**：B-008 R1 实测 has_buff=T + 既非 type3a 又非 type3b 共 27 例 corpus 反例（16 other_with_internal_buff + 11 other_unknown 异质群体）；其中 940068 类 active_buff_chain 是候选 type，需 B-009 工具链按 ADD_BUFF count / SELECT 节点 / SELF_REG 等子型扫描后再决定升 type / 升 §6 第三独立轴 / 留 §反直觉点。
  - **v0.8 §6 闭环保持不动**：type3a/b 两独立轴 + multi_overlap 14.7% 不修订；v0.9 仅在 §仍不确定 §6 v0.9 进展段加记录（不撤回 v0.8 闭环）。
  - **rule_3 v2 关联**：单/双例不升独立轴是 rule_3 v2 既定原则；本批 R1 严格遵守。
  - **Buff 系统 confidence 高保持**（不升级 / 加 §反直觉点 罕见模式 + §仍不确定 §6 v0.9 进展段）。
  - 旧 R0 主张"BUFF 入口 ≥ 3 独立轴 + 第三类 active_buff_chain"已迁移到本段下方 §思想史迁移 v0.9 段 HM-9-β（永不 silent delete）+ HM-9-2 撤回链记录（依赖 D-805 ✗，思想史迁移本身不成立）。
  - 出处：[batch_buffer/B-008.yaml R1 D-805-R1](batch_buffer/B-008.yaml) + [B-008_auditor_verdict.md](batch_buffer/B-008_auditor_verdict.md)（R0 否决 / 元发现 1）+ [B-008_auditor_verdict_r2.md](batch_buffer/B-008_auditor_verdict_r2.md)（R2 通过 / 改进幅度 0.85 / cross_delta_consistency 范式推广建议）+ [B-008_R1_counter_example_scan.py](batch_buffer/B-008_R1_counter_example_scan.py) + [B-008_R1_counter_example_scan.json](batch_buffer/B-008_R1_counter_example_scan.json)（rule_6 实施证据 / 27 反例机械可复现）。

### 思想史迁移 v0.9（B-008 R1 D-805 R0 第三独立轴撤回 + HM-9-2-R1 撤回链记录）

> **保留旧表述 + 切换日期 + 推翻原因 + 新认知指针**——"删 mental_model 旧条目时强制保留思想史"（README §AI 工作守则 §6）。永不 silent delete。
>
> **本段 2 项思想史迁移**：HM-9-β（R0 D-805 第三独立轴撤回，与 [SkillEntry系统.md §思想史迁移 v0.9 段 HM-9-β](SkillEntry系统.md) 同源 / 跨页登记）+ HM-9-2-R1 撤回链记录（依赖 D-805 ✗，原计划迁移作废）。

**迁移日期**：2026-05-10（v0.8 → v0.9 切换 / B-008 R0 → R1 → R2 修订）

#### HM-9-β：B-008 R0 D-805 "BUFF 入口 ≥ 3 独立轴 + 第三类 active_buff_chain" 主张（跨页同源 / 简版）

**旧表述（B-008 R0 D-805）**：

> "BUFF 类 Mode E 真技能 type3 入口至少 3 独立轴 — 子模式 a (BuffConfig 字段，13 例) / 子模式 b (REGISTER_SKILL_EVENT，18 例) / **第三类 active_buff_chain (940068 类，中等流程 + ADD_BUFF + 副作用)与 type3a/b 并列**" → 升 BUFF §6 第三独立轴 / 加 v0.9 注脚。

**旧出处**：B-008 R0 yaml `delta_id: D-805`（仅 PROPOSE 阶段，未落盘 Buff系统.md）

**推翻原因（auditor R0 元发现 1 + 元发现 3 + rule_3 v2 反向）**：
- 940068 单例（refs=9 / 1 已学样本）升独立轴前未跑反例（rule_1 corpus_full_scan 走形式）
- auditor R1 跑 [B-008_R1_counter_example_scan.py](batch_buffer/B-008_R1_counter_example_scan.py) 实测 has_buff=T + 既非 type3a 又非 type3b 共 corpus **27 例反例**（含 16 other_with_internal_buff + 11 other_unknown 异质群体），940068 单例升注脚证据强度 1/27 = 3.7% 严重不足
- 与 v0.7 D-604-R1（type4 / 3 例 → §反直觉点 罕见模式）+ v0.8 D-703-R1（type7-8 / 1-2 例 → §反直觉点 罕见模式）范式不一致 — 单/双例不升独立轴是 rule_3 v2 既定原则
- R0 D-802 / D-805 内部对 active_buff_chain 定位冲突（auditor R0 元发现 3）：D-802 视角"SkillEntry type9 反例兄弟 type" vs D-805 视角"BUFF 第三独立轴" — R1 跨子系统收敛到统一定位（cross_delta_consistency 字段）

**新认知指针**：本页 §反直觉点 5 罕见模式 active_buff_chain（与 type4/7/8 范式一致 / 不升独立轴）+ §仍不确定 §6 v0.9 进展段（27 反例待 B-009 子型扫描）+ [SkillEntry系统.md §仍不确定 §7 v0.9 进展段 active_buff_chain hypothesis](SkillEntry系统.md)（SkillEntry 视角候选 type 假说 / cross_delta_consistency 跨子系统统一定位）

**v0.8 §6 闭环保持不动**：type3a/b 两独立轴 + multi_overlap 14.7%；v0.9 不撤回 v0.8 闭环，仅在 §仍不确定 §6 加 v0.9 进展段记录（不构成思想史迁移级别的修订）。

**证据样本**：940068（已学 1 例 + alias_filename_id=146000835）+ corpus 27 反例（auditor R1 实测，含 940068 + 1860213 等）
**证据来源**：[batch_buffer/B-008.yaml R1 D-805-R1 r1_revision_actions](batch_buffer/B-008.yaml) + [B-008_auditor_verdict.md](batch_buffer/B-008_auditor_verdict.md) + [B-008_auditor_verdict_r2.md](batch_buffer/B-008_auditor_verdict_r2.md) + [B-008_R1_counter_example_scan.py](batch_buffer/B-008_R1_counter_example_scan.py)（rule_6 实施证据 / R2 三处独立 cross-check 全过）

#### HM-9-2-R1：撤回不迁移记录

**原计划迁移**：B-008 R0 HM-9-2 主张"BUFF 入口 ≥ 3 独立轴" 思想史迁移登记到 Buff系统.md

**撤回原因**：HM-9-2 依赖 D-805 R0 第三独立轴主张 ✗ 否决 → 思想史迁移本身不成立。Buff 系统 §6 v0.8 闭环（type3a/b 两独立轴 / multi_overlap 14.7%）保持不动；仅在 §反直觉点 段加 v0.9 注脚"罕见 active_buff_chain 形态（940068 类）"+ §仍不确定 §6 v0.9 进展段记录 corpus 27 反例待 B-009 子型扫描（见 D-805-R1）。

**为何记录在此**：撤回链本身是 harness steering loop 的诚实记录 — D-805 ✗ 触发 HM-9-2 撤回（无新主张推翻 v0.8 §6 闭环）→ 不构成思想史迁移级别的修订。永不 silent delete 撤回链。

**证据来源**：[batch_buffer/B-008.yaml R1 historical_migrations.HM-9-2-R1](batch_buffer/B-008.yaml) + [B-008_auditor_verdict_r2.md](batch_buffer/B-008_auditor_verdict_r2.md)（HM-9-2-R1 ✓ 撤回不迁移决策正确）

### 思想史迁移 v0.8（B-007 R1 D-702 BUFF type3 a/b 互斥 → 独立轴软化）

> **保留旧表述 + 切换日期 + 推翻原因 + 新认知指针**——"删 mental_model 旧条目时强制保留思想史"（README §AI 工作守则 §6）。永不 silent delete。

**迁移日期**：2026-05-10（v0.7 → v0.8 切换 / B-007 R0 → R1 D-702）

#### HM-8-1：v0.7 D-605-R1 "BUFF type3 子模式 a 6/9 互斥 vs 子模式 b 3/9 互斥" 主张

**旧表述**：v0.7 D-605-R1 §仍不确定 §6 主张"BUFF 类 Mode E 真技能 type3 入口至少 2 子模式 — 子模式 a (BuffConfig 字段, 6/9) 互斥 vs 子模式 b (REGISTER_SKILL_EVENT, 3/9)"。

**旧出处**：Buff系统.md §仍不确定 §6 v0.7 表述 + §认知演变 v0.5 → v0.7 段（B-006 R1 D-605-R1）

**推翻原因**：
- B-007 R0 corpus_full_scan 修订后实测：a/b 不互斥，是两独立轴（buff_with_effect_list 轴 + has_reg_event 轴），可同时为 True
- corpus a∩b 真重叠 6 例（auditor R0 实证验证）：940086 / 1750001 / 1750087 / 1860401 / 1900097 / 30522011
- multi_class_overlap 14.7% > 5% 阈值（rule_5 触发实例 / 已合并到 README §AI 工作守则 rule_3 v2 反向警告示例）
- B-007 1900111 既含 BUFF 又含 ADD_BUFF + REG_EVENT，type6 + type3b 多重叠（剧本战斗常见模式）
- 13（type3a）+ 18（type3b）= 31 corpus 例 - 6 重叠 = 25 独立 + 6 重叠 = 7.5%（占 type3 31 例）独立分布（不是互斥分类）

**新认知指针**：§关键不变量 1 v0.8 注脚（两独立轴）+ §仍不确定 §6 v0.8 闭环（a∩b 真重叠 6 例 + b1/b2/b3 子型软分）+ README §AI 工作守则 rule_3 v2 反向警告示例

**证据样本**：1900111 / 1900093 / 1860234（type3b 反例）+ 940107 / 1750087（type3a 直读）+ a∩b 重叠 6 例（940086 / 1750001 / 1750087 / 1860401 / 1900097 / 30522011）
**证据来源**：[batch_buffer/B-007.yaml R1 D-702](batch_buffer/B-007.yaml) + [B-007_recode_full_scan.py](batch_buffer/B-007_recode_full_scan.py) + [B-007_corpus_full_recode.json](batch_buffer/B-007_corpus_full_recode.json) + [B-007_auditor_verdict.md](batch_buffer/B-007_auditor_verdict.md)（auditor 跑 cls_counter 验证 a∩b=6 例）

---

## 引用样本与源码

**真实样本**：
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30531005_*.json` — 5 GET_BUFF_LAYER_COUNT + 3 REMOVE_BUFF + 2 BuffConfig + EnhanceSkillBuffConfigID=2250099
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30431000_*.json` — SubType=102 / 4 ADD_BUFF + 4 BuffConfigNode（buff 串联型）
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30234006_*.json` — ADD_BUFF（数量未拉取）
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30222002_*.json` — SubType=102 / APPLY_ENTITY_EFFECT 透明 + SET_COLL × 4（隐身型，hold-out 反例）
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30215001_*.json` — SubType=102 / ADD_FORCE + SET_COLL × 2 + ADD_BUFF × 2（真位移型）
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30433001_*.json` — SubType=901 / SET_COLL × 4 + APPLY × 2 + CREATE_ROLE 替身（替身复合型）
- **`{{SKILLGRAPH_JSONS_ROOT}}通用BUFF/SkillGraph_1750087_*.json` — 招魂台胜利 Buff / SubType=0 / Mode E type3 BUFF 内部 trigger 子模式 a（BuffConfig 字段入口）/ refs=15 / B-006 R1 sample_score=0.812**（v0.7 新增，BUFF 类 Mode E 入口子模式 a 的代表样本）
- **B-007 R1 BUFF 类直读样本（v0.8 新增 / 4 样本支持 D-702 独立轴软化）**：
  - `{{SKILLGRAPH_JSONS_ROOT}}通用BUFF/SkillGraph_940107_*.json` — 全死气死气版本 / SubType=1001 / Mode E type3a (轴 a 内驱 / buff_with_effect_list=True) / refs=66（v0.8 阈值放宽 50→300 false negative 修复证据）/ sample_score=0.750
  - `{{SKILLGRAPH_JSONS_ROOT}}通用BUFF/SkillGraph_1900111_*.json` — 剧情BUFF触发 / SubType=0 / Mode E type3b 子型 b1 ADD_BUFF 联动型（type3b ∩ type6 复合 / multi_overlap 反例）/ refs=48 / ADD_BUFF×3 + BuffConfig×3（无 effect_list）/ sample_score=0.688
  - `{{SKILLGRAPH_JSONS_ROOT}}通用BUFF/SkillGraph_1900093_*.json` — 剧情BUFF特效 / SubType=0 / Mode E type3b 子型 b2 effect_anim / refs=45 / REG×2 + ADD_BUFF×2 + CREATE_EFFECT×4 + PLAY_ROLE_ANIM×2 / sample_score=0.875
  - `{{SKILLGRAPH_JSONS_ROOT}}通用BUFF/SkillGraph_1860234_*.json` — 剧情BUFF碰撞控制 / SubType=0 / Mode E type3b 子型 b3 collision / refs=25 / SET_COLL×12 + REG×1 + UNREG×1 + ADD_BUFF×1 / sample_score=**1.000** ⭐（含 REG/UNREG 范式 N 对管理）

- **B-008 R1 BUFF 类直读样本（v0.9 新增 / active_buff_chain 罕见模式 / D-805-R1 跨子系统定位收敛 / 与 type4/7/8 范式一致 / 不升 §6 第三独立轴）**：
  - `{{SKILLGRAPH_JSONS_ROOT}}天命气运/SkillGraph_940068_*.json` — 天命气运-伙伴同心（流程加 buff 型）/ SubType=0 / Mode E / 9 节点 ORDER→DELAY→SELECT_CIRCLE→ADD_BUFF→GET_ATTR 完整链 / refs=9 < type5 阈值 30 / has_buff=T 但既非 type3a 又非 type3b（has_buff_with_effect_list=F + has_reg_event=F）/ **alias_filename_id=146000835**（文件名数字 ID ≠ SkillID）/ R1 不再升 BUFF 第三独立轴归 §反直觉点 5 罕见模式 / sample_score=0.53

**源码**（待读）：
- `Assets/Scripts/HotFix/Game/Battle/` — Buff 运行时实现
- `Assets/Scripts/CSGameShare/Hotfix/` — BuffConfig 数据结构

**Excel 表**（待对账）：
- `{{SKILL_EXCEL_DIR}}/` — Buff 配置（具体表名待确认）

**关联文档**：
- [SkillTag 系统.md](SkillTag系统.md) — 与本系统并列的状态系统
- [SkillEntry 系统.md](SkillEntry系统.md) — EnhanceSkillBuffConfigID 是 SkillConfig 顶层字段；SubType 字典双向引用
- [实体碰撞与可见性.md](实体碰撞与可见性.md) — 隐身/位移/替身型 SubType 102/901 实现的伴生子系统
- [节点字典.md](../docs/节点字典.md) — TSET_GET_BUFF_LAYER_COUNT / TSET_ADD_BUFF / TSET_REMOVE_BUFF 字段
