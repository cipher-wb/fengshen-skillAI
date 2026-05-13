---
type: 复盘页
summary: CREATE_BULLET / 跨表配置引用必须用 RefConfigBaseNode 包装 + edge 连线，不能只填 PT=0 常量 ID（否则视觉断线 / 策划无法跳转查阅）
date: 2026-05-13
tags: [PostMortem, SkillEditor, RefConfigBaseNode, BulletConfig, ModelConfig, 跨表引用]
status: 提案待审（来源 memory 升级批 v0.16.41 / Mode C 一致性巡检）
---

# PostMortem #039 — CREATE_BULLET → BulletConfig 跨表引用必须 RefConfigBaseNode 包装

## 新规则

**SkillEditor 中凡是可以连线引用的配置参数（`BulletConfig / BuffConfig / ModelConfig / SkillConfig` 等 `isConfigId=true` 或 `RefTypeName≠空` 的 TemplateParam），必须通过 `RefConfigBaseNode` + edge 连线引用，不允许只填 PT=0 数字常量。**

## 现象

任务：2026-05-12 给 `SkillGraph_30212018` 加 32900170 / 32900171 两个 CREATE_BULLET 节点（强化 / 普通子弹）。

错误做法：

```json
// CREATE_BULLET 32900170 节点
{
  "Params": [
    { "Value": 320262, "ParamType": 0, ... }  // ← P[0] BulletConfig ID 直接填 PT=0 常量
  ]
}
```

**症状**：
- 编辑器加载 / 表面正常 / Lint 不报错
- 但 SkillEditor 视觉上 `CREATE_BULLET` 周围**没有"子弹"节点连入**
- 策划无法在 SkillEditor 里跳转查阅对应的 BulletConfig（看不到子弹的速度、模型、生命时长等属性）

用户 2026-05-12 提示：「32900170 这种创建子弹节点到具体子弹的 edge 还没连」。

## 根因

SkillEditor 的视觉表示分两层：

1. **数据层**：`Params[N] = {Value: 320262, ParamType: 0}` 是 PT=0 字面常量 → 引擎层运行时直接取数字 → 功能正常
2. **视觉层**：编辑器面板要"显示连线 + 提供跳转锚点"，必须从一个 SkillEditor 可识别的"节点对象"输出 edge

如果只有 PT=0 常量、没有 RefConfigBaseNode 节点 → 视觉层无对象可连 → 没线 → 策划只看到一串数字 / 无法跳转。

进一步影响：
- 维护成本高（每次改 BulletConfig 都要 grep ID + 切文件）
- 审核成本高（reviewer 看不到子弹属性，必须打开 BulletConfig 子文件）
- 复用率低（其他技能想 reuse 同一个 BulletConfig 时不容易发现）

**同问题适用范围**：
- `CREATE_BULLET` P[0] → BulletConfig
- `ADD_BUFF` P[?] → BuffConfig
- `BulletConfig.Model` 跨表 → ModelConfig（用 `TableDR.ModelConfigManager` + member edge）
- 所有 `isConfigId=true` 的 TemplateParam

## 修复

**RefConfigBaseNode 包装 + edge 连线范式**：

```python
# 1. 加 RefConfigBaseNode 节点
add_node(
    rid=new_rid,
    cls="RefConfigBaseNode",
    extra={
        "ManualID": 320262,
        "ID": 320262,
        "TableManagerName": "TableDR.BulletConfigManager",  # 或 ModelConfigManager / BuffConfigManager
    }
)

# 2. 加 edge: Ref → CREATE_BULLET P[0]
add_edge(
    input_node_guid=ref_node_guid,        # 子（提供输出）
    output_node_guid=create_bullet_guid,  # 父（接受输入）
    output_port_identifier="0",            # P[0]
    output_field_name="PackedParamsOutput",
)

# 3. CREATE_BULLET.Params[0] 改为 PT=2 NodeRef
create_bullet.Params[0] = {
    "Value": ref_node_id,    # 指向 RefConfigBaseNode 节点 ID
    "ParamType": 2,           # NodeRef
}
```

**30212010 金标参考**：

```
RefConfigBaseNode {
  ID=320110, ManualID=320110,
  TableManagerName='TableDR.BulletConfigManager'
} → CREATE_BULLET 32002235 P[0]  field='PackedParamsOutput' outPort='0'
```

修复后：
- 视觉上能看到 Ref 节点连到 CREATE_BULLET
- 策划在 SkillEditor 双击 Ref 节点 → 自动跳到 BulletConfig 查阅子弹属性

## 教训

1. **数据层正确 ≠ 视觉层正确**：SkillEditor 的"视觉连线 + 跳转锚点"依赖 RefConfigBaseNode 节点对象，不能用 PT=0 常量替代
2. **策划的视觉可读性是一等公民**：AI 配技能时不能只追求"能跑"，必须保证"策划在 SkillEditor 里能看明白"
3. **跨表引用同源**：BulletConfig.Model 跨引 ModelConfig 也走相同模式（member edge + RefConfigBaseNode）
4. **配套查清单**：每次加 CREATE_BULLET / ADD_BUFF 必检
   - [ ] 有没有配套的 RefConfigBaseNode？
   - [ ] edge 是否连到 CREATE_BULLET.P[0]？
   - [ ] Params[N].ParamType 是否改为 2（NodeRef）？

## 预防

### 工具固化

- `skill_compiler.py` 的 `make_bullet_config_node` / `make_model_config_node` 应自动生成 RefConfigBaseNode 包装 + edge
- `skill_lint.py` 增加规则：`isConfigId=true` 的参数若为 PT=0 → warning
- 详见 [工具链.md §A 坑 3](../mental_model/工具链.md)

### Sensor

- 蓝图视觉看 CREATE_BULLET 节点周围没"子弹"节点连入 → 检查是否漏了 RefConfigBaseNode 包装
- 配技能时审核 checklist：所有 CREATE_BULLET / ADD_BUFF 都必须有 RefConfigBaseNode

## 相关

- [memory/feedback_create_bullet_refconfig.md](../../../memory/feedback_create_bullet_refconfig.md) — memory 原文（rule_2 思想史保留）
- [memory/feedback_skilleditor_refnode_over_id.md](../../../memory/feedback_skilleditor_refnode_over_id.md) — 通用规则原文（rule_2 思想史保留）
- [mental_model/SkillEditor文件结构.md §E 跨表引用 RefConfigBaseNode 包装](../mental_model/SkillEditor文件结构.md) — 升正式后的体系化主张
- [mental_model/工具链.md §A 坑 3](../mental_model/工具链.md) — skill_compiler 坑 3 引用类节点必须显式生成
- [postmortem #033 unique-parent-rule](2026-05-12-033-skilleditor-unique-parent-rule.md) — 同类 SkillEditor 视觉断线机制
- [postmortem #035 BulletConfig / ModelConfig ID 冲突](2026-05-12-035-bulletconfig-modelconfig-id-dup.md) — 跨表 ID 命名空间相关

## 决定项

- **沉淀位置**：
  - mental_model 子系统页（[SkillEditor文件结构.md §E](../mental_model/SkillEditor文件结构.md)）✓ 已落
  - 工具固化（`skill_compiler.py` make_bullet_config_node / make_model_config_node 已固化 / lint 待增规则）
  - PostMortem 本文件（详细案例 + 教训）
- **memory 处理**：原 `memory/feedback_create_bullet_refconfig.md` 保留 + 加首行升级注脚（rule_2 严守）
