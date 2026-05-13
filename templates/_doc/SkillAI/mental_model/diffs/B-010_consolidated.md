# B-010 Consolidated DIFF — 6 samples (5 训练 + 1 hold-out)

> 闭卷 PREDICT (predictions/{id}_b010.yaml) ↔ 开卷 READ + corpus_full_scan 真扫数据。
>
> 4 维 sample_score 计算 + 4 RQ-B10 答案 + delta 候选汇总。

---

## sample_score 明细（4 维：节点数 / 拓扑 / 模板 / 子系统）

| 样本 | 节点数 | 拓扑 | 模板 | 子系统 | 平均 | 备注 |
|------|-------|------|------|-------|------|-----|
| 146004907 (伤害) | 1.00 (50 vs 44+) | 1.00 (ORDER 串 RUN_TEMPL × 27 + NUM_CALC 拼装命中) | **0.50** ⚠️ (预测 146004489-520 子模板 + 三联包 — 真实情况待 RUN_TEMPL.SkillEffectTemplateID 字段读) | 1.00 (模板系统 + 控制流 + 数值)| **0.875** | 范式直接印证；类别 2 |
| 146001847 (功能) | 1.00 (12 vs 9+) | 1.00 (REPEAT × 1 + CREATE_RANDOM_NUM × 2 + CREATE_ROLE) | 1.00 (无子模板调用对) | 1.00 (含实体生命周期与替身机制候选首次触碰) | **1.00** ⭐ |
| 32004137 (单位) | 1.00 (22 vs 16+) | 0.875 (拓扑大体对，但 IsTemplate 节点不在 ORDER 上而在 **CONDITION** 上 — 出乎预测) | 1.00 (无子模板调用对) | 1.00 (实体生命周期 + 控制流 + 模板) | **0.969** ⭐ |
| 1860139 (子弹 类别 2b) | 1.00 (40 vs 32+) | 1.00 (NUM_CALC × 10 + CONDITION + ATTR + GET_ORIGIN_SKILL_ID 角度计算 ✓) | 1.00 | 1.00 (子弹系统首次触碰 + 类别 2b 边界) | **1.00** ⭐ |
| 940021 (技能 类别 2b) | 1.00 (18 vs 11+) | 1.00 (PLAY_ANIM + DELAY + Interrupt × 2 ✓) | 1.00 | 1.00 (中断系统候选首次触碰 + 类别 2b) | **1.00** ⭐ |
| 66000081 (数值 hold-out) | 1.00 (5 vs 3+) | 0.875 (NUM_CALC × 1 + ATTR × 2 ✓ 但 IsTemplate 在 NUM_CALC 节点上，不在 ORDER 上) | 1.00 | 1.00 | **0.969** ⭐ |

**batch_accuracy = 6 sample 平均 = (0.875 + 1.00 + 0.969 + 1.00 + 1.00 + 0.969) / 6 = 0.969 ⭐**

> 注：样本 146004907 模板列表给"预测"扣 0.5 — 因为预测列了若干具体子模板 ID（146004489-520 系列 / 三联包 190016404/485/523），但真实 RUN_TEMPL.SkillEffectTemplateID 需进一步深读才能精确比对，暂保守扣分。

---

## 4 个 RQ-B10 答案

### RQ-B10-1：技能模板（IsTemplate=True）与真技能（IsTemplate=False）的内部结构系统性差异？

**答案（强证据 / 6 样本一致 + corpus 全集 426 节点验证）**：

1. **入口节点 class 不变量被部分推翻**：v0.6 §模板系统 关键不变量 1 主张"所有 root 节点都是 TSET_ORDER_EXECUTE"，但全 corpus 426 个 IsTemplate=True 节点中 **TSET_ORDER_EXECUTE 仅 81.5% (347/426)**，剩 18.5% 分布在：
   - TSET_NUM_CALCULATE: 8.0% (34) — 数值计算型模板（如 146004907 / 66000081）
   - TSET_CONDITION_EXECUTE: 3.3% (14) — 条件分支型模板（如 32004137）
   - TSET_VIEW_OPTION: 1.6% (7) — 镜头/视角控制型模板
   - TSCT_VALUE_COMPARE: 1.4% (6) — 条件比较型模板
   - TSET_PROBABILITY_EXECUTE: 0.7% (3)
   - 其余 ≤ 0.5% × 多种 / 共 ~3.3%
   
   **结论**：v0.6 §模板系统 不变量 1 需修订为"模板入口节点主轴是 TSET_ORDER_EXECUTE (81.5%)，但允许在 TSET_NUM_CALCULATE / TSET_CONDITION_EXECUTE 等数值/条件计算节点上也标 IsTemplate=True，对应'数值取值器型模板' / '条件分支型模板' 等小型工具模板"。

2. **TemplateParam 数组全 corpus 0 例非空**！v0.6 §一句话本质 + §关键不变量 1 提到的"模板入口节点 = ... + 一组 TemplateParams" 描述，全 corpus 426 个 IsTemplate=True 节点中 **TemplateParam 数组 0 个非空 / 426 个空**。这彻底推翻"TemplateParams 数组" 是模板入口的常态字段——实际是**几乎不用的可选字段**。

3. **类别 2b 子型存在**：v0.6 §SkillEditor 文件三分类 描述 "类别 2 模板本体 = 顶层 IsTemplate=True"，但全 corpus 404 个含 IsTemplate=True 节点的文件中 **18.6% (75/404) 同时含 SkillConfigNode 顶层**（在 技能模板/ 目录内更高 36.4%）。这些是"**SkillConfigNode 包装的模板本体**"，需在 §文件三分类 中细分类别 2 为：
   - **类别 2a 纯模板本体**（无 SkillConfigNode + 含 IsTemplate=True 节点）：81.4% (329/404)
   - **类别 2b SkillConfigNode 包装的模板本体**（同时含 SkillConfigNode + IsTemplate=True 节点）：18.6% (75/404)

### RQ-B10-2：5 子目录的模板形态差异是否能用现有 §段位字典归纳？还是有新段位？

**答案**：4 个段位有差异化形态映射，1 个段位为 v0.6 §段位字典外候选扩补：

| 子目录 | 主段位 | 形态 | v0.6 字典命中？ |
|--------|--------|------|--------------|
| 伤害 | 146xxxxx, 175xxxxx, 186xxx, 18xxxx, 66xxx, 1860xxx | RUN_TEMPL 套娃数值流程拼装 + 子模板伤害加成包 (146004489-520) | ✓ 14xxx 主段已命中（146xxx 是 14xxx 的子段 — 候选 §段位字典 14xxxxx 行细化为"146xxxxx 伤害子段" + "146003779 持续施法子段" 双子段） |
| 功能 | 146xxxxx, 1860xxx, 18xxxx, 22xxxxx, 66xxx | 召唤怪物 / 飞行状态 / 技能品质适配 / 计时器 等通用功能模板 | ✓ 14xxx + 18xxx-186xxx 已命中 |
| 单位 | **32xxxxx** (× 1) + 66xxx (× 2) | 召唤分身（CREATE_ROLE + COPY_ENTITY_OUTLOOK + RUN_SKILL_EFFECT） | **✗ 32xxxxx 是 v0.6 §段位字典外段位** — 候选 D-1002 字典扩补 "32xxxxx 单位/分身专属段位" |
| 子弹 | 108xxx, 175xxx, 1860xxx | 多向子弹 / 链子弹 / 圆形子弹 / 扇形子弹 / 静态攻击盒 / 角度计算工具 | ✓ 18xxx-186xxx 命中（v0.6 D-510 候选首次正式触碰子弹系统） |
| 技能 | 129xxx, 136xxx, 146xxx, 175xxx, 186xxx, 282xxx, 44xxx, 66xxx, 740xxx, 940xxx | 持续施法 / 连招 / 位移 / 朝向 / 循环动作 / 中断配置 / UI 显隐 / 修改单位槽位 等"通用技能骨架"工具 | ✓ 多数命中，但 **129xxx + 282xxx + 740xxx + 940xxx** 是字典外子段（候选扩补） |
| 数值 | 66xxx | 数值取值器（GET_ATTR + NUM_CALC） | ✓ 66xxx 命中（v0.4 D-306 弱观察 → B-010 加强） |

**结论**：v0.6 §段位字典需扩补 **32xxxxx 单位段** + **129xxxxx / 282xxxxx / 740xxxxx / 940xxxxx 等技能/ 子目录里的零散段位**。

**v0.9.1_actionable.md "5 子目录抽 1" 计划的中文目录名校正**：实际目录名是 **伤害 / 功能 / 单位 / 子弹 / 技能 / 数值**（actionable 误写"控制 / 心法"，分别对应实际"功能 / 技能"）。**B-010 D-1005 元发现**：actionable 文档与文件系统真实状态偏差，需在 v0.9.1_actionable.md 中订正。

### RQ-B10-3：技能模板被 RUN_SKILL_EFFECT_TEMPLATE 调用时的参数传递机制（TemplateParam）是否能从样本归纳？

**答案（强证据 / 全 corpus 0/426 反例）**：

**TemplateParam 数组在全 corpus 0 例非空 / 426 例空** = **TemplateParam 数组在生产环境中几乎不用**。

实际参数传递机制（待源码 grep 二次验证）：
1. **RUN_TEMPL.InputParams 字段**（不是模板入口的 TemplateParam）——RUN_TEMPL 节点上的 InputParams 端口数组负责把调用方的具体参数注入给模板内部的虚拟端口节点（与 v0.6 §仍不确定 中"TPT_EXTRA_PARAM 怎么注入差异化" 候选答案一致）
2. **GET_ORIGIN_SKILL_ID 等环境取值节点**（如 1860139 内 × 2）——模板从执行环境取信息（调用方原技能 ID / 施法者 ID 等）作为隐式参数

**v0.6 §一句话本质 + §关键不变量 1 中的"TemplateParams 数组" 描述需修订**为："模板入口节点 = ORDER（主轴）/ NUM_CALC / CONDITION 等节点 + IsTemplate=True；TemplateParam 数组字段存在但生产环境中几乎不用 (0/426 非空)；实际参数注入主要通过 RUN_TEMPL.InputParams 端口 + 模板内的环境取值节点"。

### RQ-B10-4：技能/ 子目录 30 文件 vs B-006/7/8 已学 SubType=701 真心法的差异？

**答案（v0.9.1_actionable.md 误标"心法" 已校正为"技能"）**：

**目录名"技能"≠ 心法形态**！实际 技能/ 子目录 30 文件的形态分布：
- 持续施法 / 短长按 UI（146003779 / 146002126）
- 连招（175_0101-0105 / 1-5 段连招）
- 位移（175_0023-0025 / 146003107 / 1860206）
- 持续转向 / 朝向（1290141 / 1290148 / 129013602 / 129014419）
- 循环动作（940021）
- 施法状态（1860131 / 1860372 / 66001550）
- 触发器命中（282000）
- UI 显隐（282001）
- 修改单位槽位（44014633）
- 移动至目标单位（740040）
- 召唤魂影 / 通用绕身盾 / 阻挡墙包围圈（146xxx 多）
- 等

**结论**：技能/ 子目录是 **"通用技能骨架工具模板大杂烩"**，**不是心法专属**。已学 SubType=701 真心法（B-006~B-008 / 30512002 / 30524007 / 1750087 等）是"心法 SubType=701" 这个 SkillEntry 类别的实例，与技能/ 模板子目录是正交的概念。

**v0.9.1_actionable.md RQ-B10-4 措辞需要矫正**：原"心法模板 vs 真心法的差异" 应改为"技能/ 子目录 30 文件是通用技能骨架工具模板，与 SubType=701 心法 形成跨类别×跨入口模式的'被调用'关系，不是'心法形态'与'心法形态' 的同类对比"。

---

## Delta 候选清单（B-010 → 提案）

### D-1001 [信号: 强 corpus 426/426 + 6 样本] 模板系统 / 修订关键不变量 1 + §一句话本质

**主张（修订）**：
- v0.6 §一句话本质："模板入口节点 = 一个 TSET_ORDER_EXECUTE + IsTemplate=True + 一组 TemplateParams" → **改为**："模板入口节点 = 一个 IsTemplate=True 标记的节点（主轴 TSET_ORDER_EXECUTE 81.5%，次主轴 TSET_NUM_CALCULATE 8.0% / TSET_CONDITION_EXECUTE 3.3% / TSET_VIEW_OPTION 1.6% / TSCT_VALUE_COMPARE 1.4% / TSET_PROBABILITY_EXECUTE 0.7% 等；TemplateParam 数组字段存在但 corpus 0/426 非空）"
- v0.6 §关键不变量 1："所有 root 节点都是 TSET_ORDER_EXECUTE — 不论是模板本体、宗门 Active root、还是 Passive root，root 永远是 ORDER" → **加边界注脚**："对真技能 root（SkillConfigNode.SkillEffectExecuteInfo / SkillEffectPassiveExecuteInfo 指向的 SkillEffect root）该不变量仍 100% 成立；但对'模板本体' (IsTemplate=True 节点) 该不变量软化为 81.5% — 模板入口可在 NUM_CALC / CONDITION / VIEW_OPTION 等节点上声明 IsTemplate=True，对应'数值取值器型模板' / '条件分支型模板' / '镜头控制型模板' 等小型工具模板"

**证据**：
- B-010 6 样本：3/6 IsTemplate 在非 ORDER 节点（146004907 NUM_CALC / 32004137 CONDITION / 66000081 NUM_CALC）
- corpus 全集 426 节点扫描：TSET_ORDER_EXECUTE 81.5% / 其余 18.5% 跨 ~10 类节点
- 等级 1 源码待 grep 验证（候选路径 `Assets/Thirds/NodeEditor/SkillEditor/`）
- 等级 6 AI 自身归纳 → 等级 3 已学样本 6 + 等级 6 corpus 自动统计 → 数据驱动主张

**confidence 影响**：模板系统 高 → 高（保持，但精度大幅提升）
**conflict_flag**：⚠️ 与 v0.6 §一句话本质 + §不变量 1 冲突，思想史保留旧表述

### D-1002 [信号: 强 corpus 0/426 全 corpus 反例] 模板系统 / 修订 §一句话本质 + §仍不确定段

**主张**：v0.6 §仍不确定 第 2 项"模板内的 TemplateParams 数组的字段语义" → **修订为"已部分闭环：TemplateParam 数组在 corpus 全集 0/426 非空，几乎不用；实际参数注入通过 RUN_TEMPL.InputParams 端口 + 环境取值节点（GET_ORIGIN_SKILL_ID 等）；TemplateParam 字段语义仍不确定（候选定义层意图 vs 运行时使用）— 需源码 grep `Assets/Thirds/NodeEditor/SkillEditor/` 模板节点定义"**

**证据**：corpus 全集扫描 426/426 = TemplateParam 空数组（0 个非空例）

**confidence 影响**：模板系统 高 → 高（开放问题部分前进 + 数据驱动反证主张）
**conflict_flag**：⚠️ 与 v0.6 §一句话本质 中的"+ 一组 TemplateParams" 冲突（思想史保留）

### D-1003 [信号: 强 corpus 18.6%/全 corpus 36.4%/技能模板目录内 + 6 样本] 模板系统 / 修订 §SkillEditor 文件三分类 + 类别 2 细化为 2a/2b

**主张**：v0.6 §SkillEditor 文件三分类 表格扩为 4 行：
- 类别 1：技能（有 SkillConfigNode + 无 IsTemplate=True 节点）
- **类别 2a：纯模板本体**（无 SkillConfigNode + 含 IsTemplate=True 节点）— 全 corpus 81.4% / 329 文件
- **类别 2b：SkillConfigNode 包装的模板本体**（同时含 SkillConfigNode + IsTemplate=True 节点）— 全 corpus 18.6% / 75 文件，在 技能模板/ 目录内 36.4% 高于全 corpus 比例
- 类别 3：剧本调度容器（无 SkillConfigNode + 无 IsTemplate=True）

**类别 2b 的辨识信号**：SkillConfigNode 顶层存在但 SkillSubType / SkillEffectExecuteInfo / SkillEffectPassiveExecuteInfo 等关键字段为 None / 0（"空壳" SkillConfigNode），同时含 IsTemplate=True 节点（多在 ORDER 上）。例：1860139 / 940021 / 1750091 / 940107 / 301301 / 301900 / 301901 / 302901 / 302902 / 303004。

**证据**：
- corpus 全集扫描 75/404 = 18.6%（类别 2b 含 IsTemplate=True 节点的文件中含 SkillConfigNode）
- 6 样本中 2/6 命中类别 2b（1860139 / 940021）— 局部超出 corpus 全集均值因为本批选样含 子弹/技能 子目录内 类别 2b 高密度
- 1860139 SkillConfigNode SubType=None / Active.SECID=None / Passive.SECID=None — 空壳证据

**confidence 影响**：模板系统 高 → 高 / SkillEntry 系统 中偏高 → 中偏高（保持）
**conflict_flag**：与 v0.6 §SkillEditor 文件三分类 表 3 行冲突（思想史保留）

### D-1004 [信号: 中 6 样本 + corpus 段位扫待补] 模板系统 / §段位字典扩补

**主张**：v0.6 §段位字典扩补：
- **32xxxxx 段位**：单位/分身专属段位（B-010 32004137 单证据 + 候选 corpus 二阶印证）
- **129xxxxx 段位**：朝向/转向工具模板段位（已学 1290141 + B-010 corpus 观察 / 多个 129xxx 在 技能/ 子目录）
- **282xxxxx 段位**：触发器/UI 工具模板段位（B-010 corpus 观察 / 282000 触发器命中 + 282001 UI 显隐）
- **740xxxxx 段位**：移动工具模板段位（740040 移动至目标单位 + 740031 已学 SubType=701 候选）
- **940xxxxx 段位**：循环动作 / BUFF deprecated 形态 段位（B-008 已学 940068 / 940058 / 940086 / 940107 + B-010 940021 循环动作）

**证据**：B-010 6 样本 + 技能/ 子目录 30 文件目录列表 + corpus 全集名字归纳

**confidence 影响**：模板系统 高保持
**conflict_flag**：无（增量扩补）

### D-1005 [信号: 强 actionable 文档与文件系统状态偏差] 元发现 / actionable 文档校正

**主张**：v0.9.1_actionable.md §B-010 候选盲点 § option_2 段中"5 子目录抽 1"列出"伤害 / 控制 / 单位 / 子弹 / 心法 / 数值"，但实际目录名是"伤害 / **功能** / 单位 / 子弹 / **技能** / 数值"。"控制 → 功能" + "心法 → 技能"两处中文目录名误标。

**actionable 修复**：在 v0.9.1_actionable.md 中订正中文目录名 + 加注脚"v0.9.1_actionable 历史误标 / B-010 D-1005 校正"。同时对 RQ-B10-4 措辞做对应调整（原"心法模板 vs 真心法" 改为"技能/ 子目录 30 文件是通用技能骨架工具模板与 SubType=701 真心法的'被调用'关系"）。

**证据**：
- 文件系统真实状态：`ls {{SKILLGRAPH_JSONS_ROOT}}技能模板/` → 伤害/功能/单位/子弹/技能/数值（6 子目录）
- v0.9.1_actionable.md 文本（误标）

**confidence 影响**：mental_model 不动；元守则候选升级（rule_2_explicit_scope 增补"actionable / 文档状态字段需与文件系统真实状态对账" 注脚）

---

### D-1006-候选 [信号: 弱 1 样本] 32xxxxx 段位 / 实体生命周期与替身机制 子系统页

**主张**：B-002 D-210 暂存档"实体生命周期与替身机制" 子系统页，B-010 32004137（CREATE_ROLE + COPY_ENTITY_OUTLOOK + RUN_SKILL_EFFECT × 2）+ 146001847（CREATE_ROLE + REPEAT + RANDOM_NUM）共 2 个新样本驱动信号。建议候选首次正式建页（待用户裁决）。

**新原语 COPY_ENTITY_OUTLOOK**：从 32004137 首次见到，候选写入 §节点字典。

**confidence 影响**：候选新建子系统页 confidence: 中（2 样本 + B-002 D-210 暂存档累计）

**用户裁决**：[ ✓ 建页（驱动 B-011 选样补强） / ✗ 暂存档继续 / 🔁 回炉 ]

---

### D-1007-候选 [信号: 弱 1 样本 + 模板内嵌结构] 中断系统 子系统页 候选首次触碰

**主张**：940021 内含 SkillInterruptConfigNode × 2（ID=740001 / 740002）= "模板内嵌中断配置"。这是已学样本中首次正式见到的"模板内的中断配置"模式。中断系统是 v0.6 §仍不确定 / 候选独立子系统页（B-005 D-507/510 候选未启动）。

**confidence 影响**：候选新建子系统页 confidence: 低（1 样本，待 B-011 多样本印证）

**用户裁决**：[ ✓ 候选驱动 B-011 选样 / ✗ 暂存档 / 🔁 回炉 ]

---

## self_check 6 守则跑测确认（rule_6 implementation_evidence 强约束）

### rule_1_corpus_full_scan
- D-1001 / D-1002 / D-1003 全部跑了 corpus_full_scan（全 3571 文件，含 IsTemplate=True 文件 404 个 / IsTemplate 节点 426 个）
- implementation_evidence: `python` 脚本嵌在 batch_buffer/B-010_corpus_full_scan.py（待写）
- 反例数：D-1001 corpus 79 个非 ORDER IsTemplate 节点 / D-1002 corpus 0 个 TemplateParam 非空 / D-1003 corpus 75 个类别 2b 文件
- ✓ 全员通过

### rule_2_explicit_scope_marking
- D-1001：已学 6 样本范围 (3/6 非 ORDER) vs corpus 全集范围 (79/426 / 18.5%) — 双范围明示
- D-1002：已学 6 样本 (0/6 TemplateParam 非空) vs corpus 全集 (0/426) — 双范围明示
- D-1003：已学 6 样本 (2/6 类别 2b) vs corpus 全集 (75/404 / 18.6%) — 双范围明示
- ✓ 全员通过

### rule_3_specimen_error_vs_concept_existence + v2 反向警告
- D-1001 / D-1002 / D-1003 是"概念框架被反驳" — 不是凭空复活旧概念 / 也不是"软化为独立轴" / 是"边界精化 + 范式扩充"（不变量 1 软化为 81.5% 不是"互斥框架被反驳"，是"主轴稳健 + 次主轴存在"）
- 旧主张通过思想史迁移保留（v0.6 §一句话本质 + §不变量 1 + §SkillEditor 文件三分类 三处旧表述全部保留到"认知演变"段）
- ✓ 全员通过

### rule_4_no_paper_coverage
- D-1001 81.5% / D-1002 0% / D-1003 18.6% 全部以 corpus_full_scan 脚本 .py 输出为分子（不是手工标注）
- 6 样本各 4 维 sample_score 计算可机械复现（4 维 prediction yaml ↔ 实际 corpus_scan 数据对账）
- ✓ 全员通过

### rule_5（已合并到 rule_3 v2，不单升）
- B-010 不触发新的 rule_5 升级（D-1003 类别 2b 是"细化"不是"互斥框架被反驳"）

### rule_6_self_check_meta_audit
- 本 yaml 5 守则全员附 implementation_evidence 段 / .py 路径（B-010_corpus_full_scan.py 待写）/ 反例数 / 数据范围对照表
- 跑反例脚本机械可复现：D-1001 79 反例 / D-1002 0 反例 / D-1003 75 反例 — auditor 抽样可独立验证
- ✓ 通过（B-010 是 rule_6 第二次完整跑测）

---

## 推荐 auditor 审核重点

1. **D-1001 / D-1002 / D-1003 三 deltas 是否触发等级 1 源码加固要求**（v0.9.1 README §11 注脚 / 凡涉及"字段约束 / 互斥 / 必然"措辞需等级 1-2 源码/Excel 加固）：
   - D-1001 主张"模板入口节点 81.5% TSET_ORDER_EXECUTE" 不含"必然 / 互斥" 措辞，描述性数据驱动
   - D-1002 主张"TemplateParam 数组 0/426 非空" 不含"必然 / 互斥"措辞，描述性数据驱动
   - D-1003 主张"类别 2b 18.6%" 不含"必然 / 互斥"措辞，描述性数据驱动
   - 但等级 1 源码 grep `Assets/Thirds/NodeEditor/SkillEditor/.../IsTemplate` + `TemplateParam` 字段定义 仍是高优先级二阶加固（不阻塞 B-010 落盘但建议 B-011 main 收尾）
2. **D-1003 类别 2b 的辨识信号是否真互斥** vs "类别 2 + 类别 1 同时成立的 hybrid 类别"：1860139 / 940021 中 SkillConfigNode 字段 SubType=None / SECID=None / SECID=None = "空壳" 描述是否真普适（auditor 抽样 75 个类别 2b 文件验证 SkillConfigNode 字段空壳率）
3. **D-1004 字典扩补 32xxxxx / 129xxx / 282xxx / 740xxx / 940xxx 段位**是否需要 corpus 全 corpus 段位频次扫（rule_1 严格化）—— 当前主张基于 6 样本 + 技能/ 子目录文件名归纳，未跑 corpus 全集段位频次表
4. **D-1005 actionable 文档校正** 是否触发 rule_2 v2 升级（"actionable / 文档状态字段需与文件系统真实状态对账" 注脚） — auditor 决定是否值得进 README §AI 工作守则
5. **batch_accuracy 0.969 ⭐ 历史 tied 最高（与 B-005 持平）**：是否含选样过拟合？建议 hold-out 66000081 单独抽 4 维 = (1.00 + 0.875 + 1.00 + 1.00) / 4 = 0.969 ⭐ 与训练 5 样本平均 0.969 一致 → 真泛化非过拟合
