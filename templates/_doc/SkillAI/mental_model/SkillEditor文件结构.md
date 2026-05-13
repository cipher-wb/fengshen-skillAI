---
subsystem: SkillEditor JSON 文件结构
confidence: 中
last_review: 2026-05-13
related_postmortems: [033, 034, 037, 039（候选）]
related_samples:
  - SkillGraph_30312003【木宗门】神通_人阶_叶雨.json
  - SkillGraph_30212018.json # unique-parent 立法样本
  - SkillGraph_30212010.json # 金标 / outPort 端口模式 + RefConfigBaseNode 范式
mental_model_version: v0.2
---

## 一句话本质

SkillGraph_*.json 是 Unity SerializeReference 序列化产物，**节点 = 双数组写入**（内容仓库 + UI 目录），**edge = 单数组**。手写脚本破坏任一约束 → SkillEditor 加载时无声"丢节点 / 丢连线"，但参数列表里可能还能查到数值（误导排查方向）。

---

## 关键不变量（违反就 100% 出问题）

### A. 节点双数组写入铁律（PostMortem #037 / v0.1 / 2026-05-13 入库）

任何节点必须**同时**写入：

1. `data.references.RefIds[]` — 节点完整数据（SerializeReference 内容仓库）
2. `data.nodes[]`（顶层）— 仅 `{"rid": NNNN}` 形式的"目录索引"

**校验式**：`len(d['nodes']) == len(d['references']['RefIds'])`。

**违反特征**（症状↔根因映射）：
- "节点在蓝图工作区不可见" + "SkillTagsList 红色`错误TagID`但有数值" → 顶层 `nodes[]` 漏写
- "节点可见但无连线 / 父子关系丢失" → 通常是 edge 端口铁律（PostMortem #033/#034），不是本铁律

**为何 SkillTagsList 仍显示数值**：SkillTagsList 是 SkillConfigNode 内嵌字段，按 `SkillTagConfigID` 数字直接查，不经过节点目录；所以即使定义节点是"孤儿"，参数列表里仍能读到 Value——这是误导排查的关键陷阱。

**证据**：
- 等级 1（用户实测）：2026-05-13 配 SkillGraph_30312003 叶雨，v2 脚本只写 `references.RefIds[]`，SkillEditor 表现为 SkillTagsList 显示"错误TagID"但有值 320292/90、320287/30，蓝图工作区看不到新节点
- 等级 2（修复验证）：v3 同步写双数组（refs=66 / edges=61 / nodes_top=66）后，SkillEditor 加载正常，节点可见 / Tag 定义被识别 / 参数列表绿字

### B. 顶层 `nodes[]` 仅存索引、`references.RefIds[]` 存内容（结构原理）

```json
{
  "nodes": [{"rid": 1000}, {"rid": 1001}, ...],   // 仅索引
  "edges": [...],
  "references": {
    "version": 2,
    "RefIds": [
      {"rid": 1000, "type": {"class": "..."}, "data": {...}},  // 完整内容
      ...
    ]
  }
}
```

SkillEditor 加载流程：先遍历 `nodes[]` 拿 rid 作为渲染目录 → 再用 rid 去 `references.RefIds[]` 查 data 反序列化。`nodes[]` 不存在的 rid → 编辑器视为孤儿，**不渲染、不参与 edge 端解析**。

### C. `edges[]` 是顶层单数组（不双写）

edge 只在顶层 `data.edges[]` 出现一份，**不**对称镜像到任何子数组。与 nodes 双写规则相反，这一点必须区分清楚（否则会写出"重复 edge / 编辑器警告"）。

### D. unique-parent 强约束（v0.2 / 2026-05-13 memory 升级入库 / PostMortem #033）

> 来源：[memory/feedback_skilleditor_unique_parent.md](../../../memory/feedback_skilleditor_unique_parent.md) / 2026-05-12 配 30212018 立法。

**铁律 1：每个节点最多 1 个父引用（unique parent）** — 适用所有类型节点：

- **控制流节点**：ORDER / REPEAT / CONDITION / SWITCH 子项
- **数据流节点**：NUM_CALC / GET_ENTITY_ATTR / cos / sin
- **写操作节点**：MODIFY / ADD / CHANGE_POS

**违反时的现象（症状↔根因映射）**：

| 现象 | 含义 |
|------|------|
| Console: "连线数据丢失，参数N" | SkillEditor lint 报错 |
| 视觉：Params 有该项但看不到连线 | SkillEditor 自动隐藏多余 edges |
| 数据：JSON edges 内 edge 还在 | 但 SkillEditor 不渲染（**误导排查方向**） |

**铁律 2：edge 方向语义**：

| 视觉端口 | 对应 edge 字段 |
|---------|---------------|
| 左侧 "ID" port（被引用） | `outputNodeGUID` (destination) |
| 右侧 "技能效果ID" port（调用方） | `inputNodeGUID` (source) |

- `inputNodeGUID = 子`节点（提供 output）
- `outputNodeGUID = 父`节点（接受 input）
- 视觉箭头：子.右 → 父.左
- 每个子的"左 ID port"只能 1 条 incoming → **unique parent**

**铁律 3：`outputPortIdentifier` 两种模式 ⚠️ 易错**：

#### 模式 a：固定端口（按 Params 索引）— 大多数节点

- `NUM_CALC / CHANGE_POSITION / MODIFY_ENTITY_ATTR / CREATE_BULLET / DELAY / SWITCH` 等
- `outputPortIdentifier` = **Params 索引数字字符串**（`"0"`, `"1"`, `"2"`...）
- 含义：edge 指向父节点 Params[N] 这一项
- 例：`dynamic_visual_angle → CREATE_BULLET P[1]` outPort=`"1"`

#### 模式 b：动态端口（所有 input edges 都用 '0'）⚠️ 易踩

- **`ORDER_EXECUTE / AND / OR / SELECT_EXECUTE / NUM_MAX / NUM_MIN`** 等"多子项聚合"型节点
- 所有 input edges 的 `outputPortIdentifier` **全部用 `"0"`**（不论 Params 多少项）
- 用 `'1'` / `'2'` → SkillEditor 不识别 → **自动删 edge + 同步清掉 Params 对应项**
- 例（30212010 320357 AND）：
  - edge1: 320358 → 320357  outPort=`"0"`
  - edge2: 320359 → 320357  outPort=`"0"`
  - **两条都 '0' / 不是 '0' 和 '1'**

**判断规则**：节点 Params 可变长（随用户增减）→ dynamic port → 全用 `"0"`。

> ⚠️ **30122001 真实样本印证**（[memory feedback_skill_compiler_pitfalls.md §1](../../../memory/feedback_skill_compiler_pitfalls.md)）：ORDER_EXECUTE 32000163 两条出边都是 `"0"`，但 `ConfigJson.Params=[32000162, 32000164]` 顺序正确——**Params 数组才是真相，edges 只是视觉**。

**铁律 4：成员型 edge `outputFieldName='PackedMembersOutput'` 用字段路径字符串**：

`BulletConfig / SkillConfig / ModelConfig / BuffConfig` 等"配置容器"节点的字段引用：

| outputPortIdentifier 值 | 字段含义 |
|------------------------|---------|
| `"Model"` | BulletConfig.Model |
| `"AfterBornSkillEffectExecuteInfo.SkillEffectConfigID"` | BulletConfig.AfterBorn |
| `"BeforeBornSkillEffectExecuteInfo.SkillEffectConfigID"` | BulletConfig.BeforeBorn |
| `"DieSkillEffectExecuteInfo.SkillEffectConfigID"` | BulletConfig.Die |
| `"SkillEffectExecuteInfo.SkillEffectConfigID"` | SkillConfig.SkillEffectExecuteInfo |

⚠️ 用 `"0"` 而不是字段路径 → SkillEditor 不识别 → 自动删 edge → 视觉没线 → 子弹/技能配置不生效。

**金标样本**：`SkillGraph_30212010` 320359 等多个 outPort 范式（详见 [memory/feedback_value_compare_schema.md](../../../memory/feedback_value_compare_schema.md) §30212010 参考样本）。

### E. 跨表引用必须用 RefConfigBaseNode 包装（v0.2 / 2026-05-13 memory 升级入库 / PostMortem #039 候选）

> 来源：[memory/feedback_create_bullet_refconfig.md](../../../memory/feedback_create_bullet_refconfig.md) + [memory/feedback_skilleditor_refnode_over_id.md](../../../memory/feedback_skilleditor_refnode_over_id.md) / 2026-05-12 配 30212018 时遇到 / PostMortem #039（待落盘）。

**铁律**：凡是可以连线引用的配置参数（`BulletConfig / BuffConfig / ModelConfig / SkillConfig` 等 `isConfigId=true` 或 `RefTypeName≠空`），**必须**通过 `RefConfigBaseNode` + edge 连线引用，**不允许**只填 PT=0 数字常量。

**反例 vs 正例对比**：

```
错（只填 PT=0 常量）:
  CREATE_BULLET.P[0] = {V=320262, PT=0}
  → SkillEditor 视觉上不显示连线
  → 策划看到一串数字，不知道去哪查 BulletConfig

对（加 RefConfigBaseNode + edge）:
  + RefConfigBaseNode(ManualID=320262, TableManagerName='TableDR.BulletConfigManager')
  + edge: Ref(320262).GUID → CREATE_BULLET.GUID, P[0], outPort='0'
  + ConfigJson Param 改为 ParamType=2（NodeRef / 函数返回值）, Value 指向 RefConfigBaseNode 节点 ID
  → 视觉上能看到 Ref 节点连到 CREATE_BULLET
  → 策划可以在 SkillEditor 直接跳转查阅
```

**30212010 金标范式**：

```
RefConfigBaseNode {
  ID=320110, ManualID=320110,
  TableManagerName='TableDR.BulletConfigManager'
} → CREATE_BULLET 32002235 P[0]  field='PackedParamsOutput' outPort='0'
```

**适用场景**：
- CREATE_BULLET P[0] 引 BulletConfig
- ADD_BUFF P[?] 引 BuffConfig
- BulletConfig.Model 跨表引 ModelConfig（用 `TableDR.ModelConfigManager` + member edge）
- TemplateParam `isConfigId=true` 的所有项

**非配置引用例外**：纯数值参数（扇角度数 / 间隔 N / 距离）用字面量 PT=0 即可，不需要 RefConfigBaseNode。

### F. 跨蓝图引用 condition/buff 节点同样不允许（v0.2 加入）

> 来源：[memory/feedback_skilleditor_unique_parent.md §3c](../../../memory/feedback_skilleditor_unique_parent.md)。

SkillCondition (TSCT_*) 节点跨蓝图引用 → SkillEditor 把 Params 清空：

```
错: 当前蓝图 TSCT_AND.P[0] = {V=外部蓝图的 TSCT_HAS_BUFF ID, PT=0}
  → SkillEditor 把 Params 清空
  → AND 退化为"空判断"默认 true
  → 逻辑全错（buff 检查永远 pass）
```

**解法**：把 TSCT_* 节点也**复制**到本蓝图（连同它引用的下游 condition 链）。

### G. 复制节点时必须重扫 edges 补 PT=2 NodeRef（v0.2 / 2026-05-12 实测重灾区）

> 来源：[memory/feedback_skilleditor_unique_parent.md §Sensor D](../../../memory/feedback_skilleditor_unique_parent.md)。

复制节点时只 reallocate Params 内 ID 而没补 PT=2 NodeRef 对应的 edges 是常见漏洞：

- `PT=2 NodeRef` → 必须有 edge：`inputNodeGUID=NodeRef target, outputNodeGUID=当前节点, outputPortIdentifier=Params 索引`
- 缺 edge 时 lint 不一定报错（lint pass），但**运行时 NodeRef 解析为 0** → 计算公式 `cos × r / 10000 + caster.X` 算出 `0 × r / 10000 + 0 = 0` → CHANGE_POSITION 把子弹挪到 `(0,0,0)` → **8 颗子弹都叠在原点**

**复制后自查模式**：

```python
for i, p in enumerate(node.Params):
    if p.ParamType == 2:  # NodeRef
        add_edge(p.Value, node.ID, outPort=str(i))
```

---

## 反直觉点（容易踩的）

1. **"SkillTagsList 显示值 ≠ Tag 节点存在"** — 参数列表有 Value 仍可能是孤儿 Tag。审核时必须**同时**核对蓝图工作区里能否看到 SkillTagsConfigNode 实体节点。
2. **"refs 数量对了就行" ✗** — 必须 `refs == nodes_top`，仅前者对齐不够。
3. **rid 与 GUID 解耦** — 顶层 `nodes[]` 用 rid 索引、`edges[]` 用 GUID 连接、`references.RefIds[]` 既有 rid 也有 GUID。修脚本时不要混用键。
4. **TableTash 是节点级元数据** — 不空填 `""` 会让 SkillEditor 走"migration path"去查 Excel 表（详见 [Assets/Thirds/NodeEditor/CLAUDE.md](../../../Assets/Thirds/NodeEditor/CLAUDE.md)），查不到则节点丢失。所有节点 TableTash 必须与其 cls 配对的 hash 一致（如 SkillTagsConfigNode → `6A8A6883BDFDA1411BB2461E65CB2D9B`，SkillEffectConfig → `0CFA05568A66FEA1DF3BA6FE40DB7080`）。

---

## 推荐操作模板（手写脚本加节点）

```python
def add_node(rid, cls, tash, guid, order, pos, extra):
    node = {
        "rid": rid,
        "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {"GUID": guid, "computeOrder": order, ..., "TableTash": tash, **extra}
    }
    refs.append(node)                        # 1. references.RefIds[]
    data['nodes'].append({"rid": rid})       # 2. 顶层 nodes[]（关键修复）
    return node

# 校验
assert len(data['nodes']) == len(data['references']['RefIds']), 'node-ref 双数组不一致'
```

---

## 与其他子系统的因果关系

- 本结构 → **所有子系统**：任何子系统的节点都要遵守双数组铁律。SkillTag 系统的"Tag 定义节点不可见"症状（PostMortem #037）就是双数组失败的典型表现。
- 本结构 → **edge 端口铁律**（PostMortem #033/#034）：edge 端口写错 ≠ 节点丢失。两类问题排查路径不同：
  - 节点不可见 → 查双数组
  - 节点可见但连不通 → 查 edge `inputPortIdentifier` / `outputPortIdentifier` / `outputFieldName`
- 本结构 → **Excel 转表**：TableTash 错填 → 走 migration → 查 Excel → 节点丢失。同源问题，但触发链不同。

---

## 仍不确定的地方

1. **`groups[].innerNodeGUIDs[]` 是否也必须同步**：当节点位置落在某个 group 矩形内时，是否需要把 GUID 加进对应 group 的 `innerNodeGUIDs`？2026-05-13 实测：新节点位置在所有 group 外（x>=900），没加 group 也正常显示。group 内场景待后续样本验证。
2. **`pinnedElements` / `serializedParameterList` / `exposedParameters`**：这几个顶层数组在我们的样本里都是空，是否对新增节点有影响待源码验证。
3. **rid 分配是否必须连续 / 单调递增**：当前所有脚本都是 `max(rid)+1`，未验证跳号是否合法。

---

## 认知演变（错→对的轨迹 / rule_2 永不 silent delete）

- **v0.1（2026-05-13）首次确立**：触发自 SkillGraph_30312003 叶雨配置任务。AI v2 脚本只写 `references.RefIds[]`，用户在 SkillEditor 里看到"SkillTagsList 显示值但是红色错误TagID + 蓝图节点不可见"。AI 多次猜测 TableTash / DESTROY_ENTITY 参数错填等次要原因，用户提出"备份你的版本，让我手动修一遍后 diff"，diff 后立刻定位到顶层 `nodes[]` 长度 54 vs 用户版本 56 → 双数组铁律确立。v3 脚本修复后一次通过。

- **v0.1 → v0.2（2026-05-13 / Mode C 一致性巡检 / memory 升级批 v0.16.41）**：来源 = 用户授权 Step 1 memory 升级。

  - **新增 §D unique-parent 强约束**（来源 [memory/feedback_skilleditor_unique_parent.md](../../../memory/feedback_skilleditor_unique_parent.md) / PostMortem #033 + #034 / 2026-05-12 30212018 立法）：
    - 4 条铁律：unique parent / edge 方向语义 / outPort 两种模式 / 成员型 edge 字段路径
    - 金标 30212010 320359 范式

  - **新增 §E 跨表引用 RefConfigBaseNode 包装**（来源 [memory/feedback_create_bullet_refconfig.md](../../../memory/feedback_create_bullet_refconfig.md) + [memory/feedback_skilleditor_refnode_over_id.md](../../../memory/feedback_skilleditor_refnode_over_id.md) / PostMortem #039 候选）：
    - CREATE_BULLET / BulletConfig.Model 等跨表引用必须包 RefConfigBaseNode
    - 反例 vs 正例对比表

  - **新增 §F 跨蓝图引用 condition/buff 节点禁忌**（来源 memory feedback_skilleditor_unique_parent.md §3c）

  - **新增 §G 复制节点重扫 PT=2 NodeRef edges**（来源 memory feedback_skilleditor_unique_parent.md §Sensor D / 2026-05-12 实测重灾区）

  - **rule_2 严守**：v0.1 §A/§B/§C 主张本体不变 / 新增 §D~§G 互补维度 / 不撤回任何原主张

---

## 引用样本与源码

**真实样本**：
- `{{SKILLGRAPH_JSONS_ROOT}}宗门技能/木宗门技能/SkillGraph_30312003【木宗门】神通_人阶_叶雨.json` — v0.1 立法样本

**源码**：
- `Assets/Thirds/NodeEditor/Nodes/Base/ConfigBaseNode.Core.cs` — TableTash 反序列化路径
- `Assets/Thirds/NodeEditor/CLAUDE.md` — TableTash hash 字典 + 节点 schema 概览

**关联文档**：
- [postmortem/2026-05-13-037-skilleditor-json-dual-array.md](../postmortem/2026-05-13-037-skilleditor-json-dual-array.md) — 本铁律的 PostMortem 原始记录
- [postmortem/2026-05-12-033-skilleditor-unique-parent-rule.md](../postmortem/2026-05-12-033-skilleditor-unique-parent-rule.md) — edge 端口铁律（与本结构互补 / §D）
- [postmortem/2026-05-12-034-dynamic-vs-fixed-port-skilleditor.md](../postmortem/2026-05-12-034-dynamic-vs-fixed-port-skilleditor.md) — 动态 vs 固定端口（§D outPort 模式）
- [postmortem/2026-05-13-039-create-bullet-refconfig.md](../postmortem/2026-05-13-039-create-bullet-refconfig.md) — RefConfigBaseNode 包装（§E / 待落盘）
- [memory/feedback_skilleditor_dual_array.md](../../../memory/feedback_skilleditor_dual_array.md) — 私人 memory 速查（§A）
- [memory/feedback_skilleditor_unique_parent.md](../../../memory/feedback_skilleditor_unique_parent.md) — 私人 memory 速查（§D + §F + §G）
- [memory/feedback_create_bullet_refconfig.md](../../../memory/feedback_create_bullet_refconfig.md) — 私人 memory 速查（§E）
- [memory/feedback_skilleditor_refnode_over_id.md](../../../memory/feedback_skilleditor_refnode_over_id.md) — 私人 memory 速查（§E 通用规则）
