---
type: 复盘页
summary: PostMortem #026 — RepeatExecute 间隔=0 时次数有 C++ 引擎硬上限（实测 200 触发；建议 ≤ 50 安全），需 lint 防线 + Desc 警告双保险；红队 sub-agent 拒绝盲从主流程接力指令救场（"REPEAT 报错就改 count=-1"差点让模板无限刷子弹）
date: 2026-05-09
tags: [PostMortem, lint, RepeatExecute, 引擎能力边界, 接力消息, 红队]
---

# PostMortem #2026-05-09-026 — RepeatExecute C++ 单帧次数硬上限 + 接力消息节点角色误判

## 三段内容

### 1) 症状

用户实测 v0.7 模板生成的技能投入战斗运行时，C++ 引擎报错：

```
[SkillEffectFactory]->RepeatExecute Execute Count Too Big
```

排查路径：

- 用户把 v0.7 EXT_PARAM[1] (子弹数N) 默认值从 8 改成 200 测试压力上限 → 立即触发引擎保护
- 同时主流程 agent 看到运行时报错"32300029 RepeatExecute Too Big"，第一反应是**误判**该节点是 OnTick 周期节点，建议把 count 改 -1（无限循环），sub-agent 拒绝盲从，去 grep emitted JSON 确认节点角色后发现：32300029 是 **spawn 循环节点**（必须 count=N），不是 OnTick。改 -1 会让模板无限刷子弹。

### 2) 根因

项目 C++ 引擎 `BattleEffectFactory.cpp:1800` 对 `iIntervalTime=0`（同帧齐发）的 RepeatExecute 有硬上限保护：

- 实测：200 已触发
- 推测分界：100 左右
- 安全建议：**≤ 50**

具体上限值未知（需查 C++ 源码常量），但保守 ≤ 50 不会撞线。

> 编辑层面：旧 lint E008 只检查 ParamType=0 字面量 > 100。当 builder 把次数暴露成 EXT_PARAM 槽位时（PT=4），调用方填什么值 lint 看不到 → 默认值就算超界也不会报错；这是 v0.7 第一次让"次数=变量"，必须升级 lint 追溯 TPARAMS 默认值。

### 3) 三层教训

#### a) 引擎能力边界（沉淀位置：lint 护栏 + 团队速查 + builder Desc）

**项目 RepeatExecute 间隔=0 时次数有硬上限**（C++ 引擎 BattleEffectFactory.cpp:1800）。

固化措施（已实施）：

- **lint E008 增强**（`doc/SkillAI/tools/skill_lint.py`）：
  - 字面量 PT=0 + Value > 100 → ERROR（保留）
  - PT=4 EXT_PARAM 引用 → 追溯模板根 TemplateParams[Value-1].DefalutParamJson.Value
    - 默认值 > 100 → ERROR（默认就超界）
    - 默认值 ≤ 100 → WARN（提示在 DefaultValueDesc 写明上限，因为 lint 拦不住调用方填值）
- **builder Desc 警告**（`doc/SkillAI/tools/builders/build_rotating_expand_bullet_ring_template_v07.py`）：
  暴露次数槽位的 `DefaultValueDesc` 必须写"⚠️ N ≤ 50 安全；超过 ~100 触发引擎保护"
- **故障注入测试**（已通过）：注入默认值 200/50/8 三档，分别得到 E=1/W=1/W=1，符合预期

#### b) 接力消息可能误判节点角色（沉淀位置：SKILL.md + skill-designer agent 规则）

**主流程 agent 看到运行时报错涉及具体 SkillEffectConfig ID 时，不能仅凭"REPEAT 报错就改 count=-1"等启发式动作**。本次案例：32300029 主流程被误判为 OnTick 节点（因接力消息描述模糊），实际是 spawn 循环节点；若按"OnTick 用 count=-1"机械修复，会让模板无限刷子弹（崩战）。

**强制流程**：遇到运行时报错涉及具体 SkillEffectConfig ID 时，第一步是 grep emitted JSON 的该节点 `ConfigJson.Desc` / `data.Desc` 字段确认节点角色（spawn? OnTick? 其他？），再决定修复方案。

#### c) Red team sub-agent 拒绝盲从指令的价值（沉淀位置：流程正面案例）

本次 sub-agent 拒绝主流程"把 count 改 -1"的接力指令，先验证再行动 → 救了模板免于"-1 无限刷子弹"灾难。

这已是 sub-agent 第 N 次（≥2 次）拒绝错误指令救场，应作为 **red team 价值正面案例** 留存。流程上确认：

- sub-agent 接到接力指令时，对涉及 RepeatExecute / count / 节点角色等关键改动，**必须先 grep 确认再改**
- 不允许"接力消息说什么就照做"

## 利 / 弊 / 噪音风险

**利**：
- 阻断"默认值就超界"（200 默认）的灾难场景，lint E=1 直接拦截
- WARN 级提示策划在 DefaultValueDesc 写明上限，让调用方有视觉警告
- sub-agent 拒绝盲从案例固化为 SKILL.md 规则后，避免后续 agent 再犯同类错误

**弊**：
- E008 增强后会对所有"间隔=0 + EXT 暴露次数"的合法模板默认产 W=1（如 v0.7 baseline 1 条 WARN），噪音轻度增加但提示有用
- 上限阈值是"实测 200 触发，100 推测分界"经验值，未来若 C++ 引擎调整阈值，lint 需要同步

**噪音风险**：低 — 间隔=0 + 次数=变量的模板不多见（多数 RepeatExecute 用固定字面量），WARN 出现频率低且每条都建议在 Desc 里加警告，是有效引导。

## 沉淀位置

- [x] **代码护栏**：`doc/SkillAI/tools/skill_lint.py` E008 增强（已实施）
- [x] **builder Desc**：`build_rotating_expand_bullet_ring_template_v07.py` TPARAMS[1] DefaultValueDesc 加 ⚠️（已实施）
- [x] **团队速查**：`doc/SkillAI/docs/易错点速查.md`（待 sync 脚本同步）
- [x] **流程规则**：`.claude/skills/skill-design/SKILL.md` 加规则段
- [x] **agent 规则**：`.claude/agents/skill-designer.md` 加"接力消息节点角色描述不可信"规则

## 交叉引用

- [[2026-05-09-025-gate05-bullet-engine-limits]] — GATE-0.5 能力研究三件套（同源理念：先验研究替代直觉）
- [[2026-05-09-024-double-root-template-anti-pattern]] — v0.7 模板系列上一次纠错
- [[2026-05-08-008-collision-template-params]] — TemplateParams 错配族
