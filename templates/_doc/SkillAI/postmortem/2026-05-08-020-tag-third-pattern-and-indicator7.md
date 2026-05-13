---
proposal_id: 2026-05-08-020
status: accepted
sediment_target:
  - doc/SkillAI/tools/skill_lint.py（E019 降为 W006，临时 tag 不强制声明）
  - doc/SkillAI/tools/skill_compiler.py（indicator_type_map 加 "扇形"=7）
  - doc/SkillAI/docs/易错点速查.md（指示器完整表 + SkillTag 三种模式）
related_skill: 30212009 千叶散华（审核时发现 14 个 lint 误报 + 指示器映射缺漏）
ir_version: 2.4.1
---

# 第三种 SkillTag 模式 + 指示器枚举漏 7（扇形）

## 决策
✅ **入库 v2.4.1（撤回 #017 的"硬必须声明"规则 + 补全 #014 的指示器枚举）**

## 现象（审核 30212009 千叶散华时连发现）

### 现象 A：SkillTag "Pattern C 临时计算" 被 lint E019 误报 14 次

30212009 是已上线的木宗门生产技能。审核时跑 lint，得到 14 个 ERROR：
```
[E019] tag_id=1001~1005（技能级 Pattern A），但本 JSON 没有 SkillTagsConfigNode 声明它
```

但生产技能在跑 — 显然不是真 bug。检查 30212009 的用法：
- MODIFY tag 1001~1005 用 Pattern A `[V=4/PT=5, V=41/PT=5, ...]`（绑初始技能实例）
- 用作"循环计数器 / 累计角度 / 当前子弹索引"的**临时计算变量**
- 不需要 RetainWhenDie / 不需要非零默认 / 用完即抛

**结论**：SkillTag 引擎允许"读未声明 tag → 默认 0"，所以临时计算用法不需要 SkillTagsConfigNode。

### 现象 B：指示器枚举 7（扇形）未被 PostMortem #014 列入

30212009 的 `SkillIndicatorType=7`，但 #014 的修复表只列到 6（双圆抓捕）。
真实 enum：
```
TIndicatorType:
  TIRT_NULL = 0
  TIRT_NO_TARGET = 1
  TIRT_SINGLE_TARGET = 2
  TIRT_LINE = 3
  TIRT_DOUBLE_CIRCLE = 4
  TIRT_MULTIWAY = 5
  TIRT_DOUBLE_CIRCLE_CAPTRUE = 6
  TIRT_SECTOR = 7  ← #014 漏了
```

我的编译器 `indicator_type_map` 也错了 — 把 "扇形" 映射到 5（多向）：
```python
"多向": 5, "扇形": 5,    # ← 错，扇形应该是 7
```

## 根因

### A 的根因
PostMortem #017 写 "tag 必须显式 SkillTagsConfigNode 声明"，是基于"位置 X/Y 跨技能读"的具体场景泛化的。**真正的规则**应该是分层的：

| Tag 用法 | 是否需要声明 | 例子 |
|---------|-------------|------|
| **私有持久（Pattern A）+ 非零默认 / 持续到死** | **必须声明** | 30221000 tag 2250022 = "技能可释放范围 default=800" |
| **跨技能共享（Pattern B 实体级）** | **必须声明 1 次**（任意 JSON 都行，编译器还应增加同源警告） | 30142003 tag 301420030 = "残影位置 X" |
| **临时计算（Pattern C）** | **不需要声明** | 30212009 tag 1001~1005 = 循环计数 / 累计值 |

### B 的根因
PostMortem #014 写补丁时**没扫完整 enum 文件**，只看了 0~6 就停了。属于 GATE-0.5 §3 三层校对的执行不到位（应该把 enum 整个 dump 出来对照）。

## 修法（待落地）

### 1. lint E019 降级 + 改判定逻辑
当前：所有 Pattern A tag 不在本 JSON 声明就 ERROR
新：
- 若 tag 有任何 MODIFY 操作（写过）→ 视为合法的"私有/临时"用法 → INFO（不报 ERROR）
- 若 tag 只有 GET 没 MODIFY → 仍 ERROR（确实是引用了不存在的 tag）

### 2. compiler indicator_type_map 补全
```python
# 修复后
indicator_type_map = {
    "-": 0, "NULL": 0,
    "无目标": 1,
    "单目标": 2, "单体": 2,
    "直线": 3,
    "双圆": 4, "圆形": 4,
    "多向": 5,
    "双圆抓捕": 6,
    "扇形": 7,        # ← 新增（TIRT_SECTOR）
}
```
同步更新 `_scan` 默认推断：fan-step IR 走 7。

### 3. 易错点速查补"SkillTag 三种模式表"

## 利
- 撤回 #017 的过度严格规则 — 团队配类似 30212009 的复杂技能不会再被 lint 误报
- 补齐 indicator 枚举 — 编译"扇形指示器"技能时不再静默错配为"多向"
- 三种 Pattern 表写到团队文档 — 新人配 SkillTag 知道选哪种

## 弊
- 已用 PostMortem #017 的训练（如 30142003 v2.3）声明了 tag — 这些声明保留无害
- E019 降为 INFO 后，**真"GET 引用不存在 tag"的情况**也会变成 INFO 不再阻塞（要单独加规则 E020 区分）

## 噪音风险
低 — 30212009 是真实生产技能反证 #017 过严，证据充分

## 三种 Pattern 完整表（团队级）
| Pattern | Param[1] | 用途 | 是否声明 SkillTagsConfigNode | 跨技能 |
|---------|----------|------|------------------------------|--------|
| **A 私有持久** | `41/PT=5`（初始技能实例） | 默认值 / 持续到死 / 持久状态 | **是** | × 仅当前技能 |
| **B 实体级共享** | `0/PT=0`（"-" 类型） | 跨技能共享状态（位置/全局计时） | **是**（声明在源技能） | ✓ 透明 |
| **C 临时计算** | `41/PT=5` | 循环计数 / 累计 / 用完即抛 | **否** | × 仅当前技能 |

**判定准则**：
- "我需要从其他技能读这个值吗？" → 是 → Pattern B
- "我希望它有非零默认 / 持续到死吗？" → 是 → Pattern A
- 否则 → Pattern C（用完即抛）

## 历史 Tag 教训演进表
| 版本 | 误解 | 真相 |
|------|------|------|
| v2.0/2.1 | tag 不需要专门处理，直接用就行 | × 跨技能读不到 |
| v2.2 | tag 是"挂在技能上"的全局变量 | × 第二段读不到第一段写的 |
| v2.3 | "tag 必须声明 + 跨技能必填 source_skill_id" | × 过严，#019 才发现实体级模式 |
| v2.3.2 | 实体级 (Param[1]=0/PT=0) 是跨技能首选 | ✓ 但没考虑临时 tag 场景 |
| **v2.4.1（本次）** | **三种模式分场景选用** | ✓ 完整 |

## 推广动作
1. ✅ 修 `skill_compiler.py` indicator_type_map
2. ✅ 修 `skill_lint.py` E019 → 降级 + 区分 GET-only 误用
3. ✅ 易错点速查加"SkillTag 三种模式表"
4. ⏳ 后续：写 IR step 让用户写 `tag_pattern: 临时` / `tag_pattern: 私有` / `tag_pattern: 实体级` 显式标注（v2.5）

## Unity 实测预期
1. ✅ 30212009 跑 lint 应 E=0（仅 W001 + 可能 W003）
2. ✅ 配新扇形指示器技能 IR 写 `type: 扇形`，编译产物 SkillIndicatorType=7
3. ✅ 配类似 30212009 用临时 tag 1001~ 计数的技能不再被 lint ERROR
