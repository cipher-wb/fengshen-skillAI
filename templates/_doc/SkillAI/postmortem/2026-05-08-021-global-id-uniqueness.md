---
proposal_id: 2026-05-08-021
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_compiler.py（_scan_global_used_ids + IdAllocator 预填）
related_skill: 30212009 千叶散华审核时发现 41 条 ID 重复（其中 30+ 条由 AI-gen PoC 产生）
ir_version: 2.5
---

# 全局 ID 唯一性 — IdAllocator 必须跨文件检查

## 决策
✅ **入库 v2.5**

## 现象

用户在 SkillEditor 点"导出数据"时，控制台报：
```
[NodeEditor] Error: 【严重错误-ID重复】详情如下:
SkillEffectConfig_32002001:
    SkillGraph_30142002_环刃归心.json
    SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json
SkillEffectConfig_32002008:
    SkillGraph_30112001【木宗门】飞叶锁魂.json
    SkillGraph_30142002_环刃归心.json
... (共 41 条重复)
```

41 条 ID 重复。其中 35+ 条由 AI 早期生成的 PoC 文件（30122900 / 30142001-30142004）造成 — 它们的 effect ID 撞上多个生产技能。

## 根因

### 1. ID 命名空间是全局的
SkillEditor 把所有 `SkillGraph_*.json` 的节点 ID 当成一张总表。
- `SkillEffectConfig.ID` 跨文件不可重复
- 同样适用 `SkillConditionConfig` / `SkillSelectConfig` / `SkillTagsConfig` / `BulletConfig` / `ModelConfig`

### 2. IdAllocator 的旧公式只看 skill_id 后 3 位
```python
base = (skill_id % 1000) * 1000
self._effect_seq = 32000000 + base
```

含义：`30142002 → base=2000 → effect_seq=32002000` 起。
但是 `30212002 → 也 base=2000 → 也 32002000` 起。**任何 skill_id 后 3 位相同的两个技能必撞 effect ID**。

而且我没做"已用 ID 全局排查" — 直接顺序分配，碰到生产技能已用的 ID 也照样占。

## 修法（已落地）

### 1. `_scan_global_used_ids(exclude_skill_id)` — 全工程扫描

```python
def _scan_global_used_ids(exclude_skill_id: int = 0) -> set[int]:
    """扫所有 SkillGraph_*.json 收集已用 effect/cond/select/tag config ID。
    排除 exclude_skill_id 对应文件（自身重编译场景）。
    缓存结果。"""
    ...
    for d in scan_dirs:
        for p in d.rglob("SkillGraph_*.json"):
            if filename starts with "SkillGraph_<exclude_skill_id>": continue
            for node in graph.references.RefIds:
                if node.cls in (TSET_*, TSCT_*, TSKILLSELECT_*, SkillTagsConfigNode):
                    used.add(node.ConfigJson.ID)
    ...
```

### 2. IdAllocator 初始化时预填全局已用 ID

```python
def __init__(self, skill_id: int, skip_global_scan: bool = False):
    ...
    self._used_ids = set(_scan_global_used_ids(exclude_skill_id=skill_id))
    # allocate_*_id 的 while loop 自动跳过冲突
```

### 3. 验证（30142002 编译模拟）
```
全工程已用 ID 总数: 131053
  ID 32002001 已用 (30112001 飞叶锁魂)
  ID 32002002 已用
  ID 32002003 已用
  ID 32002004 未用
  ID 32003015 已用
  ...

IdAllocator(30142002) 连续分配 8 个 effect ID:
  [32002004, 32002005, 32002006, 32002007,
   32002011, 32002012, 32002013, 32002014]
  ✓ 跳过 01-03（已用）
  ✓ 跳过 08-10（飞叶锁魂用）
```

## 当前局限

### 性能
- 每次 compile 启动扫 3000+ JSON，耗时约 9 秒
- 缓存只在同一 Python 进程内有效；CLI 单次调用每次重扫
- 后续可加持久化缓存（`.cache/used_ids.json` + 文件 mtime 失效）

### 仅扫这 4 类节点
- ✓ TSET_* / TSCT_* / TSKILLSELECT_* (SkillEffectConfig / Condition / Select)
- ✓ SkillTagsConfigNode
- ❌ BulletConfigNode（多技能共享 BulletConfig 的场景未处理）
- ❌ ModelConfigNode（同上）

> BulletConfig/ModelConfig 跨文件重复**不一定是 bug**——多个技能引用同一 BulletConfig 是合法用例。但当前 AI-gen 直接 embed 一份新 BulletConfigNode 而不是用 RefConfigBaseNode 占位，会在导出阶段被报"ID 重复"。这个是**架构问题**：AI 编译器应该用 RefConfigBaseNode 引用共享 BulletConfig，而不是 embed。留 v2.6 解决。

### `--skip-global-scan` 救急选项
快速迭代时可加 `IdAllocator(skill_id, skip_global_scan=True)` 跳过全局扫描（节约 9 秒），但**有撞 ID 风险**。仅限本地测试用。

## 利
- 解决 30+ 条 AI 历史冲突的根因（即使 PoC 文件已被用户删除，未来 AI 生成不会再撞）
- 防御自动化：IdAllocator 内部就拒绝冲突，不依赖人工审查

## 弊
- 启动慢 9 秒
- 仅覆盖 effect/cond/select/tag，不含 Bullet/Model（v2.6 待补）

## 噪音风险
低 — 此修复纯属"加防御"，不改 IR / 不改产物拓扑

## 历史教训

### v2.4 已修过 skill_id 唯一性（PostMortem #018）
当时只对 `meta.skill_id` 做了全局扫，没做 effect/cond/select。半套防御 → 这次 41 条冲突就是漏的另一半。

**教训**：以后凡是"全项目唯一约束"的 ID 类，扫一次必须扫全 — 不要只扫一类。

## 推广动作

1. 把 `_scan_global_used_ids` 的缓存改成**进程间持久化**（`.cache/skill_global_ids.pickle` + mtime invalidation），消除 9 秒开销
2. v2.6 处理 BulletConfig/ModelConfig 共享：编译器输出时检测到全工程已存在的 BulletConfig ID 时，emit RefConfigBaseNode 而不是 BulletConfigNode
3. skill_lint.py 加规则 E026：扫 SkillGraph 内引用的 effect/bullet/model ID，如果在全工程其他文件中已存在 BulletConfigNode embedding，警告"考虑改用 RefConfigBaseNode"
