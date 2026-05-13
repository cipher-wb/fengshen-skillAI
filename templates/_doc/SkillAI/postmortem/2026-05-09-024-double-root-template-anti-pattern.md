---
type: 复盘页
summary: 双根模板把接入义务转嫁调用方是反模式 — 必须按 1860216 风格内置 BulletConfig + 字段端口边自包含
date: 2026-05-09
tags: [PostMortem, 模板设计, 反模式, 1860216, BulletConfig, 字段端口]
---

# PostMortem #2026-05-09-024 — 双根模板反模式 / 1860216 自包含风格

## 触发

旋转扩张子弹圈模板 v0.4 用户实测后给出明确意见：

1. **双根模板（L1 主流程根 32300001 + L2 OnTick 工具根 32300101）是反模式**：调用方拿到模板后必须手动配自己 BulletConfig 的 `AfterBornSkillEffectExecuteInfo.SkillEffectConfigID = 32300101`，把接入义务转嫁给了下游
2. **应改成 1860216 风格"内置 BulletConfig + 字段级 EXT_PARAM"**：模板自带子弹定义，调用方拖入即用

用户原话："这个 OnTick 全靠调用方手动接 32300101 真烦，1860216 链子弹的内置 BulletConfig 模式才对。"

## 调查结果

### v0.4 双根反模式的代价

v0.4 模板有两个独立"根"：
- L1 ROOT (32300001, IsTemplate=true)：主流程，`SET=118 调用方` 直接接入
- L2 ROOT (32300101)：OnTick init，**没有任何节点引用它**——必须由调用方手动配置进 BulletConfig 字段

**问题**：
- 调用方需阅读 sticky note，手动找 32300101，然后在自己 BulletConfig 节点的 ConfigJson 里改 `AfterBornSkillEffectExecuteInfo.SkillEffectConfigID`——容易遗漏，新人踩坑
- 模板拓扑视觉上"两个孤岛"——破坏 BFS 单根可达性，PostMortem #022 已经指出"双根模板视觉断层"症状
- 模板的"自包含/可移植"性大打折扣：换 BulletConfig 必重配 OnTick 接口

### 1860216 链子弹模板的正确姿势（GATE-0.5 红队精读）

**关键样本**：[{{SKILLGRAPH_JSONS_ROOT}}技能模板/子弹/SkillGraph_1860216【模板】链子弹.json](../../../{{SKILLGRAPH_JSONS_ROOT}}技能模板/子弹/SkillGraph_1860216【模板】链子弹.json)

1. **模板内置 BulletConfigNode**（rid 1002, ID=1860427, IsTemplate=false）：完整 ConfigJson 写好 Model/LastTime/Speed 等默认值
2. **关键字段端口边**：BulletConfigNode 通过 `outputFieldName="PackedMembersOutput"` + `outputPortIdentifier="<嵌套字段路径>"` 让其他节点的 ID 连入
   - `AfterBornSkillEffectExecuteInfo.SkillEffectConfigID` ← TSET_ORDER_EXECUTE (186008484)
   - `BeforeBornSkillEffectExecuteInfo.SkillEffectConfigID` ← effect 节点
   - `DieSkillEffectExecuteInfo.SkillEffectConfigID` ← effect 节点
3. **TSET_CREATE_BULLET 直接死值引用** Params[0]=1860427（BulletConfig.ID）—— 不通过 EXT_PARAM
4. **模板 ROOT** (rid 1001, ID=186000022, IsTemplate=true) 的 TemplateParams 暴露给调用方的是「视觉/外观/链路 SkillEffect ID」
5. **调用方** 用 `SkillEffectType=118 (TSET_RUN_SKILL_EFFECT_TEMPLATE)` 调用 ROOT，传 Params 数组

### 关键洞察 — TParamType 枚举真值

**之前 v0.3/v0.4 设计假设错了**："ParamType=1 是 EXT_PARAM"。但 C# 真值（[common.nothotfix.cs:14977](../../../Assets/Scripts/TableDR_CS/NotHotfix/Gen/common.nothotfix.cs)）：

```
TPT_NULL          = 0  -
TPT_ATTR          = 1  属性 (不是 EXT_PARAM!)
TPT_FUNCTION_RETURN = 2 函数返回值
TPT_SKILL_PARAM   = 3  技能参数 (SkillTag)
TPT_EXTRA_PARAM   = 4  模板参数 ⭐ (这才是真正 EXT_PARAM)
TPT_COMMON_PARAM  = 5  常用数值参数
TPT_EVENT_PARAM   = 6  技能消息参数
TPT_COMMON_SKILL_PARAM = 7
```

**重要**：项目中 `ParamType=4 (TPT_EXTRA_PARAM)` 仅在 SkillEffect.Params 数组中可索引到 TemplateParam[i]，**不能直接修改 BulletConfig 字段值**——BulletConfig 字段动态化只能通过"字段端口边连入另一个 ID 提供者节点（ModelConfigNode 给 Model；SkillEffectConfigNode 给 AfterBorn 等）"。

1860216 自身的"model" TemplateParam 实际**有名无实**——模板内 BulletConfig.Model=30008 死值，model EXT_PARAM 没真消费（仅作 UI 占位）。这是 1860216 风格"对 BulletConfig 全权负责"的代价：模板调用方只能改算法系参数。

## v0.5 改动总结

**节点层**：
| 改动 | 净增减 |
|---|---|
| 新增 BulletConfigNode (32300150) IsTemplate=false | +1 |
| 新增 ModelConfigNode (320149 默认普通飞叶) | +1 |
| 节点数 80 → 82 | +2 |

**边层**：
| 改动 | 净增减 |
|---|---|
| BulletConfig.Model ← ModelConfigNode 字段端口边 | +1 |
| BulletConfig.AfterBornSkillEffectExecuteInfo ← OnTick init effect 字段端口边 | +1 |
| 自动派生 PackedParamsOutput 边（BULLET 节点 Params[0]=32300150 死值引用） | +1 |
| 边数 103 → 106 | +3 |

**TemplateParams**：
| 改动 | 净增减 |
|---|---|
| 删除 [1] bulletID（被内置 BulletConfig 替代） | -1 |
| 重新调整索引 EXT_N=1 / EXT_R0=2 / ... / EXT_FOLLOW=9 | (索引调整) |
| 新 9 项算法 EXT_PARAM 全部真消费 | 9/9 |

**默认值**（用户接力消息单位制）：
| 参数 | 默认 |
|---|---|
| N 子弹数 | 8 |
| R0 初始半径 | 200 单位 ≈ 2 米 |
| φ 切线偏移 | 0° |
| vR 径向速度 | 10 单位/帧 ≈ 3 米/秒 |
| aR 径向加速度 | 0 单位/秒² |
| ω 角速度 | 3 度/帧 ≈ 90°/秒 |
| maxR 最大半径 | 1500 单位 ≈ 15 米 |
| minR 最小半径 | 0（默认不触发）|
| followPlayer | 1（跟随主角，MOBA 标配）|

## 新规则 / 防线

### 规则 1（设计级）：模板设计若需 OnTick 等持续机制，必须用 1860216 风格内置 BulletConfig

**新规则**：设计模板时若需 OnTick 等持续运行机制（轨迹模拟 / 周期性变化），**必须** grep 项目内现存模板的"内置 BulletConfig 模式"（如 1860216 链子弹模板），不许走"调用方手动接 effect ID"路径。

**根因**：双根模板让调用方"看到模板就要读 sticky note 找隐藏 ID"——破坏拖入即用约定，拓扑视觉断裂，新人踩坑率 100%。

**实现方式**：沉淀到 `.claude/skills/skill-design/SKILL.md` GATE-0.5 校对清单 — 加一条"模板有 OnTick/持续机制时必须内置 BulletConfig + 字段端口边"。

### 规则 2（工具固化）：E022 lint 规则 — 内置 BulletConfig 字段端口一致性

**新规则**：lint 检查 BulletConfigNode 的关键字段（Model / AfterBorn / BeforeBorn / Die SkillEffectConfigID），若 ConfigJson 写非零值且**同图内有同 ID 节点**作为 ID 提供者，必须存在对应 PackedMembersOutput 字段端口边。

**实现位置**：[doc/SkillAI/tools/skill_lint.py](../tools/skill_lint.py) `check_e022_bullet_field_port_consistency()` 函数。

**重要细节（避免误报）**：
- **默认未注册到 lint_file 主管线**——生产中大量真实样本（千叶散华以外的卡牌/普通技能）的 BulletConfig 字段直接写 ID 死值且不用字段端口边，假阳性 88 条
- **仅 builder 自检场景手动调用**（同 E021）
- **白名单 Model=4**（空子弹专属，[memory/reference_empty_bullet_model.md](../../../memory/reference_empty_bullet_model.md)）
- **故障注入测试**：[doc/SkillAI/tools/verify_e022_fault_injection.py](../tools/verify_e022_fault_injection.py)，删除 v0.5 模板的 AfterBorn / Model 字段端口边后 E022 能正确触发

### 规则 3（防御）：empirical 推断 ParamType / 枚举值必须用 C# 源码二次验证

**与 PostMortem #023 同款**——本次再次踩 ParamType 枚举推断错（一开始把 ParamType=1 当 EXT_PARAM，实际 1=TPT_ATTR，4=TPT_EXTRA_PARAM）。

**沉淀**：本规则在 #023 已在 SKILL.md GATE-0.5 加，本次再次验证其重要性，无需重复加规则。

### 规则 4（认知）：TemplateParam"暴露不消费"在生产模板中是合法用法

1860216 模板的 model EXT_PARAM 名义上声明但模板内部没真消费——这在生产中是合法用法（占位 / 历史保留 / 跨文件 effect ID 引用）。E021 假阳性率 31% 的根因即此。**v0.5 没沿用这种空挂——9 项 EXT_PARAM 全部真消费**。

## 拓扑 diff (v0.4 → v0.5 实测)

```
节点：80 → 82  (+2: BulletConfigNode + ModelConfigNode)
边：  103 → 106  (+3: 2 字段端口边 + 1 自动派生 PackedParamsOutput)
TemplateParams：10 → 9 项 (-1 bulletID)
单根 BFS 可达性：v0.4 双根 → v0.5 单根 100% 可达 (73/73 非 SkillTag 节点)
Lint：E=0 W=0
故障注入测试 E022：删 AfterBorn / 删 Model 字段端口边都能拦截 ✓
```

## 相关 PostMortem

- [#022](2026-05-09-022-dynamic-port-edge-lint.md) 双根模板视觉断层（本次彻底改造）
- [#023](2026-05-09-023-tco-operator-mismatch-and-e021.md) v0.4 op 修正（v0.5 沿用）
- [memory/reference_empty_bullet_model.md](../../../memory/reference_empty_bullet_model.md) 空子弹 Model=4 私有约定（E022 白名单）

## 决定项（待用户拍板）

- [ ] 入库本 PostMortem 到团队级速查表
- [ ] 跑 `python doc/SkillAI/tools/sync_postmortem_to_easy_pitfalls.py` 同步
- [ ] 在 [.claude/skills/skill-design/SKILL.md](../../../.claude/skills/skill-design/SKILL.md) GATE-0.5 加规则 1
- [ ] 是否归档 v0.4 builder 到 `tools/builders/_archive/`（可与未来 builders 归档机制一起做）
