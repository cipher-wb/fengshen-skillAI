---
subsystem: SkillTag 系统
confidence: 中
last_review: 2026-05-13
mental_model_version: v0.7
related_postmortems: [017, 018, 019, 020]
related_samples:
  - SkillGraph_30234006_【火宗门】炎龙噬天_天阶_蓄炎流.json
  - SkillGraph_30124001_【火宗门】飞星印_地阶.json
  - SkillGraph_30325002_【土宗门】扩域凝壁_地阶_神通.json
  - SkillGraph_30431000_【金宗门】枪影阻敌_身法_天阶.json
  - SkillGraph_30531005_【金宗门】传承心法_强化普攻3.json
  - SkillGraph_30534004_【火宗门】标签效果_蓄炎.json
  - SkillGraph_30531008_【金宗门】标签效果_蓄势.json
  - SkillGraph_30312003【木宗门】神通_人阶_叶雨.json
  - SkillGraph_30212004【木宗门】奇术_人阶_灵木轰击.json
  - SkillGraph_30512003【木宗门】密卷-人阶30212004.json
mental_model_version: v0.6
---

## 一句话本质

SkillTag 是**技能内部状态系统**：可以是技能级（默认 Param[1]≠0、PT≠0）或实体级（Param[1]=0、PT=0）。**合法声明源有 3 个**（不止 SkillTagsConfigNode）+ 第 4 类系统内置 Tag 豁免；跨技能读 tag 必须用实体级；ID 不能超 int32 max；**心法注入运行时合并是三态**（情形 A 写入 / 情形 B 累加 / 情形 C 兜底初始值 — 见 §F）。SkillTag 与 [Buff 系统](Buff系统.md) **并列**而非从属，两者解决不同问题。

---

## 关键不变量（违反就 100% 出问题）

### A. 三个合法声明源（B-001 D-3 首次确立）

1. **`SkillTagsConfigNode`（flow 内）** — 节点级声明，唯一 lint 当前会检的源
2. **`SkillConfig.SkillTagsList`（顶层数组）** — SkillConfig 文件级声明，lint 当前漏检
3. **`SkillConfig.SkillDamageTagsList`（顶层数组）** — 伤害对子专用顶层声明，lint 当前漏检

证据（[batch_buffer/B-001.yaml D-3](batch_buffer/B-001.yaml)）：
- 30431000 tag 5 在 `SkillDamageTagsList:[{Tag:5,Value:30}]` 已声明 → lint E019 误报
- 30531005 tag 3 在 `SkillDamageTagsList:[{Tag:3,Value:12000}]` 已声明 → lint E019 误报
- 30124001 tag 54 在 `SkillTagsList`、tag 1201 在 `SkillDamageTagsList` 已声明 → lint E019 误报
- 30325002 tag 301 / 1001 三处都没声明 → lint E019 **真 positive**（跨技能读）

**最少 1 源也合法**（B-003 D-309 观察）：蓄势型纯心法可仅靠源 1 完成——30531008 顶层 SkillTagsList 全空 / SkillDamageTagsList 全空 + 8 个 flow 内 SkillTagsConfigNode（仅靠源 1）。与 30534004（顶层 + flow 内并行，3 源协作）形成对照：**3 源是"协作并集"而非"互斥"或"必须三全"——最少可仅 1 源**。

#### §A.补 第 4 类「系统内置 Tag」豁免（v0.5 / 2026-05-12 / Mode B 30312003 入库）

除上述 3 个**蓝图侧**声明源外，存在第 4 类——**系统内置 Tag**，由引擎在运行时 / 全局 `SkillTagsConfig.xlsx` 配表中预定义。它不需要任何蓝图侧声明也可以被 GET / ADD / MODIFY_SKILL_TAG_VALUE 直接读写。

**判定特征**：
- **小 ID（经验值 1xxx-9xxx）** → 高度怀疑系统内置 / 应查 SkillTagsConfig.xlsx 全局表确认
- **大 ID（≥ 100000，如 320xxx / 22xxxxx 等段位号系）** → 高度自定义 / 必须三声明源至少 1 源
- **判定经验是 hedge 而非铁律**（待 B-054+ Excel 加固后填实全集）

**审核规则**：
- **小 ID 三声明源全空** → **不报错**（系统内置 / lint E019 应静默）
- **大 ID 三声明源全空** → **报错**（自定义 Tag 未声明 / lint E019 真 positive）

**证据**：
- 等级 1：用户 2026-05-12 明确口头裁决——"TagID=1001 是系统内置 SkillTag，不需要 SkillTagsConfigNode 声明"
- 等级 2：30312003 fs 真扫——只有 1 个 SkillTagsConfigNode（覆盖该技能自身定义的 tag），其中 TagID=1001 出现 3 次（参数值位置），顶层 SkillTagsList / SkillDamageTagsList 与 flow 内 SkillTagsConfigNode 均未声明 1001，技能正常运行 → 1001 必然来自第 4 源 = 系统内置
- 等级 2 反向印证：30325002 历史样本中 tag 1001 → 修订归类为系统内置（不再是"真 cross-skill 读" positive），tag 301 仍 candidate 待 Excel 对账

**待办（B-054+ 加固）**：
- 工具加固：读 `{{SKILL_EXCEL_DIR}}/SkillTagsConfig.xlsx` 转表 → 填实 Tag 全集（含 1001 的 Desc / Type / 系统标记）
- lint E019 修复方案：检 3 源后还需扫第 4 源系统内置 Tag 白名单
- ID 阈值精化：1xxx-9xxx hedge → 待 Excel 加固后给出精确阈值

### B. 跨技能读 tag 的写法（PostMortem #019）

跨技能读必须用**实体级**（`Param[1]=0` / `PT=0`），不能用技能级（[postmortem #019](../postmortem/2026-05-08-019-entity-level-tag.md)）。Pattern C：`Param[1]=源技能ID 或 0`。

> **v0.5 注脚（2026-05-12 / Mode B 30312003 入库）**：本节是 lint E019 视角的「跨技能**读**」最小不变量；同样的实体级机制还允许**双向读写**的有意设计范式 —— 详见 [§E 跨技能 Tag 耦合模式（candidate）](#e-跨技能-tag-耦合模式candidate)。§B 主张本体不变（rule_2 严守）。

#### §B.补 GET/ADD/MODIFY_SKILL_TAG_VALUE 节点 P[1] 速查表（v0.7 / 2026-05-13 memory 升级入库）

> 来源：[memory/feedback_skilltag_scope_p1_meaning.md](../../../memory/feedback_skilltag_scope_p1_meaning.md) + [memory/feedback_get_skill_tag_value_p1_scope.md](../../../memory/feedback_get_skill_tag_value_p1_scope.md) / 2026-05-12 配 30212018 立法。

**Params 语义铁律**：

| 字段 | 含义 | 常见值 |
|------|------|--------|
| **P[0]** | 实体 scope（写/读到哪个 entity 的 SkillTag 槽位）| `{V=4, PT=5}` = caster 释放者 / `{V=1, PT=5}` = main entity / `{V=75, PT=1}` = 某 attr 引用的 entity |
| **P[1]** ⭐ | **SkillTag 所属技能 ID / 实例 ID（决定 SkillTag 定义在哪个蓝图）** | `{V=技能ID, PT=0}` 或 `{V=41, PT=5}` (OriginSkillInstID) |
| **P[4]** | 与 P[1] 模式联动 | 模式 A → P[4]=0；模式 B → P[4]=1 |

**P[1] 两种模式速查表**：

| 模式 | P[1] 值 | P[4] | 含义 | 适用场景 | SkillTag 定义所在蓝图 |
|------|---------|------|------|---------|----------------------|
| **A 跨技能** | `{V=技能ID, PT=0}` 或 `{V=0, PT=0}` | 0 | SkillTag 挂在 V 对应的技能/buff 上，跨次释放共享 | "buff/技能持久"的计数器 | **V 对应技能蓝图内** |
| **B 当前实例** | `{V=41, PT=5}` | 1 | SkillTag 挂在 OriginSkillInstID（每次释放 unique）| "单次释放内累加，跨次不保留" | **当前蓝图内** |

**金标范式（30212010 ADD 碧叶计数）**：

```
32002231 ADD_SKILL_TAG_VALUE Params:
  P[0] = {V=4, PT=5}          # caster scope
  P[1] = {V=30212011, PT=0}   # 模式 A / 挂在 三重碧叶技能 30212011 上 ⭐ 不是 30212010
  P[2] = {V=320100, PT=0}     # SkillTag ID
  P[3] = {V=1, PT=0}          # step
  P[4] = {V=1, PT=0}          # → 与 P[1]模式 联动
```

→ SkillTag 320100 **定义节点在 SkillGraph_30212011 三重碧叶蓝图内，不在 30212010**！

**判断模式的工作流（Sensor）**：

1. **新建 GET/ADD/MODIFY_SKILL_TAG_VALUE 节点前**：先看**同一技能文件内已有的同类节点**（而不是去其他文件找参考）
2. **若目标 tag 的 SkillTagsConfigNode 在当前 JSON 文件内** → 模式 B：`P[1]={V=41, PT=5}, P[4]=1`
3. **若目标 tag 在其他技能文件** → 模式 A：`P[1]={V=那个技能ID, PT=0}, P[4]=0`
4. **禁止**：从 BUFF 文件 / 跨技能文件抄 P[1] 用于当前蓝图内 tag 读取（PostMortem 同源 30212010 32900147 误抄事件）

**评估"是否要复制 SkillTag 定义"时的应用**：
- 模式 A（P[1] PT=0 + V=某技能ID）→ SkillTag 定义在那个技能蓝图，**不在当前蓝图** → 当前蓝图 mv/删时不影响，**不用复制**
- 模式 B（P[1] = {V=41, PT=5}）→ SkillTag 定义在当前蓝图 → 当前蓝图 mv/删前**必须复制**

### C. ID 不能超 int32 max（PostMortem #018）

任何 SkillTag ID 大于 `2,147,483,647`（int32 max），Newtonsoft.Json 会反序列化失败（[postmortem #018](../postmortem/2026-05-08-018-int32-overflow.md)）。

### D. 1 号子弹的伤害对子配对铁律

伤害必须**威力系数 + 额外伤害成对**（[memory/reference_bullet_damage_tag_pairs.md](../../../memory/reference_bullet_damage_tag_pairs.md)）：
- 1 号子弹：威力系数 tag=3 / 额外伤害 tag=5
- 2 号子弹：威力系数 tag=1201 / 额外伤害 tag=1211
- 3 号子弹：威力系数 tag=1202 / 额外伤害 tag=1212

30124001 真样本印证：`SkillDamageTagsList:[{Tag:1201}, {Tag:3}]` ↔ 1 号子弹伤害对子（[diffs/30124001.md](diffs/30124001.md) 教训 4）。

### E. 跨技能 Tag 耦合模式（candidate / v0.5 / 2026-05-12 / Mode B 30312003 入库）

> **状态**：candidate，距升正式需 ≥3 宗门 / ≥5 样本实证 + AI 自决升正式 4-gate 全通过

**模式定义**：同一宗门的不同技能之间，允许通过**硬编码对方技能 ID**（`P[1]={V=源技能ID, PT=0}` 实体级），**双向读写**对方的自定义 SkillTag，实现技能间的**状态共享与联动**。是**有意设计**，非"踩坑误用"。

**典型范式**（木宗门 30312003 叶雨 ↔ 30212011 三重碧叶 实证）：

| 动作 | 节点（rid） | 目标技能 | TagID / BuffID | 语义 |
|------|------------|---------|----------------|------|
| ADD  | TSET_ADD_SKILL_TAG_VALUE (32002584) | 30212011（三重碧叶） | TagID=320100 | 每次叶雨发射飞叶 → 三重碧叶计数 +1 |
| GET  | TSET_GET_SKILL_TAG_VALUE (32002899) | 30212011（三重碧叶） | TagID=320100 | 读三重碧叶当前计数 → 决定本次飞叶是否强化（第 3 颗） |
| CHECK | TSCT_HAS_BUFF (320315 / 320347)    | 30212011（三重碧叶） | BuffID=320037 | 检查三重碧叶 BUFF 是否激活（状态联动加强） |

**设计语义**：
- **主技能（叶雨）= 输入源驱动方**：发动时主动写入 / 读取副技能的 Tag
- **副技能（三重碧叶）= 状态容器方**：拥有 Tag 命名空间，自身负责重置逻辑
- **Tag 计数跨次施法累积**：主技能不重置（信号叠加），副技能内部按其规则消耗 / 重置

**与现有不变量的协同关系**（rule_2 严守 / 不撤回任何主张本体）：
- **不撤回 §B**：跨技能读 tag 用实体级 `P[1]={V=源ID/0, PT=0}` 仍然是底层机制（lint E019 视角）
- **不撤回 PostMortem #019**：实体级 tag 写法仍是必要条件
- **§E 是正向化扩展**：§B 从 lint 视角描述"什么时候必须用实体级"，§E 从设计视角描述"为什么这样做" —— 实体级 tag 不是只读耦合，而是**双向读写的设计基元**，宗门设计师有意用它实现技能间状态共享

**续累积观察清单**（升正式 readiness）：

| 候选样本 | 段位 | 待验证范式 |
|---------|------|-----------|
| 火宗门 30234006【蓄炎流】 | 30234xxx | 蓄炎类型 Tag / 待复审是否本范式 |
| 金宗门 30531008【蓄势】 | 30531xxx | 蓄势类型 Tag / 待复审 |
| 土宗门 30325002【扩域凝壁】 | 30325xxx | tag 301 来源待 B-054+ Excel 对账 / 若为他技能私有 Tag 则纳入本范式 |
| 其他木宗门联动技能 | 303xxxxx | 待 picker 续选定位 |

**升 candidate / 升正式路径**：
- 累积 **≥3 宗门 / ≥5 样本**实证 → 升 candidate（同 D-2401 / D-4002 模式）
- 累积 ≥5 实证 + auditor R0 推荐 → AI 自决升正式 4-gate（Gate (a)~(g) v3 全通过）

**证据**：
- 等级 1：用户 2026-05-12 口头裁决 —— "跨技能 Tag 耦合是木宗门有意设计（叶雨读写三重碧叶的 Tag）"
- 等级 2：30312003 fs 真扫 —— 30212011 在文件中出现 2 次 / BuffID 320037 出现 2 次 / TagID 320100 出现 2 次，形成完整 ADD/GET/CHECK 三角

### F. 心法注入参数的合并语义（v0.6 / 2026-05-13 / 用户口头裁决入库）

> **状态**：升正式不变量（用户 2026-05-13 直接口述三规则 / 等级 1 证据 / 业务通行用语"覆盖"为流通表述误差 / 实际语义为"累加 / 写入 / fallback"三态）

**适用场景**：心法（Xinfa 被动技能）通过 SkillConfig 首节点 Inspector 字段 **「心法专属-给满足条件的其他技能里塞参数列表」**（对应 SkillValueConfig 表 `SkillTipsConditionSkillTagsList`），向关联的功法（主动技能）的某个 SkillTag **塞入数值** 时，**最终生效值** 的合并算法。

**核心铁律**：
- **心法注入只与功法 SkillConfig 顶层「技能参数列表」（`SkillTagsList`）交互**，**不与** flow 内 `SkillTagsConfigNode` 的初始值（`Value` 字段）交互
- 初始值是**最后兜底**，只在 `SkillTagsList` 无该 tag 且无心法注入时被读取

**三种情形 / 真值表**：

| 情形 | flow 内 SkillTagsConfigNode 初始值 | 顶层 SkillTagsList 是否含该 tag | 心法塞入 | **最终生效值** | 合并行为 |
|------|----------------------------------|-------------------------------|---------|---------------|---------|
| **A** | 1000 | **无** | 500 | **500** | 心法值**直接写入**（覆写默认） |
| **B** | 1000 | **有，值=300** | 500 | **500 + 300 = 800** | 心法值**加到列表原值上**（累加） |
| **C** | 1000 | **无** | **无** | **1000** | **fallback 到 SkillTagsConfigNode 初始值** |

**算法伪码**：

```
finalValue =
  if SkillTagsList 包含该 tag (原值 = X):
    if 心法塞入 (心法值 = Y):
      return X + Y                # 情形 B：累加
    else:
      return X                    # SkillTagsList 单独提供，无心法
  else:                            # SkillTagsList 不含该 tag
    if 心法塞入 (心法值 = Y):
      return Y                    # 情形 A：直接写入
    else:
      return SkillTagsConfigNode.Value    # 情形 C：兜底初始值
```

**关键反直觉点 / 业务通行误解**：

| 误解（业务通行说法） | 精确语义（实际行为） |
|---------------------|---------------------|
| "心法塞入会**覆盖** SkillTag 默认值" | 仅情形 A 是覆写；情形 B 是**累加**，不是覆盖 |
| "SkillTag 初始值 vs 心法值 二选一" | **三态**：列表原值 / 列表原值+心法值 / 兜底初始值 |
| "在 flow 内 SkillTagsConfigNode 改初始值就能改最终生效值" | **不能**。一旦 SkillTagsList 声明了该 tag 或心法塞入了该 tag，初始值就被忽略 |

**与 §A 三声明源关系（rule_2 严守 / §A 主张本体不变）**：
- §A 三声明源讲的是「声明是否合法 / lint 是否报错」的视角
- §F 讲的是「运行时合并 / 最终值如何计算」的视角
- 两者**正交互补**：可以在 §A 三源中任意组合声明，但**心法注入路径**只识别顶层 `SkillTagsList`（源 2）作为"累加底盘"
- 因此**为了让心法注入走累加分支（情形 B），功法必须在顶层 SkillTagsList 显式声明该 tag 并给定累加底值**；若只在 flow 内 SkillTagsConfigNode 声明（源 1）则心法注入走情形 A（直接写入，与初始值无关）

**典型业务样本**：
- 功法 `30212004【木宗门】奇术_人阶_灵木轰击` — TagID `320058`（灵木轰击蓄能点数）作为消费方
- 心法 `30512003【木宗门】密卷-人阶30212004` — 首节点 Inspector「心法专属-给满足条件的其他技能里塞参数列表」声明 `{320058, 0}`
- 数值表 `SkillValueConfig-XinFa` `SkillTipsConditionSkillTagsList` 字段填 `灵木轰击蓄能点数,1`
- 通过 `SkillXinfaConfig.ConditionSkills[0]=条件ID|心法ID|心法等级` 关联

**配置建议（给策划）**：
- **想做"心法叠加增益"**（如心法 +N 蓄能、+N 段数、+N 倍率）→ **必须**在功法顶层 SkillTagsList 显式声明该 tag 并给定**累加底值**（情形 B）
- **想做"心法解锁新数值"**（功法默认无、心法激活后才生效）→ 顶层 SkillTagsList 不声明该 tag，心法值直接写入（情形 A）
- **想做"功法独立基线"**（无心法时也要有默认值）→ flow 内 SkillTagsConfigNode 给初始值（情形 C 兜底）

**升正式依据（无需 candidate 走 fast-path 真硬停 #5）**：
- 等级 1：用户 2026-05-13 直接口述三规则 + 给出具体数字示例（1000 / 300 / 500 → 500 / 800 / 1000）
- 不构成概念反转：与 §A 三声明源并行存在 / §A 主张本体不变 / 仅新增"运行时合并视角"
- 非命名空间细化 / 非 rule 编号修订 / 是新的不变量主张本体

**待办（B-054+ 加固）**：
- 源码 grep 验证：在 `Assets/Scripts/HotFix/Game/Battle/` 找心法注入合并函数（关键词 `SkillTagsList` + `Add` / `Set` / `XinFa` / `条件技能`）确认 +/写入两分支实现
- Excel 对账：`SkillValueConfig-XinFa` 全量样本扫描，确认 `SkillTipsConditionSkillTagsList` 字段格式 `tag名,值` 在引擎侧的合并行为
- 反例边界：心法塞同一 tag 的多个等级是否互相覆盖 / 多心法都塞同一 tag 时是否累加（多心法 vs 多等级）

---

### F.1 心法注入双键映射 / 静默失效铁律（v0.6.1 patch / 2026-05-14 / AI 自决细化 / 非概念反转）

> **状态**：升正式不变量细化（§F v0.6 的工程实现细节补强 / 来源 = 用户 2026-05-14 让 AI 阅读 `心法强化功法的配置.md` §4.2 警示后立刻补 / 等级 1 证据）
>
> **rule_2 严守**：§F v0.6 主张本体不变 / 本 §F.1 仅补"双键映射不一致 → 静默失效"的工程实现风险

**核心铁律**：心法注入链路中**同一个 SkillTag 同时被两种 key 引用**，且两端各自维护 / 必须**逐字符一致**：

| 位置 | key 形式 | 示例 |
|------|---------|------|
| 心法首节点 Inspector「心法专属-给满足条件的其他技能里塞参数列表」 | **数字 tag ID** | `320058` |
| `SkillValueConfig.xlsx` → `SkillValueConfig-XinFa` 页签 / `SkillTipsConditionSkillTagsList` 字段 | **tag 中文名**（= `SkillTagsConfig.ConfigJson.Desc`） | `灵木轰击蓄能点数` |

**静默失效特征**（高频踩坑）：
- 名字差一个字 / 一个空格 / 一个标点 → 整条链路**不报错 / 不警告**
- 表现：游戏内 UI **不显示**「所受心法加成：XX心法」/ 功法逻辑读不到注入值 / 走 §F 情形 C 兜底（初始值）
- 排查极困难：四张表（功法/心法/SkillXinfaConfig/SkillValueConfig-XinFa）单独看都"合法"

**与 reference_skilltag_desc_unique.md memory 的因果关系**：
- 该 memory 已立法 `SkillTagsConfig.ConfigJson.Desc` 必须**全工程唯一 + ≤15 字 + 风格 `<技能名><变量名>`**
- **本 §F.1 解释了为什么必须这样**：Desc 在 SkillValue 表中作为 **跨表 key** 使用 / 重名 → 多心法注入冲突 / 字符不一致 → 静默失效
- 例：320957 旧名「叶散风行强化开关」改为「叶散风行-寻踪术装备态」（2026-05-14 用户实例） / 含技能名前缀避免跨技能撞名 / 含具体语义降低改名成本

**配置自检清单**（配心法塞参时强制 4 步）：
1. 功法 `SkillTagsConfig.ConfigJson.Desc` 全工程 grep 唯一 ✓
2. 心法首节点 Inspector「塞参数列表」填**数字 tag ID** ✓
3. `SkillValueConfig-XinFa.SkillTipsConditionSkillTagsList` 填的 tag 名与功法 SkillTag 节点 Desc **逐字符一致** ✓（推荐 Excel 公式从功法 Desc 反查 / 不要手敲）
4. `SkillXinfaConfig.ConditionSkills[0]` = `条件ID|心法ID|心法等级` 每级一行 ✓

**升正式依据（无需 candidate 走 fast-path 真硬停 #5 / AI 自决细化 4-gate 满足）**：
- 等级 1 证据：用户 2026-05-14 提供 `E:\wb\封神工作文档\AAAA本地设计工作文档\2025年9月三测相关\技能表格配置工具\心法强化功法的配置.md` §4.2 明文警示「键的形式差异（高频踩坑点）」+ 「tag 名写错一个字、空格、标点，整条链路会静默失效」
- 等级 1 业务实例：320957「叶散风行-寻踪术装备态」改名事件（2026-05-14）= memory `reference_skilltag_desc_unique.md` 立法的工程根源
- 非概念反转 / §F 三态主张本体不变 / 仅补"key 形式差异"的工程实现细节
- 0 反预测 / 不构成跨级 rule 修订 / 不修订正式 rule 段（落盘到 §F 之后新增 §F.1 / 同 v0.6 落盘模式）

**待办（B-054+ 加固）**：
- 工具：写 lint 脚本对账「功法 SkillTag Desc」↔「SkillValueConfig-XinFa.SkillTipsConditionSkillTagsList tag 名」全量一致性扫描
- 反例边界：tag 名含 Unicode 全角/半角字符差异是否影响匹配（如 `-` vs `－`）

⭐ **2026-05-14 区分新立**：本节涉及的 `SkillPreConditionConfig`（SkillXinfaConfig.ConditionSkills[0] 里的"条件 ID" / 心法注入触发条件 / **Excel 配**）与 `RUN_SKILL_EFFECT_TEMPLATE.ParamUID 8` 引用的 `SkillConditionConfig`（技能内伤害增益触发条件 / **蓝图 TSCT 节点配 / NodeEditor 自动导出**）**不是同一张表**。详见独立子页 [SkillCondition系统.md](SkillCondition系统.md) §C。

---

### F.2 Inspector「心法专属-塞参数列表」Value 双路径并行（v0.6.2 patch / 2026-05-14 / 反例驱动校准 §F 描述）

> **状态**：升正式不变量校准（§F v0.6 描述"Inspector 是占位 0 + 真实数值由 SkillValueConfig-XinFa 传入"是**单路径描述** / 实际项目存在**双路径并行**惯例 / 本节补强 / 来源 = 用户 2026-05-14 实例 "Inspector 直接填 10"+ 寻踪术 30512005 既有 3 条惯例 [{320962,1000}, {320964,100}, {320957,1}] 全部 Value 非 0 锚定）
>
> **rule_2 严守**：§F v0.6 "占位 0 + Excel 传值"路径主张本体保留（适用于按等级配数值的标准 §F 流程）/ 本 §F.2 补强"Inspector 直接填值"路径（适用于固定值 / 不按等级变化的简化场景）

**路径对照表**：

| 路径 | Inspector Value | SkillValueConfig-XinFa | 适用场景 |
|------|----------------|------------------------|---------|
| **§F 标准路径**（v0.6）| 0（占位）| 必填 `<tag名>,<实际值>` 每级一行 | 心法等级越高数值越大 / 多等级阶梯配置 |
| **§F.2 简化路径**（v0.6.2）| **直接填实际值** | 可填可不填（如填仍走 §F 三态合并 + 累加底盘语义）| 固定值 / 心法等级不影响数值 / 装备态 0/1 旗帜 |

**实例（寻踪术 30512005 SkillTipsConditionSkillTagsList 现状）**：
- `{320962, 1000}` — 直接 1000 / 非占位 0
- `{320964, 100}` — 直接 100 / 非占位 0
- `{320957, 1}` — 装备态旗帜 / 直接 1 / 非占位 0
- `{320966, 10}` — 2026-05-14 新增 / 叶散风行寻踪术条件附加伤害定值 / 直接 10 / 非占位 0

**与 §F 三态合并算法关系**：
- 简化路径下 Inspector Value 仍参与 §F 三态算法
- 功法 SkillTagsList 含该 tag = 走 §F 情形 B 累加（Inspector Value + SkillTagsList 原值）
- 功法 SkillTagsList 不含 = 走 §F 情形 A 直接写入
- 心法塞入"实际值"还是"占位 0"在三态算法层完全等价 / 路径区别仅在"是否依赖 SkillValueConfig-XinFa 阶梯化"

**判定速查**：策划要"心法升级伤害也跟着涨" → 走 §F 标准路径；要"装备就有 / 不装备就没有 / 与等级无关" → 走 §F.2 简化路径。

**升正式依据**：等级 1 实证（寻踪术 SkillTipsConditionSkillTagsList 4 例 100% Value 非 0）+ 用户 2026-05-14 实操确认 / 非概念反转 / §F 主张本体不动 / 是同一机制的两个并行路径。

---

### F.3 RUN_SKILL_EFFECT_TEMPLATE.ParamUID 10 形式=4 时脱万分比反直觉点（v0.6.3 patch / 2026-05-14）

> **状态**：升正式反直觉点（来源 = 用户 2026-05-14 口头确认 / 等级 1 业务实例 30212010 寻踪术条件附加伤害定值 10）

**铁律**：「子弹通用逻辑-伤害」模板（`SkillEffectType=118`）的 `ParamUID 10 = 技能增伤-值（万分比）` 字段名虽然标注"万分比"，但**仅当 ParamUID 9 = 1/2/3（B类增伤/C类增伤/最终倍率）时单位才是万分比**；当 ParamUID 9 = 4（条件附加伤害）时 **ParamUID 10 是固定数值 / 脱离万分比单位**。

| ParamUID 9 取值 | ParamUID 10 单位 | 示例 |
|----------------|------------------|------|
| 1 / B 类增伤 | 万分比 | 1000 = 10% 增伤 |
| 2 / C 类增伤 | 万分比 | 同上 |
| 3 / 最终倍率 | 万分比 | 1500 = 1.5x 最终倍率 |
| **4 / 条件附加伤害** ⭐ | **定值** | **10 = +10 点固定伤害**（不是 0.1%）|

**踩坑特征**：策划想 "+10 点附加伤害" 凭"万分比"字面理解填 100000（= 10% 想成 1）→ 实际生效 100000 点伤害 / 直接秒杀；或填 10 想"0.1%"实际正好就是策划想要的 +10 → 误以为字段单位字面正确。

**配套实例**：叶散风行 30212010 / 4 个伤害 RST 节点 Params[12]（= ParamUID 10）= `{V:0, PT:0}` 占位 + edge 连线到 GET_SKILL_TAG_VALUE(320966) / 寻踪术装备时 tag=10 / 等价 ParamUID 10=10 / 即 +10 点附加伤害。

**升正式依据**：等级 1（用户 2026-05-14 口头确认 + 蓝图实际填法对照）+ 非概念反转 / 与 §F 正交。

---

### G. SkillTag 命名空间 = (ID, cid) 二元组（candidate / v0.16.40 / B-061 D-6107 / 细化 reference_skilltag_builtin_ids.md / NOT 撤回旧主张）

> **状态**：candidate / 1 对 (ID, cid) 二元组实证 / 升 candidate 后续累积 ≥3 对实证
>
> **rule_2 严守**：memory/reference_skilltag_builtin_ids.md "小 ID 系统内置无需声明 / 大 ID 必须 SkillTagsConfigNode" 旧主张本体保留 / 部分场景仍适用 / 本 §G 仅细化为正交命名空间维度

**主张本体**：

SkillTag 真正命名空间**不是单 ID** 而是 **(ID, cid) 二元组**。同一 SkillTag ID 可在不同 cid 下承载**完全不同的语义**。

**典型例 — Tag41**：

| (ID, cid) | 语义 | 出处 |
|----------|------|------|
| (41, 1460084) | 当前伤害类型 | B-060 L2 review 146004930 |
| (41, 1460110) | 化解成功标记 | B-061 L3 fs 真扫 146004834 |

**意义**：

- 细化 `memory/reference_skilltag_builtin_ids.md` 系统内置 Tag 豁免判定不能只看 ID
- 同 ID 不同 cid 时**不能假定共享语义** / 必须逐 cid 验证
- 审核 SkillTag 使用时 P[1] / P[2] 之外**还要看 cid**

**关联子系统**：详见 [伤害管线.md §P3 反直觉点](伤害管线.md) / 子弹伤害管线 25 deltas 蒸馏初版第一次落地命名空间二元组细化。

---

### H.前 §命名规范铁律 — Desc 全工程必须唯一 + 两层描述（v0.7 / 2026-05-13 memory 升级入库）

> 来源：[memory/feedback_skilltag_desc_unique.md](../../../memory/feedback_skilltag_desc_unique.md) / 2026-05-12 复制 30212017 → 30212018 时立法。

**铁律**：SkillTag 必须 **2 个维度同时唯一**：

| 维度 | 规则 | 工具检查 |
|------|------|---------|
| **ID** | 全工程唯一 | `id_allocator.py` 自动避让 |
| **中文描述 (`ConfigJson.Desc`)** | 全工程唯一 ⚠️ 易忘 | Excel 转表 `checkHelper.lua` 时 fail |

**ID 唯一**用 [工具链.md §E id_allocator](工具链.md) 自动；**Desc 唯一**需要人工管。

**反例（实战触发立法）**：
```
SkillTagsConfig 技能参数描述重复：xxx, ID:  320937, 320950
```
（2026-05-12 把 30212017 蓝图复制成 30212018，8 个 SkillTag ID 重分配避开冲突但**中文描述照搬** → 转表 fail）

**两层描述模式 / 风格**：

| 字段 | 角色 | 长度 | 示例 |
|------|------|------|------|
| **`ConfigJson.Desc`** | **"中文变量名"** | **短 (≤15 字)** | `叶散风行PoC-自旋速度` |
| **`data.Desc`（节点级）** | **详细说明** | 可长 | `每帧 facing 旋转角度°/帧 / -6=1秒1圈 / 负=顺时针 / 0=不转` |

**30212010 风格金标**：`<技能名><变量名>` 短而清晰
- `320098 "叶散风行子弹数量"`
- `320110 "叶散风行中本次飞强化"`
- `320127 "叶散风行追踪范围"`

**复制技能时的标准做法**：每个新 SkillTag 描述末尾必须加技能名后缀

```
原 30212017 SkillTag 320938 Desc: "出生半径（叶子离主角多远爆发出现）/ 200..."
新 30212018 SkillTag 320953 Desc: "出生半径（叶子离主角多远爆发出现）/ 200... 【叶散风行 PoC】"
```

后缀格式参考：`【<技能中文名>】` 或 `【<技能ID-类型>】`。

**Sensor**：转表 Excel 报 "技能参数描述重复" 错 → 第一时间扫复制过的技能内 SkillTag 描述，加技能名后缀。

**已纳入代码护栏**：`doc/SkillAI/tools/builders/*.py` 复制 SkillTag 时自动加后缀。

### H.前补 §SkillTag ID 等级速查铁律 — 内置 vs 自定义（v0.7 / 2026-05-13 memory 升级入库）

> 来源：[memory/reference_skilltag_builtin_ids.md](../../../memory/reference_skilltag_builtin_ids.md) / 2026-05-12 审核 30312003 叶雨时用户口头确立。

**核心铁律**：

| ID 等级 | 经验阈值 | 是否需要 SkillTagsConfigNode 声明 | lint E019 判定 |
|---------|---------|----------------------------------|---------------|
| **小 ID（系统内置）** | 1xxx-9xxx 经验 / 待 Excel 加固精确阈值 | **不需要**（引擎运行时 / 全局 `SkillTagsConfig.xlsx` 预定义）| 三声明源全空 → **不报错**（lint E019 应静默） |
| **大 ID（自定义）** | ≥ 100000（如 320xxx / 22xxxxx 段位号系）| **必须**三声明源至少 1 源 | 三声明源全空 → **报错**（真 positive） |

**已知系统内置 Tag（小 ID 示例）**：

| Tag ID | 用途 |
|--------|------|
| **1001** | 通用本地计数器（叶雨中用作子弹序号计数，每次发射圈前清零）|
| **3, 5** | 1 号子弹"威力系数 / 额外伤害"标准配对（见 §D 主表）|
| **1201, 1211** | 2 号子弹"威力系数 / 额外伤害"配对 |
| **1202, 1212** | 3 号子弹"威力系数 / 额外伤害"配对 |
| **16** | 用途待 Excel 加固确认（叶雨伤害模板 P5 使用）|

**已知自定义 Tag（大 ID 示例）**：
- 320xxx 系列（木宗门）：`320098 叶散风行子弹数量` / `320100 飞叶数量（三重碧叶）` / 等
- 22xxxxx 系列（其他宗门段位号系）
- 146xxxxx 系列（伤害管线 / 见 [伤害管线.md §字典](伤害管线.md)）

**判定经验是 hedge 而非铁律**（待 B-054+ Excel `SkillTagsConfig.xlsx` 加固后填实全集）。

**与 §G (ID, cid) 二元组细化的关系**（rule_2 严守 / NOT 撤回）：
- 本 §等级速查是**单 ID 视角**的"是否需要声明"问题
- §G (ID, cid) 二元组是**同 ID 不同 cid 时语义可不同**的细化（适用大 ID 居多）
- 两者**正交互补**：先判 ID 等级是否需要声明；再看 cid 决定具体语义

**Sensor**：审核时看到小 ID SkillTag 无 SkillTagsConfigNode → **不报错**；看到大 ID SkillTag 无 SkillTagsConfigNode → **报错**。

---

### H. B-060+B-061 SkillTag ID 字典补全（v0.16.40 / B-060 D-6006 R1 修订后）

> **状态**：字典扩展 / 注解类 / NOT 升 candidate / NOT 升正式 / 升正式前需 Excel `SkillTagsConfig.xlsx` 对账加固
>
> ⚠️ **R1 修订**：B-060 R0 D-6006 字典含错误 tag_id=146004858 闪避条目 / 来源主对话接力消息错误断言 / B-061 D-6113 fs 真扫推翻 / 实际 1460112 / **rule_2 严守**：R0 错误条目作思想史保留作反面教材 / GATE-CONSISTENCY 立法触发实例 #1

详见 [伤害管线.md §字典 SkillTag ID 字典补全](伤害管线.md) 完整表格。核心条目（首批字典扩展）:

- Tag273 = 伤害缓存 / Tag184 = 会心增伤累加 / Tag191 = 化解增伤累加（builtin）
- Tag1460079 = 威力系数 / Tag1460110 = C 类增伤 (cid 1460110 时为化解成功标记 / 见 §G)
- Tag1460111 = B 类增伤
- **Tag1460112 = 闪避结果（1=闪了 / 0=没闪 / 反直觉）** （R1 新增 / 替换 R0 错误 ID 146004858）
- Tag1900120 = 护体灵光削减倍率 / Tag1860139 = 特殊条件标签
- Tag660061 = 伤害重算标记（B-059 candidate）

---

## 反直觉点（容易踩的）

1. **lint E019 当前 4/5 样本都误报** — 本批 5 样本只有 1 个真 cross-skill 读（30325002），其他 4 个都是 SkillConfig 顶层已声明的"看似未声明"。审核技能时**先排除顶层声明再判 E019**，不能直接信 lint（[batch_buffer/B-001.yaml D-3](batch_buffer/B-001.yaml)）。

   > **v0.5 注脚（2026-05-12 / Mode B 30312003 入库）**：B-001 D-3 评估 30325002 中所述"tag 301 / 1001 三处都没声明 = 真 cross-skill positive"修订为：
   > - **tag 1001 已闭环** = 系统内置 Tag（见 §A.补） / lint E019 对系统内置应豁免 / 不再视为真 cross-skill 读 positive
   > - **tag 301 仍 candidate** = 待 B-054+ 读 `SkillTagsConfig.xlsx` 对账后才能判定（可能系统内置 / 可能真 cross-skill 读他技能私有 Tag）
   >
   > lint E019 修复方案需先排除"系统内置 Tag 白名单"，然后再判三声明源缺失。**rule_2 严守**：原 v0.2 论断保留作思想史 / 仅加注脚 / 不删除。

2. **SkillTag ≠ Buff** — SkillTag 是数值状态（持久 / 派生计算），Buff 是结构化状态（带时长 / 层数 / 效果）。心法计层用 buff_layer 不用 SkillTag（[Buff 系统.md](Buff系统.md)）。

3. **声明源 1 vs 2/3 的协作关系**（B-002 D-207 部分回答）：
   - 源 1（flow 内 SkillTagsConfigNode）= flow 内运行时声明 + 初始值（含 Desc）+ 同 flow 可读写
   - 源 2（顶层 SkillTagsList）= 此技能用到的 tag 清单（让运行时分配槽位）
   - 源 3（顶层 SkillDamageTagsList）= 伤害对子专用顶层声明
   - **同一 tag 可在两源同时声明**（30534004 真证据：tag 2200140 顶层 SkillTagsList 与 flow 内 SkillTagsConfigNode rid=1025 同时存在），不是互斥/覆盖，是**协作并集关系**
   - 部分 tag 只在源 1 出现也合法（30534004 tag 2200133 / 2200158 仅 flow 内声明）

   **新增反直觉 4：3 声明源协作非互斥** — 顶层数组的作用是"让运行时分配槽位 + 工具校验"，不是与 flow 内声明互斥；判断"tag 是否声明"时必须 OR 三源，不能三源选一。

---

## 与其他子系统的因果关系

- SkillTag → **控制流子系统**：`TSCT_VALUE_COMPARE` 读 tag 决定 CONDITION_EXECUTE 走向；MOD_TAG / NUM_CALCULATE 协同实现"层数累加 / 数值条件"。
- SkillTag → **伤害管线**：威力系数 + 额外伤害（伤害对子铁律）通过 SkillTag 传递。
- SkillTag ←→ **SkillEntry 系统**：Active 与 Passive 子树共享 SkillTag 状态。
- SkillTag 与 **Buff 系统并列**（不是包含）：两套状态系统，按用途选择。

---

## 仍不确定的地方

1. ~~**3 个声明源的优先级 / 冗余 / 协作机制**~~（B-002 D-207 部分回答）：30534004 真证据显示**3 源协作非互斥**——顶层是槽位声明，flow 内是初始化值，可以同时声明同 tag。仍待源码进一步确认源 2/3 顶层声明缺失时是否触发运行时报错（即顶层是否真的是"必须显式分配槽位"）。
2. **lint E019 修复方案**：检 3 源后，是否还有"声明在 SkillTagsConfig.xlsx 全局表"的第 4 源？（待 B-002 验证 30325002 tag 301/1001 是否在 xlsx 表里）
3. **跨技能 SkillTag 30325002 tag 301 / 1001 的真实来源**（v0.5 拆分 / 2026-05-12 / Mode B 30312003 入库）：
   - **tag 1001 ✓ 已闭环**：系统内置 Tag（见 §A.补）/ 由引擎运行时或全局 `SkillTagsConfig.xlsx` 预定义 / lint E019 应豁免 / SkillTagsConfig.xlsx 仍待对账加固 Tag 全集 Desc/Type 元数据
   - **tag 301 ⏳ 仍 candidate**：需读 `{{SKILL_EXCEL_DIR}}/SkillTagsConfig.xlsx` 对账确认归属——可能是系统内置（同 1001）/ 也可能是真 cross-skill 读到其他技能私有 Tag（PostMortem #017 范式）/ 待 B-054+ Excel 加固后定论

4. **§F 心法注入合并语义反例边界**（v0.6 / 2026-05-13 新增）：
   - **多心法都塞同 tag**（两个心法都通过 `SkillTipsConditionSkillTagsList` 塞同一 tag）→ 是累加还是后写覆盖前写？
   - **同心法多等级同 tag**（心法 1 级塞 500、心法 5 级塞 1500）→ 升级是替换还是叠加？
   - **心法塞入 + 功法运行时 MODIFY_SKILL_TAG_VALUE**（运行时 mod 操作发生在心法注入"之前"还是"之后"）→ 时序问题
   - **顶层 SkillDamageTagsList 是否同样参与累加底盘**（§F 只验证了 SkillTagsList 即源 2，源 3 SkillDamageTagsList 待 grep 验证）
   - 待 B-054+ 源码 grep 心法注入合并函数 + 多心法样本扫描定论

---

## 认知演变（错→对的轨迹）

- **v0.2（2026-05-09）首次确立**：B-001 前心智模型只知道 SkillTagsConfigNode 一个声明源（lint E019 也只检这个）。30124001 / 30431000 / 30531005 三样本反复出现"看似未声明但 SkillConfig 顶层已声明"，3 次重复 = 模式信号，确认 3 个源（[batch_buffer/B-001.yaml D-3 evidence](batch_buffer/B-001.yaml)）。
- **PostMortem #017 / #018 / #019 关联**：本子系统页吸收以上 3 条踩坑教训为不变量 B / C / D，使其从"分散错题"变成"成体系不变量"。
- **v0.2 → v0.3（2026-05-09）反直觉 4 新增 + 仍不确定 1 部分回答**：B-002 D-207 通过 30534004 真证据（tag 2200140 顶层 + flow 内同时声明）回答 v0.2 §仍不确定 1 的"3 源关系"——确认是协作并集而非互斥覆盖。新增反直觉 4 强调"声明判定必须 OR 三源"。出处：B-002 D-207（[B-002.yaml F-8](batch_buffer/B-002.yaml)）。
- **v0.3 → v0.4（2026-05-09）§A 末尾补"最少 1 源"观察**：B-003 D-309 通过 30531008（顶层两 List 全空 + 8 SkillTagsConfigNode 全 flow 内）vs 30534004（B-002 已知，顶层 + flow 内并行）形成对照——3 源是"协作并集"而非"互斥"或"必须三全"，最少可仅 1 源。补充观察让 §A 三源关系认知收敛。**confidence 中 → 中**（curator 推中偏高，按用户决定保持中——仍无标准枚举可参照）。出处：B-003 D-309（[B-003.yaml D-309](batch_buffer/B-003.yaml)）。

- **v0.4 → v0.5（2026-05-12）Mode B 30312003 审核回流入库 / 两 delta 全接受**：来源 = skill-reviewer 任务 GATE-MENTAL-OUT 触发的 curator Mode B 回流（[batch_buffer/B-053_modeB_followup_30312003.yaml](batch_buffer/B-053_modeB_followup_30312003.yaml)）/ 用户 2026-05-12 全接受拍板。
  - **D-MB-3120031 概念补盲（非反转）**：新增 §A.补「系统内置 Tag 豁免」第 4 类声明源（小 ID 如 1001 由引擎 / `SkillTagsConfig.xlsx` 全局预定义，无需蓝图侧声明） / §反直觉点 1 加 v0.5 注脚（30325002 tag 1001 闭环为系统内置，不再视为真 cross-skill positive）/ §仍不确定 §3 拆分（tag 1001 闭环 + tag 301 仍 candidate 待 Excel 对账）。证据 = 用户 2026-05-12 口头裁决（等级 1）+ 30312003 fs 真扫 TagID=1001 出现 3 次 + 顶层与 flow 内 SkillTagsConfigNode 均未声明 1001 + 技能正常运行（等级 2）。**rule_2 严守**：v0.2 §反直觉点 1 / §仍不确定 §3 主张本体保留 / 仅加注脚。
  - **D-MB-3120032 新增 candidate**：新增 §E 跨技能 Tag 耦合模式（木宗门叶雨 30312003 ↔ 三重碧叶 30212011 ADD/GET/CHECK 三角）/ §B 末尾加 v0.5 cross-ref 注脚（§B 主张本体不变）。**candidate 严守不升正式**，待 ≥3 宗门 / ≥5 样本累积。证据 = 用户 2026-05-12 设计意图裁决（等级 1）+ 30312003 fs 真扫双向 ADD+GET +TSCT_HAS_BUFF 范式（等级 2）。
  - **confidence 维持 中**（系统内置 Tag 全集仍待 B-054+ Excel 加固 / §E 仅 1 例尚未升 candidate）。

- **v0.7 → v0.6.1+ patch（2026-05-14 / AI 自决细化 / 非概念反转 / 新增 §F.1 双键映射静默失效铁律）**：来源 = 用户让 AI 阅读 `E:\wb\封神工作文档\AAAA本地设计工作文档\2025年9月三测相关\技能表格配置工具\心法强化功法的配置.md` §4.2 后判定 mental_model 已覆盖 §F 三态主体但缺"双键映射不一致"工程实现铁律 / 用户原话"立刻补"。
  - **新增 §F.1**：Inspector 用数字 tag ID / SkillValueConfig-XinFa 用 tag 中文名（= SkillTagsConfig.ConfigJson.Desc） / 两端逐字符一致 / 差一字符整链路静默失效不报错
  - **与 memory `reference_skilltag_desc_unique.md` 因果回填**：该 memory 立法的 Desc 全工程唯一 + ≤15 字 + 风格 `<技能名><变量名>` 的工程根源 = §F.1 双键映射风险 / 320957 改名「叶散风行-寻踪术装备态」（2026-05-14）作业务实例锚定
  - **AI 自决升正式 4-gate 满足**：(a) 用户提供 md §4.2 明文 + 业务实例 / (b) 阈值 = 等级 1 证据足够 / (c) 0 反预测 / (d) §F 主张本体不变 / 非升 rule 编号 / 非命名空间细化 / 落盘到 §F 之后新增 §F.1 / 非修订正式 rule 段
  - **rule_2 严守**：§F v0.6 三态主张本体保留 / 本批仅补 §F.1 工程实现细节维度

- **v0.6 → v0.7（2026-05-13 / Mode C 一致性巡检 / memory 升级批 v0.16.41）**：来源 = 用户授权 Step 1 memory 升级，4 个 memory 同主题应聚合到 SkillTag系统.md：
  - `memory/feedback_skilltag_desc_unique.md` → 新增 §H.前 §命名规范铁律（Desc 全工程唯一 + 两层描述模式）
  - `memory/reference_skilltag_builtin_ids.md` → 新增 §H.前补 §SkillTag ID 等级速查铁律（小 ID 内置 vs 大 ID 自定义 / 与 §G 二元组互补）
  - `memory/feedback_skilltag_scope_p1_meaning.md` + `memory/feedback_get_skill_tag_value_p1_scope.md` → 新增 §B.补 GET/ADD/MODIFY P[1] 速查表（2 模式 + 金标 30212010 32002231）
  - **rule_2 严守**：§A~§G 主张本体不变 / 新增 §H.前 + §H.前补 + §B.补 互补维度 / 不撤回任何原主张 / memory 原文保留 + 加首行升级注脚

- **v0.5 → v0.6（2026-05-13）用户口头裁决直接入库 / 新增 §F 升正式不变量**：来源 = 用户在配 `心法强化功法的配置.xlsx` 文档时主动 dump 三规则 + 给出具体数字示例（1000 / 300 / 500 → 500 / 800 / 1000）。
  - **新增 §F 心法注入参数合并语义（升正式）**：心法注入合并算法 = 三态（情形 A 直接写入 / 情形 B 累加 / 情形 C 兜底初始值）/ 心法注入只与顶层 SkillTagsList 交互 / 与 flow 内 SkillTagsConfigNode 初始值正交。
  - **修订业务通行表述误差**：`心法强化功法的配置.md` v0 表述 "覆盖原 tag 默认值" 精化为"累加 / 写入 / fallback 三态" / md 文档同步修订（[E:\wb\封神工作文档\AAAA本地设计工作文档\2025年9月三测相关\技能表格配置工具\心法强化功法的配置.md](file:///E:/wb/封神工作文档/AAAA本地设计工作文档/2025年9月三测相关/技能表格配置工具/心法强化功法的配置.md)）/ Excel 文档待用户关闭后同步。
  - **走 fast-path 真硬停 #5 边界判定**：非概念反转（§A/§B/§C/§D/§E 主张本体不变）/ 非命名空间细化 / 非 rule 编号修订 / 是新的运行时合并视角不变量主张本体 → AI 自决升正式 4-gate 全通过（用户口头裁决 = 等级 1 / 三规则齐全 + 数字示例 + 无反预测 + 与历史不变量正交不冲突）。
  - **rule_2 严守**：v0.2 ~ v0.5 所有主张本体保留 / §A 三声明源不变 / §F 与 §A 正交补强而非替换。
  - **confidence 中 → 中**（升正式不变量但仍待 B-054+ 源码 grep 验证心法注入合并函数 + 多心法多等级同 tag 反例边界探查）。

---

## 引用样本与源码

**真实样本**：
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30431000_*.json` — SkillDamageTagsList 顶层声明
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30124001_*.json` — 1 号子弹伤害对子真样本
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30325002_*.json` — 真跨技能读 tag 301 / 1001
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30531005_*.json` — SkillDamageTagsList tag 3
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30234006_*.json` — flow 内 5 SkillTagsConfigNode
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/SkillGraph_30534004_*.json` — 3 源协作真证据（tag 2200140 顶层 + flow 内同时声明 / tag 2200133 + 2200158 仅 flow 内）
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/木宗门技能/SkillGraph_30312003【木宗门】神通_人阶_叶雨.json` — v0.5 Mode B 入库 / §A.补 系统内置 Tag (1001) + §E 跨技能 Tag 耦合 (↔ 30212011 三重碧叶 / TagID=320100 + BuffID=320037) 双实证
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/木宗门技能/SkillGraph_30212004【木宗门】奇术_人阶_灵木轰击.json` — v0.6 §F 心法注入消费方典型样本 / TagID=320058 灵木轰击蓄能点数
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/宗门心法/SkillGraph_30512003【木宗门】密卷-人阶30212004.json` — v0.6 §F 心法注入声明方典型样本 / 首节点 Inspector「心法专属-给满足条件的其他技能里塞参数列表」

**源码**：
- `Assets/Scripts/CSGameShare/Hotfix/CSCommon/common.nothotfix.cs` — SkillTag / TCommonParamType 枚举
- `Assets/Scripts/HotFix/Game/Battle/` — SkillTag 运行时实现

**Excel 表**（B-002 待对账）：
- `{{SKILL_EXCEL_DIR}}/SkillTagsConfig.xlsx` — SkillTag 全局定义
- `{{SKILL_EXCEL_DIR}}/SkillValueConfig.xlsx` `SkillValueConfig-XinFa` 页签 — §F 心法注入数值源 / `SkillTipsConditionSkillTagsList` 字段 = `tag名,值`
- `{{SKILL_EXCEL_DIR}}/SkillXinfaConfig.xlsx` — §F 心法↔功法关联表 / `ConditionSkills[0]=条件ID\|心法ID\|心法等级`
- `{{SKILL_EXCEL_DIR}}/SkillPreConditionConfig.xlsx` — §F 心法触发条件 ID 定义

**关联文档**：
- [postmortem/2026-05-08-017-skill-tag-cross-skill.md](../postmortem/2026-05-08-017-skill-tag-cross-skill.md) — 跨技能 SkillTag 必须显式声明
- [postmortem/2026-05-08-018-int32-overflow.md](../postmortem/2026-05-08-018-int32-overflow.md) — int32 溢出
- [postmortem/2026-05-08-019-entity-level-tag.md](../postmortem/2026-05-08-019-entity-level-tag.md) — 实体级 tag 写法
- [memory/reference_bullet_damage_tag_pairs.md](../../../memory/reference_bullet_damage_tag_pairs.md) — 伤害对子铁律（§D 主表）
- [memory/feedback_skilltag_desc_unique.md](../../../memory/feedback_skilltag_desc_unique.md) — Desc 全工程唯一（§H.前 / v0.7 入库）
- [memory/reference_skilltag_builtin_ids.md](../../../memory/reference_skilltag_builtin_ids.md) — 内置 vs 自定义 ID（§H.前补 / v0.7 入库）
- [memory/feedback_skilltag_scope_p1_meaning.md](../../../memory/feedback_skilltag_scope_p1_meaning.md) — P[1] 2 模式（§B.补 / v0.7 入库）
- [memory/feedback_get_skill_tag_value_p1_scope.md](../../../memory/feedback_get_skill_tag_value_p1_scope.md) — GET P[1] 作用域（§B.补 / v0.7 入库）
- [子弹系统.md](子弹系统.md) — 子弹序号-威力 Tag 配对 ↔ §D 主表
- [伤害管线.md](伤害管线.md) — 整体伤害管线（含字典扩展）
- [Buff 系统.md](Buff系统.md) — 与 SkillTag 并列的状态系统
- [batch_buffer/B-001_actionable.md](batch_buffer/B-001_actionable.md) — 待 main 修 lint E019
