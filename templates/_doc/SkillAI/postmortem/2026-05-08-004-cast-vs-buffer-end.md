---
proposal_id: 2026-05-08-004
status: accepted
sediment_target:
  - doc/SkillAI/docs/易错点速查.md §13（补加规则 #2）
  - doc/SkillAI/tools/skill_lint.py E013（补加规则 #2）
related_skill: 30142001 火焰追踪弹幕（v1.1.1 第二轮修正）
---

# 提案：技能时长规则漏报 — cast 必须 ≤ buffer_end

## 决策
✅ **入库**

## 新规则
SkillEditor 时长约束实际有 **4 条**（不是 3 条）：
1. cast ≤ base_duration
2. **cast ≤ buffer_start + buffer_frame**（即 cast 必须在缓冲区结束前）⚠️ 容易漏
3. buffer_start ≤ base_duration
4. base_duration ≤ cd_time

之前 PostMortem #003-C 沉淀的 E013 只有规则 1/3/4，**漏了规则 2**。

## 现象
30142001 第二轮配置 cast=24/bs=0/bf=20/bd=30/cd=90：
- 规则 1: 24 ≤ 30 ✓
- 规则 4: 30 ≤ 90 ✓
- 规则 2: 24 > buffer_end(20) ❌ — 编辑器报"技能时间不符合规则"

我之前只验证了 1/4 两条，没意识到还有"cast 必须在缓冲区结束前"。

## 根因
**对 SkillEditor 缓冲机制理解不全**：
- 之前以为 buffer_frame 只是"动作可被中断的窗口长度"
- 实际语义是"出手后还能被取消/连招的窗口" → 出手必须先于这个窗口结束
- 所以 cast ≤ buffer_end 是硬约束

## 解决方式
1. **Lint E013 补规则 2**：仅当 buffer_frame > 0 时检查 `cast > buf_start + buf`
   - 反向测试：cast=24/bs=0/bf=20 → 报错"出手帧 24 > 缓冲区结束帧(0+20=20)" ✓
   - 不会误报 buffer_frame=0 的连招技能
2. **速查表 §13 重写**：从 3 条规则扩到 4 条；加 IR/JSON 字段映射表 + 真实样本参考
3. **30142001 IR 修正**：buffer_frame 20 → 30（让 buffer_end=30 ≥ cast=24）

## 利
- 4 条约束全护栏
- 历史 bug 修复：E013 不再漏报真实违规
- 文档明确字段映射（cast_frame ↔ SkillCastFrame ↔ "攻击触发帧"）

## 弊
- E013 复杂度上升（4 条分支）
- 速查 §13 篇幅增加

## 噪音风险
低 — 4 条都是真实硬约束

## 反思
**这是一类"沉淀不彻底"的典型错误**：
- PostMortem #003-C 我以为已经把时长规则全沉淀了（cast≤bd≤cd 三条）
- 用户实测又踩了第 4 条（cast≤buffer_end）
- 教训：沉淀规则时要**穷举所有约束**，不能"沉淀已知的就算"

未来策略：
- 沉淀时主动找该字段在编辑器源码里**全部 Validate 调用点**，确保所有约束都纳入
- 或在反向测试时不仅测"我知道的违规"，也测"边界值组合"（如这种 buffer_frame 偏小的场景）
