---
type: 主题页
summary: PostMortem 自动反思工作流 — AI 主动汇报本轮踩的新坑，用户拍板是否入库
date: 2026-05-08
tags: [PostMortem, 自成长, 反思]
---

# PostMortem 自动反思工作流

> **核心理念**：每次任务结束 AI 自动反思 → 输出提案 → 用户拍板入库与否。**用户始终是 gatekeeper**，避免噪音污染 memory。

## 触发时机

AI 在以下时机自动触发反思：
1. 完成一个 SkillAI 相关任务（生成/修改/审核技能）后
2. 修了一个 Bug 之后
3. 用户说"复盘"/"总结一下"

## 提案格式

见 [.claude/skills/skill-design/references/postmortem_template.md](../../../../.claude/skills/skill-design/references/postmortem_template.md)。

每份提案包含 7 个字段：
- 标题 + 编号（YYYY-MM-DD-NNN）
- **新规则**：一句话规则
- **现象**：触发的 bug 或不符预期
- **根因**：机制层面的"为什么"
- **建议沉淀位置**：3 选 1（私人 memory / 团队公开版 / 工具固化）
- **利 / 弊 / 噪音风险**：让用户判断
- **决定项**：入库 / 合并 / 改写 / 不入库

## 沉淀位置选型

| 位置 | 适用场景 | 触达对象 |
|---|---|---|
| `memory/feedback_skill_compiler_pitfalls.md` | 私人偏好、与策划个人工作流相关 | 仅当前用户 |
| `doc/SkillAI/docs/易错点速查.md` | 普遍性陷阱、其他策划也会踩 | 团队所有人 |
| `doc/SkillAI/tools/<script>.py` | 能用代码自动检测/防止的 | 编译/Lint 时自动护栏 |

**优先级：代码护栏 > 团队文档 > 私人 memory**。能固化为代码的规则就别只放文档；能加文档的就别只放 memory。

## 归档制度

每份提案在通过用户审核后：
1. **如果入库**：内容写入对应位置（memory / docs / tools），同时在本目录归档一份原始提案 `YYYY-MM-DD-NNN-<slug>.md`
2. **如果不入库**：归档原始提案 `YYYY-MM-DD-NNN-<slug>.rejected.md` 含用户拒绝理由
3. **如果合并**：归档 `YYYY-MM-DD-NNN-<slug>.merged-into-<existing>.md`

归档的目的：日后回顾"为什么没记这条规则"，避免重复讨论。

## 索引（按时间倒序）

| 编号 | 标题 | 状态 | 沉淀位置 |
|------|------|------|---------|
| [2026-05-14-043](2026-05-14-043-designer-prompt-iron-rule-burial.md) | **Designer Prompt 铁律埋藏 + Agent Edge 方向反向救场** — 翻车 1：主对话给 skill-designer 下 prompt 时把"isConfigId=true 必须 RefConfigBaseNode 连线"铁律埋在"关键铁律"第 9 条，agent 在风险段提到但"选择跟随老惯例"未包装，导致策划手动指出"新增节点没连线，仅靠数字关联"。翻车 2 → 救场：续作 prompt 描述 edge 方向写反（`inputNodeGUID=RST` 应为 `=子`），agent 严守 memory `feedback_skilleditor_unique_parent.md` + 现网 9 条同类边反向执行 / 0 损失。立法：主对话写 designer prompt 必须把翻车级 memory 铁律显式标红放顶部 + 显式声明"老惯例不算数" + edge 方向用语义描述（数据源→消费方）非 GUID 字段名。 | ✅ 入库 v0.1 | PostMortem #043 + memory feedback_skilleditor_refnode_over_id.md + memory feedback_skilleditor_unique_parent.md + 主对话 prompt 自检清单（待入 CLAUDE.local.md）|
| [2026-05-14-042](2026-05-14-042-skillcondition-blueprint-misperception.md) | **SkillConditionConfig 误判 Excel 必填** — 主对话 GATE-0 时给方案 B 选项原文"要在 SkillConditionConfig.xlsx 新增一条 / 策划要配表"，策划纠正"根本不需要配 excel 表！skillcondition 完全可以用蓝图来配，参考 SkillGraph_301104 吴波测试"。读样本闭环：rid=1011 TSCT_VALUE_COMPARE 节点 ID=320510 / TableTash=`ED89F46EAB95F7ACF5C1911A5A375278`（= SkillConditionConfig 表哈希）/ 蓝图 TSCT_* 节点 = 表行 / NodeEditor 自动导出。根因：mental_model 没有 SkillCondition 子系统页 / 只在 SkillTag系统.md §F 提了 SkillPreConditionConfig（心法注入触发条件 / Excel）/ 主对话脑补两者同源。立法：GATE-MENTAL-IN 显式列"不确定的地方" / grep 1 个现网样本验证 / 涉及表名归属时 0 grep 不下结论。 | ✅ 入库 v0.1 | mental_model/SkillCondition系统.md v0.1 + memory reference_skillcondition_blueprint.md + SkillTag系统.md §F.1 交叉引用修订 |
| [2026-05-14-041](2026-05-14-041-paramtype4-uses-paramuid-not-array-index.md) | **PT=4 引用 Value 是 ParamUID 不是 TPD 数组索引** — 节点 ConfigJson.Params 当 `ParamType=4` (TPT_EXTRA_PARAM) 时，`Value` 必须是目标 TemplateParam 的 **ParamUID（1-indexed 业务编号）**，不是 TemplateParamsDesc 数组的 0-indexed 索引。L0 case 4 TP[7] 守卫排查：1090/1092/1093 写 `{V:7,PT:4}` 实际指向 ParamUID=7 = "自定义额外伤害" 而非 TPD[7]=触发条件（ParamUID=8），导致守卫永远 fallback to true → 用户报"TP[7]配不配没区别"。修：V=7→V=8 三处。症状识别：PT=4 引用表现"永远 true/false / 无视外部传值"。同源 #037（脑补结构）#038（脑补字段名）— 都是 fs 真扫 ground truth 反面教材。 | ✅ 入库 v0.1 | memory/feedback_paramtype4_uses_paramuid.md + PostMortem #041 + 待 curator 加 mental_model SkillEditor文件结构.md §H + 代码护栏候选 lint_paramuid_ref.py |
| [2026-05-13-040](2026-05-13-040-empty-bullet-model.md) | **空子弹专属 Model ID = 4** — 创建"锚点空子弹" / 无视觉表现 BulletConfig 时 Model 必填 4（项目专属空模型 ID），不要填 0（NULL 默认值 / 引擎走 fallback 路径 / "弹不出来"）。典型场景：cast 瞬间创建 Speed=0 / Model=4 不可见锚点子弹捕获 caster 位置 → 真正子弹通过 anchor.AfterBornSE 链发出 → caster 跑了发射点仍是 cast 时位置（位置捕获 idiom）。来源 2026-05-08 用户配 30212009 千叶散华锚点子弹时口头确立 / memory 升级批 v0.16.41 入 PostMortem。 | 🟡 待用户决定 | mental_model/子弹系统.md §D + skill_compiler.py 待加规则 + skill_lint.py 待加 warning |
| [2026-05-13-039](2026-05-13-039-create-bullet-refconfig.md) | **CREATE_BULLET → BulletConfig 跨表引用必须 RefConfigBaseNode 包装** — 凡是 `isConfigId=true` 的 TemplateParam（BulletConfig/BuffConfig/ModelConfig 等）必须通过 RefConfigBaseNode + edge 连线引用，不允许只填 PT=0 数字常量。否则 SkillEditor 视觉无连线 / 策划无法跳转查阅。同模式：BulletConfig.Model 跨引 ModelConfig（用 TableDR.ModelConfigManager + member edge）。来源 2026-05-12 配 30212018 时 32900170/32900171 漏 Ref 包装 / memory 升级批 v0.16.41 入 PostMortem。 | 🟡 待用户决定 | mental_model/SkillEditor文件结构.md §E + mental_model/工具链.md §A 坑 3 + skill_compiler.py make_bullet_config_node + skill_lint.py 待加规则 |
| [2026-05-13-038](2026-05-13-038-relay-message-assertion-unverified.md) | **接力消息事实性断言必须 fs 真扫独立验证** — 子弹伤害管线 7 模板 review 中两处错误断言（"146004907 真实非真实共用" + "闪避 ID 146004858"）经 sub-agent fs 真扫推翻；B-060 D-6006 字典已含错误 ID 触发 cross-batch 不一致；同源 #026（信息层 vs 指令层）。修法：(1) sub-agent prompt 标注 ⚠️ 待验证断言 + GATE-0.5 必查项 +1；(2) curator Mode B 加 GATE-CONSISTENCY 子步骤；(3) D-6115 候选升正式 4-gate 评估 | ✅ 入库 v0.1 | PostMortem #038 + B-061 D-6115 + CLAUDE.local.md GATE-CONSISTENCY 立法 + 代码护栏待办 lint_delta_consistency.py |
| [2026-05-13-037](2026-05-13-037-skilleditor-json-dual-array.md) | **SkillEditor JSON 节点双数组写入铁律** — 手写脚本加节点必须同时写到 `references.RefIds[]`（内容仓库）和顶层 `nodes[]`（UI 渲染目录），缺一→节点不可见但 SkillTagsList 仍显示数值（标红"错误TagID"误导排查方向）。SkillGraph_30312003 叶雨任务连续踩坑：v2 只写前者→排查多轮误猜 TableTash/DESTROY 参数→用户备份 diff 才定位真因→v3 同步双写解决。校验式 `len(nodes)==len(refs)`。 | ✅ 入库 v0.1 | memory/feedback_skilleditor_dual_array.md + mental_model/SkillEditor文件结构.md + PostMortem #037 + 加节点脚本 add_node() 统一封装 |
| [2026-05-12-036](2026-05-12-036-collision-template-default-values.md) | **碰撞模板默认侦测冷却/间隔偏离实战值** — 30214005 烈焰直射 ConfigJson.Params[13]=10/[14]=0 (旧编译器硬编码 default) ≠ 模板 L1 DefalutParamJson default 间隔=1/冷却=10 ≠ 用户实战经验默认 间隔=1/冷却=10 → 三层 default 分裂。修法：编译器 `expand_bullet_straight` 行 1066/1082 改 default 间隔=1/冷却=10 + 新增 `detect_cooldown` IR 字段 + 30214005 重编译 P[13]=1 / P[14]=10 / 拓扑无变 / Lint E=0。**沉淀 4 层**：编译器 + ir_schema + skill-designer 铁律 + SKILL.md GATE-0.5 + curator delta D-036X 候选 | 🟡 待用户决定 | skill_compiler.py expand_bullet_straight + ir_schema.json hit_block + skill-designer.md §模板默认值偏离速查 + SKILL.md GATE-0.5 加项 + 30214005 重编译产物 |
| [2026-05-12-035](2026-05-12-035-bulletconfig-modelconfig-id-dup.md) | **BulletConfig/ModelConfig 全工程 ID 唯一 — #021 v2.6 待办兑现** — 30214005 烈焰直射撞 30222005 青岚劲（PoC 时 AI 抄了 BulletConfig=320032 + ModelConfig=3200088）→ NodeEditor 报"严重错误-ID重复"。修法：30214005 改用 IP=250 AI 专属段（来自 AIGeneratorConfig.AIIpSegment 项目预留）BulletConfig=2500001 / ModelConfig=25000001。沉淀：3 层防线（skill-designer agent 铁律 + SKILL.md GATE-0.5 全工程 ID 扫描 + skill_compiler.py v2.6 _scan_global_used_ids 扩 BulletConfig/ModelConfig） | 🟡 待用户决定 | skill-designer.md §8 新增 + SKILL.md GATE-0.5 扩展 + skill_compiler.py v2.6 待办 + curator delta D-035X (升 candidate 不变量) |
| [2026-05-09-026](2026-05-09-026-repeat-execute-c++-cap-runtime-error.md) | **RepeatExecute 间隔=0 时次数 C++ 引擎硬上限** — 实测 200 触发 "Execute Count Too Big"，建议 ≤ 50 安全；E008 升级追溯 EXT_PARAM 默认值（200→ERROR / 50→WARN / 8→WARN）；红队 sub-agent 拒绝盲从主流程"REPEAT 报错就改 count=-1"接力指令救场（实为 spawn 节点必须 count=N，改 -1 会无限刷子弹） | 🟡 待用户决定 | skill_lint.py E008 增强 + build_rotating_expand_bullet_ring_template_v07.py TPARAMS[1] Desc + SKILL.md "节点角色 grep 确认" 规则 + skill-designer.md "接力消息不可全信" 规则 |
| [2026-05-09-025](2026-05-09-025-gate05-bullet-engine-limits.md) | **GATE-0.5 必做"能力研究三件套"** — 连续 3 次（v0.1/v0.5/v0.6）漏样本：基于"我以为还有 OnTick/OnXXXSkillEffectExecuteInfo/TracePathType=4 静态轨迹"等错误归纳设计模板，6 版翻车后用户拍板退化为 360° 散射。新规则：开 mermaid 前必须做"枚举全列 + ConfigNode 钩子字段穷举 + 相关枚举穷举"三件套 | 🟡 待用户决定 | SKILL.md GATE-0.5 加段 + 易错点速查同步 + builder build_circular_scatter_template.py 落地 24 节点替代方案 |
| [2026-05-09-024](2026-05-09-024-double-root-template-anti-pattern.md) | **双根模板把接入义务转嫁调用方是反模式** — v0.4 双根 (L1 主根 + L2 OnTick 工具根) 调用方需手配 BulletConfig.AfterBorn → 1860216 风格自包含修复 (内置 BulletConfig + ModelConfigNode + 字段端口边)；新增 E022 lint (默认关，故障注入验证拦截 AfterBorn/Model 字段端口边丢失)；纠正 ParamType 枚举认知 (1=TPT_ATTR / 4=TPT_EXTRA_PARAM) | 🟡 待用户决定 | skill_lint.py check_e022_bullet_field_port_consistency（默认不启用）+ build_rotating_expand_bullet_ring_template_v05.py |
| [2026-05-09-023](2026-05-09-023-tco-operator-mismatch-and-e021.md) | **TCO 操作符 op 编码错配 + E021 槽位无消费规则** — empirical 推断枚举值翻车（GT/LT 反向）+ v0.4 简化设计（删 lifetime/damagePerHit）+ E021 手动启用规则 | 🟡 待用户决定 | skill_lint.py check_e021_template_param_unused（默认不启用）+ builder op 修正 |
| [2026-05-09-022](2026-05-09-022-dynamic-port-edge-lint.md) | **Dynamic Port 出边自检 + 双根模板视觉澄清** — 反向反思：接力诊断错误（误把 REPEAT 当 dynamic port），求证后用 3573 真实样本证伪 + 加 E020/W006 lint 防线 | 🟡 待用户决定 | skill_lint.py E020/W006 已固化 |
| [2026-05-08-021](2026-05-08-021-global-id-uniqueness.md) | **v2.5 全局 ID 唯一性** — IdAllocator 必须预扫全工程已用 ID（effect/cond/select/tag），跨文件重复会让 SkillEditor 导出 xlsx 报"严重错误-ID重复"（41 条由 30142002 等 PoC 文件引发） | ✅ 入库 v2.5 | skill_compiler.py 加 _scan_global_used_ids + IdAllocator 预填 |
| [2026-05-08-020](2026-05-08-020-tag-third-pattern-and-indicator7.md) | **v2.4.1 第三种 SkillTag 模式（Pattern C 临时计算）+ 指示器枚举漏 7（扇形）** — 30212009 千叶散华审核反证 #017 过严 + 补 TIRT_SECTOR=7 | ✅ 入库 v2.4.1 | skill_lint.py E019 区分 GET-only / skill_compiler.py indicator_type_map +扇形=7 / 易错点速查加三种 Pattern 表 |
| [2026-05-08-019](2026-05-08-019-entity-level-tag.md) | **v2.3.2 SkillTag 实体级 (Pattern B)** — Param[1]=0/PT=0 表示"-" 类型 = 挂在实体上而非技能上，跨技能透明读取（推翻 #017 的"必填 source_skill_id"） | ✅ 入库 v2.3.2（被 #020 完善：加上 Pattern C 临时计算） | skill_compiler.py MODIFY/GET 改实体级模式 / 简化去掉 source_skill_id 参数 |
| [2026-05-08-018](2026-05-08-018-int32-overflow.md) | **v2.3.1 hotfix：所有 ID ≤ int32 max** — Newtonsoft.Json 把 3014200301 解为 -1280766995 → 节点反序列化全炸 → "ID:0 ConfigID:0" 连环报错 | ✅ 入库 v2.3.1 | skill_compiler.py validate_ir +_check_int32 递归防御 / IR tag 改 skill_id*10+offset |
| [2026-05-08-017](2026-05-08-017-skill-tag-cross-skill.md) | **v2.3 SkillTag 跨技能必填 source_skill_id** — tag 必须显式 SkillTagsConfigNode 声明 + 命名约定 + 跨技能读用 GET_SKILL_TAG_VALUE 显式填 skill_id | ⚠️ 部分推翻（被 #019 改为实体级 Pattern B：Param[1]=0/PT=0 即可跨技能透明读取，不需要 source_skill_id） | tag 显式声明规则保留；source_skill_id 机制废弃 |
| [2026-05-08-016](2026-05-08-016-two-stage-v2.2-fixes.md) | **v2.2 两段式技能三修** — 第二段 CD 不继承主 CD / 槽位用 GET_SKILL_SLOT_TYPE 动态取 / 位置记录用双 SkillTag (X/Y) | ✅ 入库 v2.2（被 #017 修补：tag 必须声明 + 跨技能必填 skill_id） | ir_schema +1 字段 + skill_compiler.py 重写 _split_two_stage / expand_summon_clone / expand_return_to_clone / expand_two_stage_skill |
| [2026-05-08-015](2026-05-08-015-two-stage-real-mechanism.md) | **两段式按键真机制 = 44014633 切槽位** — 30221000 反向工程 + IR v2.1 改多 SkillConfig 输出（一个 yaml → 两个 JSON） | ✅ 入库 v2.1（被 #016 修补） | ir_schema two_stage_skill 扩 5 字段 + skill_compiler.py 多 SkillConfig 输出 + KNOWN_TEMPLATES +1 模板 |
| [2026-05-08-014](2026-05-08-014-indicator-enum-fix.md) | **TIndicatorType 枚举错配** — "直线"实际是 3 不是 2，2 是单目标（PostMortem #008/#009 同源坑扩到 SkillConfig 字段） | ✅ 入库（修正性） | skill_compiler.py indicator_type_map + _scan 默认值修正 |
| [2026-05-08-013](2026-05-08-013-ir-v2.0-mvp-shipped.md) | **IR v2.0 MVP 端到端** — MOBA 大招级技能落地（displacement / summon_clone / two_stage_skill / return_to_clone / aoe_circle / clone_active_pattern PoC） | ⚠️ 部分推翻（two_stage_skill 被 #015 重做） | ir_schema +6 step + skill_compiler.py +6 expander + KNOWN_TEMPLATES +4 模板 |
| [2026-05-08-012](2026-05-08-012-detection-cooldown-vs-startup-delay.md) | **侦测冷却 ≠ 启动延迟** — v1.3 子弹出生即死，改 DELAY 包第二碰撞模板 | ✅ 入库 v1.3.1 | expand_bullet_boomerang 用 TSET_DELAY_EXECUTE 包第二碰撞 + 速查§18 |
| [2026-05-08-011](2026-05-08-011-dual-collision-self-detect.md) | **双碰撞模板架构 v1.3** — 让回旋子弹"碰到主角才销毁"（target_camp=3 + 侦测冷却） | ⚠️ 部分废弃（被 #012 推翻：侦测冷却≠启动延迟） | v1.3 拓扑保留，但启动机制由 #012 用 DELAY 取代 |
| [2026-05-08-010](2026-05-08-010-distance-cutoff-bug.md) | LifeFlag=3 + MaxDistance 截断 → 子弹回飞途中提前死亡（v1.2.4 修复） | ✅ 入库 v1.2.4 | LifeFlag=1 + MaxDistance×4 + LastTime 充足 |
| [2026-05-08-009](2026-05-08-009-trigger-vs-shape-enum.md) | **TTriggerType vs TShapeType 用错枚举** — 1 误为圆形实为矩形 + LifeFlag/TracePathParams 没用对 | ✅ 入库 v1.2.3 | expand_bullet_boomerang shape=0(TTT_Circle) + TracePathParams 注入 IR 参数 + LifeFlag=3 + SKILL.md GATE-0.5 §3 加"3 层枚举校对" |
| [2026-05-08-008](2026-05-08-008-collision-template-params.md) | **子弹通用-碰撞模板参数 [9]"是否跟随创建者飞行"** — 一个参数错配导致 AOE 跟主角动 + 视觉"矩形"错觉 | ✅ 入库 v1.2.2 | expand_bullet_boomerang follow_creator=0 + LastTime 收紧 + GATE-0.5 §3 加"读模板 TemplateParams 中文名" |
| [2026-05-08-007](2026-05-08-007-boomerang-redesign.md) | **回旋飞回重设计 v1.2.1** — 单 Bullet 套蝴蝶妖配置 + derive_edges 修生命周期边丢失 | ✅ 入库 | expand_bullet_boomerang 简化 + derive_edges 修复 + SKILL.md GATE-0.5 §3 警告"不能凭字段名猜行为" |
| [2026-05-08-006](2026-05-08-006-ir-v1.2-boomerang-pattern.md) | **IR v1.2 回旋飞回 pattern + 双 Bullet 接力** — LOL 泰隆 R 模式落地（**已被 #007 推翻为单 Bullet**） | ⚠️ 部分废弃 | 双 Bullet 实现已废，schema/反编译器仍生效 |
| [2026-05-08-005](2026-05-08-005-firstpass-quality.md) | **首次配技能为何 4 轮才对** — AI 偷懒+健忘的流程纪律问题 | ✅ 入库（流程级） | skill-design SKILL.md 加 GATE-0.5（先验研究）+ GATE-3.5（自审 4 项） |
| [2026-05-08-004](2026-05-08-004-cast-vs-buffer-end.md) | 时长规则漏一条 — cast 必须 ≤ buffer_end | ✅ 入库（补充 003-C） | 速查§13 改写 + Lint E013 补规则 2 |
| [2026-05-08-003-A](2026-05-08-003-explosion-aoe-misconception.md) | **explosion 设计认知错误**：碰撞模板的 collision_radius 已是 AOE，不需要 QUICK_DAMAGE | ✅ 入库（修正性） | 速查§11 重写 + PRD§4.3.2 + 编译器 v1.1.1 |
| [2026-05-08-003-B](2026-05-08-003-explosion-aoe-misconception.md) | SkillIndicatorParam 按 type 分类（单体应为空） | ✅ 入库 | 速查§12 + 编译器修正 |
| [2026-05-08-003-C](2026-05-08-003-explosion-aoe-misconception.md) | 时长规则 cast≤bd≤cd（Lint E013 漏报修复） | ✅ 入库 | 速查§13 + Lint E013 修正 |
| [2026-05-08-002-A](2026-05-08-002-ir-v1.1-mvp-fields.md) | IR 升级到 v1.1（angles / explosion / on_hit_buff） | ✅ 入库 | PRD §4.3.1 / §4.3.2 + ir_schema.json + skill_compiler.py |
| [2026-05-08-002-B](2026-05-08-002-ir-v1.1-mvp-fields.md) | ~~explosion v1.1 是单目标量不是真 AOE~~（被 003-A 推翻 — explosion 不是节点而是语义糖） | ⚠️ 已废弃 | 速查§11 已被 003-A 重写 |
| [2026-05-08-002-C](2026-05-08-002-ir-v1.1-mvp-fields.md) | 子弹运动学由 BulletConfig 决定 | ❌ 拒绝 | （PRD §4.3.2 已顺带说明，不另开条目） |

## 反例 — 哪些不应做提案

- **已存在的规则**：先 grep `memory/feedback_skill_compiler_pitfalls.md` 和 `docs/易错点速查.md`，已有就不重提
- **一次性问题**：仅这次任务特有的环境问题（如本地 Python 版本不对），不是规则
- **数值类问题**：单个技能的伤害系数偏高 — 这是数值评审范畴，不是规则
- **用户偏好类**：用户说"我喜欢更短的输出" — 这应该入 memory/user_*.md 而不是 feedback

## 模板（开发者参考）

完整 markdown 模板见 [.claude/skills/skill-design/references/postmortem_template.md](../../../../.claude/skills/skill-design/references/postmortem_template.md)。

## 交叉引用

- [[../README]] — SkillAI 系统入口
- [[../docs/易错点速查]] — 团队公开版易错点（待生成）
- 私人 memory：`memory/feedback_skill_compiler_pitfalls.md`
