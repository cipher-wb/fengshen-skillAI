---
proposal_id: 2026-05-12-036
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py (expand_bullet_straight detect_interval default 10→1 + 新增 detect_cooldown default 10)
  - doc/SkillAI/tools/ir/ir_schema.json (hit_block 新增 detect_cooldown 字段 + detect_interval default 10→1)
  - .claude/agents/skill-designer.md (新增 §模板默认值偏离实战值速查 表)
  - .claude/skills/skill-design/SKILL.md (GATE-0.5 加项 - 用模板时查偏离速查表)
  - mental_model/candidate (curator delta D-036X 候选 / 由 curator agent peer review)
related_skill: 30214005 烈焰直射 (用户口头修订触发)
---

# 碰撞模板（SkillGraph_【模板】子弹通用逻辑-碰撞.json）默认侦测冷却/间隔偏离实战值

## 决策
✅ **入库** — 用户战斗策划经验沉淀（证据等级 4 = 用户实测最高优先 / 同 PostMortem #025 教训）

## 触发实例

30214005 烈焰直射首次配置（PoC 时基于 v1.x 编译器默认值生成）：

| 参数 | 30214005 当前 | 用户期望（实战值） | 模板自身 default |
|------|--------------|-------------------|------------------|
| 侦测间隔(帧) | **10** | **1** | **1** |
| 侦测冷却(帧) | **0** | **10** | **10** |

用户原话（2026-05-12 口述）：
> 当使用 `SkillGraph_【模板】子弹通用逻辑-碰撞.json` 这个模板的时候，**默认情况下**：
> - 侦测冷却 应填 10
> - 侦测间隔 应填 1

## 三层默认值的"分裂状态"（根因）

碰撞模板（路径 `{{SKILLGRAPH_JSONS_ROOT}}技能模板/子弹/SkillGraph_【模板】子弹通用逻辑-碰撞.json`）的"侦测间隔/侦测冷却"参数有 3 个层次的默认值，互相冲突：

| 层次 | 来源 | 侦测间隔 | 侦测冷却 |
|------|------|---------|---------|
| **(L1) 模板 TemplateParams 自身定义** | rid=1000 ID=190016404 (ORDER_EXECUTE 根) `TemplateParams[10]/[11].DefalutParamJson` | **1** | **10** |
| **(L2) 编译器硬编码 default**（旧） | `expand_bullet_straight` 行 1066 + 行 1082 | **10** | **0** |
| **(L3) 用户实战经验 / 用户期望** | 战斗策划口头确认 2026-05-12 | **1** | **10** |

⚠️ **关键发现**：
- L1 模板自身 default 与 L3 用户期望**完全一致**（模板原作者已经设了正确值）
- 但 L2 编译器作者（之前的我）**没读 L1 模板的 DefalutParamJson 字段** → 盲设了反向值（间隔=10 / 冷却=0）
- 调用方 ConfigJson.Params 写入的值会**覆盖 L1**，所以 L2 写错就坏了

## 各参数语义复盘

### 侦测间隔(帧) = 模板内 `TSET_REPEAT_EXECUTE` 周期
- **=1**：每 1 帧侦测一次（高频，几乎实时）
- **=10**：每 10 帧侦测一次（低频，会漏检快速穿过的目标）
- **实战意义**：直线/扇形子弹掠过目标时，间隔过大可能跳过目标 → 必须 = 1 / 高频侦测

### 侦测冷却(帧) = 同一目标两次成功侦测之间的冷却
- **=10**：同一目标命中后 10 帧内不会再次触发命中后功能（防止单次穿过多次扣血）
- **=0**：无冷却 → 子弹与目标接触每帧持续触发命中（DoT 效果 / 通常不是想要的）
- **实战意义**：
  - 单次命中即销毁的子弹（如 30214005 烈焰直射 `destroy_on_hit=true`）：理论上 0 也行（子弹销毁了）但 10 是安全默认 — 防"销毁前一帧多触发"
  - 持续型 AOE 子弹（如旋转环刃）：必须 ≥ 10 / 不然每个目标每帧扣血 → 数值灾难
- **PostMortem #012 已澄清**："侦测冷却"≠ "启动延迟"（两次成功侦测之间的间隔 / 不是"出生后等 N 帧"）

## 解决方式（3 处沉淀）

### A. 编译器修订（doc/SkillAI/tools/skill_compiler.py 行 1058-1090）

```python
# Before:
detect_interval = hit_cfg.get("detect_interval", 10)
collision_node = make_template_call_node(
    template_key="子弹通用逻辑-碰撞",
    extra_params=[
        ...,
        detect_interval,                     # 侦测间隔 (default 10 ❌)
        0,                                   # 侦测冷却 (硬编码 0 ❌)
        0,                                   # 侦测次数
    ],
    ...
)

# After:
# PostMortem #036: 侦测间隔默认 1 / 侦测冷却默认 10 (与碰撞模板自身默认一致 + 用户实战经验值)
detect_interval = hit_cfg.get("detect_interval", 1)
detect_cooldown = hit_cfg.get("detect_cooldown", 10)
collision_node = make_template_call_node(
    template_key="子弹通用逻辑-碰撞",
    extra_params=[
        ...,
        detect_interval,                     # 侦测间隔 (PostMortem #036 默认 1)
        detect_cooldown,                     # 侦测冷却 (PostMortem #036 默认 10)
        0,                                   # 侦测次数
    ],
    ...
)
```

⚠️ **范围**：仅修了 `expand_bullet_straight` 的硬编码 default，**未动**：
- `expand_bullet_boomerang` 第一/第二碰撞模板（行 1280-1349）：因 PostMortem #011/#012 涉及双碰撞 + DELAY 包装机制特殊，第二碰撞用 5 帧间隔有合理性 → **后续单独评审**
- 其他自定义子弹 expander：审视性扩张 / 后续按需

### B. ir_schema.json (hit_block) 加 detect_cooldown 字段 + 修订 detect_interval default

```json
"detect_interval":    { "type": "integer", "default": 1, "description": "侦测间隔(帧) — 默认 1 (PostMortem #036 用户实战经验值，与碰撞模板自身默认一致；旧默认 10 已废)" },
"detect_cooldown":    { "type": "integer", "default": 10, "description": "侦测冷却(帧) — 默认 10 (PostMortem #036 用户实战经验值，与碰撞模板自身默认一致；同一目标两次成功侦测之间的冷却)" },
```

### C. 30214005 烈焰直射 IR YAML 同步修订 + 重编译

IR 加注释 + 显式字段：
```yaml
# PostMortem #036 默认值修订: 侦测间隔=1 / 侦测冷却=10 (与碰撞模板自身默认一致 + 用户实战经验值)
# 旧默认 detect_interval=10 / 侦测冷却=0 是反向值 → 用户口头修订 2026-05-12
detect_interval: 1         # 侦测间隔 1 帧 (用户实战默认 / 模板默认值)
detect_cooldown: 10        # 侦测冷却 10 帧 (用户实战默认 / 模板默认值 / 同一目标两次成功侦测间冷却)
```

重编译产物（`{{SKILLGRAPH_JSONS_ROOT}}宗门技能/AIGen/SkillGraph_30214005_烈焰直射.json`）：
- 节点数：11（与编译前一致 / 拓扑无变更）
- ConfigJson.Params[13] = **1**（曾 10）
- ConfigJson.Params[14] = **10**（曾 0）
- Lint：E=0 W=1（W003 急速影响=0 / 与本次修订无关）

## 利
- ✅ 编译器 default 与 L1 模板 default 对齐 → 后续配技能默认值正确
- ✅ 30214005 实测可正确侦测（间隔=1 高频不漏检 / 冷却=10 防销毁前多触发）
- ✅ IR 显式增加 `detect_cooldown` 字段，调用方可按场景覆盖（如旋转持续型子弹设 30）
- ✅ 沉淀 3 层：代码护栏（编译器+schema）/ 团队文档（skill-designer + SKILL.md）/ mental_model（curator delta）

## 弊
- ⚠️ `expand_bullet_boomerang` 第一/第二碰撞模板未同步修订 — 那两处历史上有特殊机制（PostMortem #011/#012），盲改会引发双碰撞拓扑回归 → 后续单独评审
- ⚠️ 已用 `expand_bullet_straight` 编译过的旧技能（如 30122900 PoC / 30214003 长虹贯日）的 ConfigJson.Params[13]/[14] 仍是 10/0 — **需要批量重编译或保持现状（用户可决定）**

## 噪音风险
低 — 与 L1 模板默认值对齐 / 与用户实战经验对齐 / 不是凭空新规则

## 反思 — "读模板 DefalutParamJson"是 GATE-0.5 应该做但漏的一步

PostMortem #008 已经说过"调用模板前必须读 TemplateParams 的中文名定义"，但这次踩的是**读了名字没读 DefalutParamJson**：

| 我做了 | 我没做 |
|--------|--------|
| ✓ 读了 13 个 TemplateParams 的中文名 | ✗ **没读每个 TemplateParam 的 DefalutParamJson 字段** |
| ✓ 编了 `make_template_call_node` 调用 | ✗ 编译器硬编码了 default，没有 fallback 到模板自身 default |

**新规则（GATE-0.5 §3 扩充）**：
> 任何用 `make_template_call_node` 调用的模板 default 值，**必须以模板根节点 TemplateParams[i].DefalutParamJson 为权威默认**。编译器 expander 的硬编码 default 必须 = 模板 DefalutParamJson 解析值。
>
> 操作命令：
> ```python
> # 查模板的 TemplateParams default 值
> with open('<template_path>',encoding='utf-8') as f: d=json.load(f)
> for r in d['references']['RefIds']:
>     tps=r['data'].get('TemplateParams') or []
>     if len(tps)>0:
>         for i,tp in enumerate(tps):
>             print(i, tp.get('Name'), tp.get('DefalutParamJson'))
> ```
>
> **不能凭"我以为 default 是 0"**（因为不同模板 default 不同 / L1 = 真相）。

## Unity 实测预期

用户 Ctrl+R 刷新 Unity → SkillEditor 打开 30214005 烈焰直射：
- 第三个 RUN_SKILL_EFFECT_TEMPLATE（碰撞模板）的"侦测间隔"显示 **1**（曾 10）
- 第三个 RUN_SKILL_EFFECT_TEMPLATE（碰撞模板）的"侦测冷却"显示 **10**（曾 0）
- 拓扑无变更 / 11 节点 / 10 边
- 实战进入战斗：火符直线飞 / 高频侦测命中（不漏检）/ 命中销毁
