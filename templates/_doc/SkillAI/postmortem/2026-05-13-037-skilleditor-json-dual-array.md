---
type: 复盘页
summary: SkillGraph_*.json 手写节点必须同时写到 references.RefIds[] 和顶层 nodes[] 双数组，缺一导致 UI 不渲染
date: 2026-05-13
tags: [PostMortem, SkillEditor, JSON结构, 双数组, SerializeReference]
---

# PostMortem #037 — SkillEditor JSON 节点双数组写入铁律

## 新规则

**手写脚本往 `SkillGraph_*.json` 添加节点时，必须同时写入两个数组：**

1. `data.references.RefIds[]` — 节点完整数据（Unity SerializeReference 反序列化的内容仓库）
2. `data.nodes[]`（顶层）— 仅 `{"rid": NNNN}` 的"目录索引"

**校验式**：`len(d['nodes']) == len(d['references']['RefIds'])`。

## 现象

任务：给 `SkillGraph_30312003【木宗门】神通_人阶_叶雨.json` 新增 2 个 SkillTagsConfigNode（320292/320287）+ 10 个 effect 节点（GET×2/DELAY×3/DESTROY×3/ORDER×2）+ 13 条 edge。

v2 脚本执行后：
- ✓ `references.RefIds[]` 从 54 → 66
- ✓ `edges[]` 从 48 → 61
- ✗ 顶层 `nodes[]` 仍是 54（漏写）

打开 SkillEditor 表现：
- 技能参数列表里 320292 / 320287 **有值**（90 / 30）但显示红色"**错误TagID**"
- 蓝图工作区里看不到任何新加的节点
- 用户排查若干轮均无解

## 根因

SkillEditor 加载 JSON 的流程：

1. 先遍历**顶层 `nodes[]`** 拿全部 rid 作为渲染目录
2. 再用 rid 去 `references.RefIds[]` 查内容反序列化
3. SkillTagsList 是 SkillConfigNode 内部的列表，按 `SkillTagConfigID` 直接查找——所以它能在参数列表里**显示值**，但因为对应的 SkillTagsConfigNode 不在顶层 `nodes[]` 名单上 → 编辑器视它为"未定义" → 标红"错误TagID"

特征：**"参数列表里有 Value 但蓝图里找不到节点 + 显示错误 TagID"** ≡ 顶层 `nodes[]` 漏写。

## 修复

v3 脚本统一封装：

```python
def add_node(rid, ...):
    refs.append(node)                   # references.RefIds[]
    data['nodes'].append({"rid": rid})  # 顶层 nodes[]（关键修复）
```

执行后 `refs == nodes_top == 66`，重开 SkillEditor 一切正常。

## 建议沉淀位置

- ✅ **memory** [feedback_skilleditor_dual_array.md](../../../memory/feedback_skilleditor_dual_array.md)（已加）
- ✅ **PostMortem** 本文件
- ⚠️ **代码护栏**：v3 脚本最后已加 assert；建议把这条 assert 提到 `doc/SkillAI/tools/lint_*.py` 里作为加节点脚本的统一校验项
- ⚠️ **mental_model**：在 SkillEntry系统.md 或新建 SkillEditor文件结构.md 加 §双数组写入铁律 段（已加入口引用）

## 利 / 弊 / 噪音风险

- **利**：彻底防止"加了节点 UI 不渲染"这种诡异 bug，特征明确（红色错误TagID）一眼识别
- **弊**：要求所有手写节点的脚本走统一封装函数
- **噪音**：低 —— 这是数据完整性铁律，触达对象是所有写脚本加节点的人（编译器/curator/手写修复脚本）

## 决定项

✅ **入库 3 处**：memory + PostMortem + mental_model 入口引用。代码护栏待后续 lint 工具更新。

## 关联

- 类似 schema 完整性问题：[#033 SkillEditor unique-parent](2026-05-12-033-skilleditor-unique-parent-rule.md)（edge 端口铁律）
- 同一任务的并发坑：v2 之前还踩过 TableTash 空值、DESTROY_ENTITY 参数错填 V=41 等（已在前几轮修掉）
