---
type: 复盘页
summary: 主对话给 sub-agent 的接力 prompt 中含未验证的事实性断言，sub-agent 必须在 GATE-0.5 fs 真扫独立验证而非直接采信
date: 2026-05-13
tags: [PostMortem, 接力消息, sub-agent, GATE-0.5, 工作守则]
---

# PostMortem #038 — 接力消息不可全信（事实性断言必须 fs 真扫独立验证）

## 新规则

**主对话给 sub-agent 的 prompt 中含「X 模板被 A 和 B 共用」/ 「ID 是 N」/ 「调用方有 M 个」等事实性断言时，sub-agent 必须在 GATE-0.5 fs 真扫阶段独立验证，不直接采信。**

校验式：sub-agent 报告中遇到与 prompt 断言冲突的真扫结果 → 立即报回主对话纠正，不沿用错误前提推导后续结论。

## 现象

2026-05-13 子弹伤害管线 7 模板深度 review 任务，主对话先后给 sub-agent 的 prompt 中含**两处错误断言**：

### 错误断言 #1：`146004907 真实和非真实共用`

- **来源**：上轮 175000212 review agent 推断（fs 真扫不充分）→ 主对话采信后写入下轮 146004907 review prompt
- **真相**：sub-agent GATE-0.5 fs 真扫推翻 — corpus grep 146004907 仅 `146004930（非真实）` 调用 + `175000212` 注释引用 / **`146004986（真实）` 不调 146004907**，走独立公式仅复用 L4 66001191 算额外伤害

### 错误断言 #2：`闪避输出 SkillTag146004858`

- **来源**：上轮 146004930 review agent 报告时口误（实际 sticky note 写的是 146004858 但应是 1460112）→ 主对话沿用错误 ID 写入下轮 prompt
- **真相**：sub-agent GATE-0.5 fs 真扫推翻 — 闪避模板 146004836 内 SkillTagsConfigNode rid=1011 ID=`1460112` / corpus grep `146004858` = 0 闪避语义命中

**两处错误均在 sub-agent 的 fs 真扫独立验证阶段被纠正**，验证机制有效。但若 sub-agent 直接采信错误断言，会导致：
- 整批 review 结论偏离事实
- mental_model delta 提案含错误数据
- 跨批字典不一致（如 B-060 D-6006 字典含 D-6113 推翻的 ID 146004858）

## 根因

主对话作为 review 接力链的协调者，会将每轮 sub-agent 的报告**作为下轮 prompt 的上下文事实**注入。但：

1. **sub-agent 报告本身可能含误差**（推断/口误/部分 fs 真扫覆盖不全）
2. **主对话不重复 fs 真扫验证**（信任 sub-agent 报告）
3. **错误一旦写入下轮 prompt 即固化为"事实"**，下轮 sub-agent 若不独立验证则错误传播 + 放大
4. **跨批回流时错误进入 curator delta 提案**（如 D-6006 含错误 ID）→ 字典不一致

同源教训：
- **PostMortem #026** "RepeatExecute 接力消息节点角色不可全信"：红队 sub-agent 拒绝盲从主流程"REPEAT 报错就改 count=-1"接力指令救场（实为 spawn 节点必须 count=N，改 -1 会无限刷子弹）

本 PostMortem 是 #026 在**信息层**的同源教训（#026 在**指令层**）。

## 修复

### 修复 #1：sub-agent prompt 工作守则修订

主对话 prompt sub-agent 时，对**任何事实性断言**（ID / 模板 ID / 节点数 / 调用次数 / "被谁调用" / 字典枚举值 / 等）**加显式标注**：

```
⚠️ 以下断言来自上轮 sub-agent 报告 / 你必须在 GATE-0.5 fs 真扫独立验证:
- "146004907 被真实和非真实两条分支共用"
- "闪避输出 SkillTag146004858"
```

并在 sub-agent 工作守则 §GATE-0.5 加项：

```
GATE-0.5 必查项 +1：
- 主对话 prompt 中标注 ⚠️ 的事实性断言 → 必须 fs 真扫独立验证
- 验证结果与断言冲突 → 立即报回主对话纠正 / 不沿用错误前提推导结论
```

### 修复 #2：curator Mode B 流程加 GATE-CONSISTENCY 子步骤

由 auditor 在合并审 B-059+B-060+B-061 时建议 / 用户 2026-05-13 拍板授权 / 与本 PostMortem 配套落地：

```
GATE-CONSISTENCY: cross-batch 字典/枚举/ID 一致性验证

触发条件:
  - delta 含 SkillTag ID 字典扩展
  - delta 含枚举值字典
  - delta 含 attr ID 清单
  - delta 含节点 ID / rid 清单

强制动作:
  1. grep 本 delta 所有 ID 在 corpus 内的语义引用次数（≥1 才合法）
  2. cross-check 同字典的历史升正式 / candidate / hedge 是否冲突
  3. 检查同批其他 delta 是否会推翻本 delta 的 ID
  4. 若 cross-batch 不一致 → R1 必修
```

落盘位置：`CLAUDE.local.md` § AI 自决升格规则 段（与 Gate (a)~(g) v3 并列）。

### 修复 #3：本 PostMortem 提取 D-6115 升 candidate

B-061 D-6115 "接力消息断言不可全信"原本是 candidate 评级，本 PostMortem 实证后建议 curator 在下次 review 时**升 candidate 升正式 4-gate 评估**：
- (a) auditor + curator 共识推荐 ✅
- (b) 阈值数据：#026 + 本 #038 + B-060 D-6006 字典错误 = 3 个独立事件 ✅
- (c) 0 反预测 ✅
- (d) 不触发概念反转 ✅

满足 4-gate / 可走 AI 自决升正式（待下次 curator 评估）。

## 建议沉淀位置

- ✅ **PostMortem** 本文件
- ✅ **mental_model delta**：B-061 D-6115 + 配套 GATE-CONSISTENCY 立法
- ✅ **CLAUDE.local.md 工作守则**：GATE-CONSISTENCY 段（curator 任务 #3 落盘）
- ⚠️ **代码护栏候选**：`doc/SkillAI/tools/lint_delta_consistency.py`（cross-batch 字典一致性 lint / 未来加）

## 利 / 弊 / 噪音风险

- **利**：彻底防止接力消息错误传播 / 配套 GATE-CONSISTENCY 防字典不一致 / sub-agent 独立验证机制再加固
- **弊**：sub-agent prompt 长度增加（要标注 ⚠️ + 显式列断言）/ GATE-0.5 必查项增加 1 条
- **噪音风险**：低 — 主对话每次 review 接力都会触发 / 频率高 / 但每次只多一行标注

## 决定项

✅ **入库 3 处**：PostMortem + mental_model delta + CLAUDE.local.md 工作守则。代码护栏待后续 lint 工具更新。

## 关联

- **同源 PostMortem #026** "RepeatExecute 接力消息节点角色不可全信"（指令层 / 本是信息层）
- **Auditor verdict 文件**：`doc/SkillAI/mental_model/batch_buffer/B-059_B-060_B-061_auditor_verdict_r0_INDEPENDENT_combined.md` §元发现 段含相同观察
- **触发实例**：
  - 错误 #1 = 146004907 共用断言被 fs 真扫推翻
  - 错误 #2 = 146004858 闪避 ID 被 fs 真扫推翻
  - 衍生 = B-060 D-6006 字典含错误 ID → R1 修订
