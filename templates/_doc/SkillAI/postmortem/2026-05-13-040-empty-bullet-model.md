---
type: 复盘页
summary: 创建"锚点空子弹" / 无视觉表现 BulletConfig 时 Model 必填 4（项目专属空模型 ID），不要填 0（NULL 默认值 / 可能引起不可预期处理）
date: 2026-05-13
tags: [PostMortem, SkillEditor, BulletConfig, 空子弹, ModelConfig, 锚点子弹]
status: 提案待审（来源 memory 升级批 v0.16.41 / Mode C 一致性巡检）
---

# PostMortem #040 — 空子弹专属 Model ID = 4

## 新规则

**当创建"锚点空子弹"或任何不需要视觉表现的 `BulletConfig` 时，`Model` 字段必须填 `4`（项目专门给空子弹保留的 Model ID），不要填 `0`。**

`0` 是 NULL 默认值 / 可能引起其他不可预期的处理（如默认模型回退 / "弹不出来" / 引擎走 fallback 路径）。

## 现象

任务：2026-05-08 配 `SkillGraph_30212009` 千叶散华锚点子弹时，创建 `BulletConfig 320149`"千叶散华锚点空子弹"用于：
- `Speed=0`（静止）
- 不可见（无视觉）
- 在 cast 瞬间捕获 caster 当时的位置（不跟随后续位移）
- 通过 `AfterBornSkillEffectExecuteInfo` 链发出真正的子弹

AI 默认填 `Model = 0`，用户当即纠正：

> "如果我让你创建空子弹，模型 ID 记得填 4，这个是空子弹专属 ID"

## 根因

**项目工程约定**：

| Model 值 | 含义 | 引擎处理 |
|---------|------|---------|
| **4** | ✅ **项目专属"空模型 ID"** | 不渲染 / 正常逻辑可用 / 锚点子弹专用 |
| `0` | ❌ NULL 默认值 | 引擎走 fallback 路径 / 可能"弹不出来" / 不可预期 |

ModelConfig `4` 是项目预定义的"空模型"行（待源码 grep 验证具体声明位置），区别于 ModelConfig=0（未配置 / 引擎 fallback）。

## 修复

**正确范式（千叶散华锚点空子弹）**：

```json
{
  "ID": 320149,
  "Name": "千叶散华锚点空子弹",
  "Model": 4,          // ← 关键：4 = 空模型
  "Speed": 0,
  "LastTime": 60,
  "AfterBornSkillEffectExecuteInfo": {"SkillEffectConfigID": 32002513}
}
```

## 典型应用场景：锚点空子弹（capture-at-cast pattern）

锚点空子弹是项目常用的 **位置捕获 idiom**：

1. **在 cast 瞬间创建一个 `Speed=0 / Model=4` 不可见锚点子弹**
2. **锚点子弹捕获 caster 当时的位置**（不跟随后续位移）
3. **真正的子弹通过 anchor 的 `AfterBornSkillEffectExecuteInfo` 链接发出**
4. **即使 caster 跑了，发射点仍是 cast 时位置**

这种 idiom 的核心价值：
- 解决"释放时 vs 子弹出生时位置不一致"的同步问题
- 任何需要"在固定位置生成子弹簇"的技能都可以用（千叶散华 / 扇形分层弹幕等）

## 教训

1. **项目约定不能自学**：Model=4 是项目工程约定，源码 enum 不一定显式声明，必须靠 memory / mental_model 沉淀
2. **NULL 不等于空**：`Model=0` 和 `Model=4` 在引擎处理上是两条不同路径，不能混用
3. **AI 默认填 0 是常见 bug**：策划脑子里有"空子弹"概念，AI 没有先验 → 默认填 0 → 跑不出来或 fallback 怪异行为
4. **应用 idiom 库**：锚点空子弹是项目常用 idiom，应在 [mental_model/子弹系统.md §D](../mental_model/子弹系统.md) 列入"必会模式"

## 预防

### 工具固化

- `skill_compiler.py` 的 `make_bullet_config_node` 应增加规则：`if BulletConfig.Speed==0 and Model 未指定 → 默认填 4`
- `skill_lint.py` 增加规则：`BulletConfig.Model == 0` → warning（提示是否应为 4）
- 详见 [工具链.md §A](../mental_model/工具链.md)

### Sensor

- 任何"锚点子弹" / "Speed=0 / 不可见" 场景 → 第一时间 check Model 是否为 4
- 子弹"弹不出来 / 异常 fallback 行为" → 第一时间 check Model 字段

## 相关

- [memory/reference_empty_bullet_model.md](../../../memory/reference_empty_bullet_model.md) — memory 原文（rule_2 思想史保留）
- [mental_model/子弹系统.md §D 空子弹 Model 必填 4](../mental_model/子弹系统.md) — 升正式后的体系化主张
- [mental_model/工具链.md §A 坑 3](../mental_model/工具链.md) — skill_compiler 坑 3 引用类节点配置 + 默认值
- [postmortem #035 BulletConfig / ModelConfig ID 冲突](2026-05-12-035-bulletconfig-modelconfig-id-dup.md) — 跨表 ID 命名空间相关
- 真实样本：`{{SKILLGRAPH_JSONS_ROOT}}宗门技能/木宗门技能/SkillGraph_30212009_*.json` BulletConfig 320149

## 决定项

- **沉淀位置**：
  - mental_model 子系统页（[子弹系统.md §D 空子弹 Model 必填 4](../mental_model/子弹系统.md)）✓ 已落
  - 工具固化（待 skill_compiler / skill_lint 加规则）
  - PostMortem 本文件（详细案例 + idiom 介绍）
- **memory 处理**：原 `memory/reference_empty_bullet_model.md` 保留 + 加首行升级注脚（rule_2 严守）
