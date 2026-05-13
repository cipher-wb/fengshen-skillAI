---
type: 复盘页
summary: 连续 3 次 GATE-0.5 漏样本 — 必须在能力研究阶段做"枚举全列 + ConfigNode 钩子字段穷举 + 相关枚举穷举"三件套
date: 2026-05-09
tags: [PostMortem, GATE-0.5, 能力研究, 子弹机制, 引擎边界]
---

# 2026-05-09-025: GATE-0.5 子弹引擎边界 — 必做"能力研究三件套"

## 🔍 PostMortem 提案 #2026-05-09-025

【新规则】**能力研究三件套**：当 PRD 提到"对 X 做某件事"时（X = 子弹/Buff/特效/实体），开 mermaid 之前必须做：
1. **grep 全部 SkillEffectType 枚举**，按 X 关键词过滤所有相关 effect
2. **读 X 的 ConfigNode 类源代码**，列出它有哪些"钩子字段"（如 `*SkillEffectExecuteInfo`、`Track*Config`、`OnXXX*`）
3. **读 X 相关的所有枚举**（FlyType / TracePathType / 状态 / 类型...）穷举每个值的含义

完成 1+2+3 才允许下笔画 mermaid 蓝图。

【现象】连续 3 次设计"实时整团旋转 + 半径加速度"模板都翻车——每次都是开工后再发现"项目根本不支持这种机制"，被迫推翻重来：

| 版本 | 设计假设 | 翻车点 | 真因 |
|------|----------|--------|------|
| v0.1 | 用 OnTick 循环每帧改子弹位置 | 项目无 OnTick 子弹机制 | 没查 SkillEffectType 全集 |
| ~~v0.5~~ | ~~用 BulletConfig.OnXXXSkillEffectExecuteInfo 字段端口边接每帧 effect~~ | ~~项目根本不存在 OnXXX*ExecuteInfo 字段~~ | **❌ 此行原判断错误（2026-05-09 修正）** — 用户在 Unity 实测过 v0.5 这种"内置 BulletConfig + AfterBornSkillEffectExecuteInfo 接 REPEAT(interval=1, count=-1)"机制可跑。AI 看到样本里没有"REPEAT 自驱+AfterBorn 接 OnTick"的现成组合，**误把"样本不全"当成"框架不支持"**。 |
| ~~v0.6~~ | ~~用 TracePathType=4 静态轨迹假装"飞到再悬停"~~ | **❌ v0.6 错误退化（2026-05-09 修正）** | v0.6 错误地把"REPEAT+245 不是常规模式"当成"项目不支持模板自驱 OnTick" — 实际上 v0.5 在 Unity 里能跑（用户实测验证）。v0.6 把 v0.5 的核心 OnTick 机制阉割掉退化为 360° 散射是错误方向，已撤销，恢复 v0.5 路线。 |

**真正的 GATE-0.5 教训**：v0.1 漏样本是真坑（确实没查 SkillEffectType 全集就写）。但 v0.5/v0.6 这条"项目根本不支持"的判断是 **AI 自我设限错误** — 看到样本里没有某种用法 ≠ 项目禁止这种用法。修正后教训："样本不全 ≠ 框架不支持"，以**用户实测**为最终判据。

总计耗时：v0.1 翻车是真损失（耗 GATE-0.5 漏查；可避免）；v0.5→v0.6 是 AI 自我设限错误退化，v0.7 = 回到 v0.5 + 加 1 个 BulletConfig EXT_PARAM 槽位即收尾。

【根因】GATE-0.5 当前规则只要求"找 3 个相似真实样本 + 三层枚举校对"，但**没强制要求把 X 类型的全部能力扫一遍**。AI 拿到 1~3 个相似样本就开始写，看到样本里有 OnHit/AfterBorn 这两个钩子字段就以为"还有 OnTick 一定也有"——属于**根据局部样本归纳整体能力，但项目刚好不支持这个能力**。

正确做法是：
- ConfigNode 类的字段必须**完整列出来**（grep 类定义看所有字段名），而不是从 1~3 个样本归纳
- 涉及到的枚举必须**全 6~10 个值都看一遍**，明确每个值能干什么不能干什么
- SkillEffectType 全集用 grep 一次性扫出所有相关 effect ID

只有看完 X 的全部能力边界，才能判断"我想做的事项目是否支持"。

【建议沉淀位置】
- [x] `.claude/skills/skill-design/SKILL.md` GATE-0.5 节加"能力研究三件套"段
- [x] `doc/SkillAI/docs/易错点速查.md`（团队版，via sync_postmortem 脚本）
- [ ] memory/feedback_skill_compiler_pitfalls.md：暂不放（这是流程规则，不是技术坑）
- [ ] 工具固化：暂时无法用代码自动检测"AI 没做能力研究"——只能靠流程纪律

【利】
- 一次性扫清 X 的全部能力边界，避免基于"我以为还有 X 字段"的幻想做设计
- 对全新机制的"先验研究"从"找 3 个样本"升级到"读全部源码 + 枚举"，更扎实
- 减少 5+ 版无效迭代（仅本任务直接节省 ~3 小时）

【弊】
- 增加 GATE-0.5 时间成本（从 ~10 分钟增加到 ~25 分钟），简单技能任务可能"过度调研"
- 与现有"找 3 相似样本" + "三层枚举校对"有 ~30% 重叠（一个是横向比较样本，一个是纵向穷举能力）
- 对"X = 普通技能"这种成熟领域可能产出冗余报告

【噪音风险】中 — 仅在涉及"全新机制"或"非常规子弹/Buff行为"时强制；普通配技能（直线子弹/AOE/Buff）可以省略 ConfigNode 字段穷举步骤（因为已有大量样本）

【触发判定】
何时必须做"能力研究三件套"？满足任一即触发：
- PRD 提到"实时调整 X"、"动态修改 X"、"持续监听 X"
- 用户描述里出现"环绕"、"追踪"、"折返"、"链接"、"反弹"、"传送"等非常规运动
- A0.5 §1 找不到 3 个相似真实样本（说明是冷门领域）
- 同一需求已经迭代 2 版以上还没收敛

【你的决定】
[ ] 入库
[ ] 与现有 GATE-0.5 §3 合并
[ ] 修改后入库（建议改成：...）
[ ] 不入库（理由：...）

---

## 历史背景串联

本提案是 #023 + #024 系列的**收尾**——

- [#023](2026-05-09-023-tco-operator-mismatch-and-e021.md) 操作符 op 编码错配 + E021 槽位无消费规则
- [#024](2026-05-09-024-double-root-template-anti-pattern.md) 双根模板把接入义务转嫁调用方是反模式
- **#025（本条）** GATE-0.5 必做"能力研究三件套" — 杜绝基于"我以为还有 X 字段"的设计

#023 是"做对一件事但操作符填错"
#024 是"做对一件事但接入设计不优"
#025 是"想做一件项目根本不支持的事" — 比前两个更严重，整个方案推翻

## 实操示例

**坏例**（v0.1）：
> "项目里 BulletConfigNode 应该有 OnTick 字段（毕竟 OnHit 和 AfterBorn 都有），用它每帧改位置"
>
> 真相：BulletConfig 字段集是 `Model / Speed / LastTime / AfterBornSkillEffectExecuteInfo / BeforeDieSkillEffectExecuteInfo / TracePathType` 等——**根本没 OnTick***。这是基于"OnHit/AfterBorn 都有"做错误归纳。

**好例**（应该这样做）：
```bash
# 第 1 件：grep 所有 BULLET 相关 SkillEffectType
grep -nE "T?SET_.*BULLET|TSET.*MODEL|TSET.*TRACE" Assets/Scripts/CSGameShare/Hotfix/CSCommon/common.nothotfix.cs

# 第 2 件：读 BulletConfigNode 全部字段
grep -nE "public\s+(\w+)\s+\w+\s*[;{]" Assets/Scripts/.../BulletConfigNode.cs

# 第 3 件：穷举 TracePathType 全部值
grep -nE "TracePathType.*=" Assets/Scripts/CSGameShare/Hotfix/CSCommon/common.nothotfix.cs
```

只有这 3 件全做完，才能判断"项目支不支持我想做的实时旋转"。

## 路线收敛产物（修正后 — 2026-05-09 v0.7）

**v0.6 的 24 节点圆周散射模板已撤销**（用户判定为错误退化方向）。

最终落地：v0.7 = v0.5（实测可跑）+ 1 个 BulletConfig EXT_PARAM 槽位
- **文件**：`{{SKILLGRAPH_JSONS_ROOT}}技能模板/子弹/SkillGraph_【模板】旋转扩张子弹圈.json`
- **builder**：`doc/SkillAI/tools/builders/build_rotating_expand_bullet_ring_template_v07.py`
- **核心**：v0.5 的全套 OnTick 机制（内置 BulletConfig 32300150 + 字段端口边接 32300101 OnTick init + REPEAT 每帧自驱）保留；新增 [10] [子弹] 子弹ID(BulletConfig) EXT_PARAM 槽位让调用方可选替换子弹外观/物理；不填走内置子弹 = OnTick 自动跑
- **节点数 / 边数 / TPARAMS / Lint**：82 / 105 / 10 / E=0 W=0 I=0

## 交叉引用

- [[../README]] — PostMortem 索引
- [[2026-05-09-024-double-root-template-anti-pattern]] — 上一篇（双根反模式）
- [[../../docs/易错点速查]] — 团队版易错点（自动同步）
- `.claude/skills/skill-design/SKILL.md` GATE-0.5 — 流程入口
