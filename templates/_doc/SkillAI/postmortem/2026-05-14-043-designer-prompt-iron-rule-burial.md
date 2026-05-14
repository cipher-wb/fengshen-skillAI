---
type: PostMortem
date: 2026-05-14
tags: [skill-designer, prompt 工程, memory 铁律埋藏, agent 救场, edge 方向]
summary: 主对话写 designer prompt 时把铁律埋深 / agent 选择跟随老惯例 / 同 prompt 内 edge 方向写反 / agent 严守现网+memory 反向救场
---

# #043 — Designer Prompt 铁律埋藏 + Agent Edge 方向反向救场

## 现象

### 翻车 1：铁律埋藏 → agent 选择跟随老惯例

主对话给 skill-designer 下任务 prompt（叶散风行加寻踪术条件附加伤害）时，把 [memory/feedback_skilleditor_refnode_over_id.md](C:/Users/.../memory/feedback_skilleditor_refnode_over_id.md) "isConfigId=true 引用必须 RefConfigBaseNode 连线 / 禁止纯 ID" 这条铁律埋在 "# 关键铁律（必须遵守 / 违反 = 翻车）" 第 9 条。

agent 完工后在"风险段"自己提到了：

> **未包 RefConfigBaseNode**：A3 SkillCondition `{V=320511,PT=0}` 直接填入 RST Params[10] 无视觉连线 / SkillCondition 320511 节点在 SkillEditor 里跳转可能需要手动右键 → 跳到该 ID。memory `feedback_skilleditor_refnode_over_id.md` 提示"应包 RefConfigBaseNode 方便跳转"，但叶散风行现有 RST 节点已有先例不包，**本次跟随现有惯例**。

策划查看产物后反馈："新增的节点都没有连线，只是通过数字关联，这样不便于策划阅读，我记得之前你沉淀过这个知识，怎么忘记了？"

**根因**：
1. **铁律埋深**：第 9 条 / 与"不要碰 BulletConfig"等次要约束并列 / 没有显式标红优先级
2. **agent 错判惯例权重**：老技能（吴波 301104 等）写法 = "废弃（老技能）"目录的样本 / 是 memory 立法前的产物 / 应该被新规范覆盖 / agent 选择"跟随老惯例"违反 memory 立法本意
3. **prompt 没显式说"老技能不算数"**：agent 没有判断标准区分"现网惯例" vs "废弃惯例"

### 翻车 2 → 救场：Edge 方向描述写反 / agent 严守 memory 反向执行

主对话续作 prompt（让 agent 补 RefConfigBaseNode 连线）时，描述 edge 方向：

> edge 规格：
> - `inputNodeGUID` = RST 节点 GUID
> - `outputNodeGUID` = RefConfigBaseNode GUID

这是错的。按 [memory/feedback_skilleditor_unique_parent.md](C:/Users/.../memory/feedback_skilleditor_unique_parent.md) 铁律 2：**inputNodeGUID = 子 / outputNodeGUID = 父**。RefConfigBaseNode 是数据源（子）/ RST 是消费方（父）→ 正确写法 `inputNodeGUID = RefConfig` / `outputNodeGUID = RST`。

agent 完工报告里指出（agent 救场）：

> 实测项目内 7 条现网 RefConfig→RST/CREATE_BULLET/ORDER 边 + 上一轮 2 条 A4-GET→RST Params[12] 边的**统一模式**：`inputNodeGUID = 数据源/子（RefConfig 或 GET）`，`outputNodeGUID = 消费方/父（RST 等）`。
>
> 与 memory `feedback_skilleditor_unique_parent.md`"inputNodeGUID=子/outputNodeGUID=父"铁律一致。
>
> 任务 prompt 文字描述把方向写反了 / 我按项目实际约定 + memory 铁律执行（语义正确性 > 任务文字方向描述）/ 写成 prompt 描述的反向会导致 SkillEditor 解析为 SkillCondition 试图把 ID 推回 GET 节点 / 不符合 RefConfigBaseNode 语义。

**这是 designer agent 的工程质量正面案例**：识别接力消息 prompt 与 memory + 现网样本冲突 / 选择 memory + 现网为准 / 而非盲从 prompt 文字。

## 影响

- 翻车 1：策划手动指出 / 需要 1 轮额外续作修复 / 信任损耗
- 翻车 2 救场：0 损失 / 反向勘误成功 / 但暴露主对话 prompt 工程质量问题

## 修复

### 主对话写 designer prompt 的强制清单（v1 立法）

1. **铁律优先级标红**：把 memory 引用按"如果不遵守必翻车"和"如果不遵守扣分"分级 / 翻车级铁律必须放在 prompt 最顶部 / 不允许埋在"# 关键铁律"列表第 9 条这种位置。
2. **显式声明"老惯例不算数"**：当工程内存在"废弃（老技能）"目录样本 / 或 memory 立法之前的产物时 / prompt 必须显式说"参考样本仅用于看节点结构 + 字段填法 / 涉及连线 / 引用形式 / 端口模式时以 memory 铁律为准 / 不跟随老样本"。
3. **edge 方向描述必须用语义而非 GUID 字段名**：写 "数据源连线到消费方" / "GET 输出 → RST 输入"（语义清晰）/ 不要写 "inputNodeGUID = RST" 这种容易写反的语法描述 / 让 agent 自己按 memory 铁律映射到正确字段。
4. **关键引用点要列穷举**：本次 prompt 应该列：
   - RST.Params[10] (SkillConditionConfig 引用) **必须 RefConfig 包装**
   - RST.Params[12] (PT=2 NodeRef) **必须 edge 连线**
   - TSCT.Params[0] (PT=2 NodeRef) **必须 edge 连线**
   - GET.Params[2] (SkillTag ID) 不需要包装（不是 isConfigId=true / 项目惯例 inline）
   
   穷举列表后 agent 不会漏。

### Designer agent 工作流改进（已部分体现 / curator 后续评估升级 candidate）

- **"接力消息 prompt 与 memory + 现网样本冲突时 / 永远以 memory + 现网为准"** — 本次 agent 自决修复 edge 方向 = 范式 / 该模式适合升 memory candidate。
- 提议落到 [skill-designer.md](.claude/agents/skill-designer.md) §角色边界 / 或新增 §冲突仲裁段。

## 思想史保留

- 主对话 prompt 原文（"# 关键铁律 第 9 条" 埋藏 + edge 方向描述写反）→ **保留作反面教材** / rule_2 严守 / 警示后续 prompt 工程质量。
- agent "选择跟随老惯例"的判断 → 保留作反面教材 / 警示 agent 不要把"现网样本"和"现网正确范式"混为一谈（废弃目录样本是反例不是范式）。
- agent edge 方向反向救场 → **保留作正面教材** / 同 PostMortem #038 "接力消息节点角色不可全信"范式 / 工作流升级提议依据。

## 关联沉淀

- mental_model 新增 [SkillCondition系统.md](../mental_model/SkillCondition系统.md) §D 配置铁律
- 关联 PostMortem [#042](2026-05-14-042-skillcondition-blueprint-misperception.md)（同任务的另一个翻车）
- 关联 memory [feedback_skilleditor_refnode_over_id.md](C:/Users/.../memory/feedback_skilleditor_refnode_over_id.md)（本次被埋深的铁律）+ [feedback_skilleditor_unique_parent.md](C:/Users/.../memory/feedback_skilleditor_unique_parent.md)（edge 方向铁律）
