---
proposal_id: 2026-05-12-035
status: proposed
sediment_target:
  - .claude/agents/skill-designer.md（新增"配 ID 类节点必查全工程唯一"铁律）
  - .claude/skills/skill-design/SKILL.md（GATE-0.5 增加扫 BulletConfig/ModelConfig ID 唯一性步骤）
  - doc/SkillAI/tools/skill_compiler.py（_scan_global_used_ids 扩展 BulletConfig/ModelConfig + 引入 AI 专属 IP 段 250）
  - doc/SkillAI/mental_model/(待 curator 决定子系统页) — 升 candidate 不变量 D-035X "ID 类节点全工程唯一 + IP 段命名空间"
related_skill: 30214005 烈焰直射（与 30222005 青岚劲撞 BulletConfig=320032 / ModelConfig=3200088）
related_postmortem: #021（effect/cond/select/tag 已修，BulletConfig/ModelConfig 留 v2.6 — 即本帖兑现）
ir_version: 2.6（compiler 待跟）
---

# BulletConfig / ModelConfig 全工程 ID 唯一 — #021 v2.6 待办兑现

## 决策
**Proposed**（PostMortem 落盘 + skill-designer 铁律 + SKILL.md GATE-0.5 扩展同步推进 / curator delta 已提案）

## 现象

用户在 Unity NodeEditor 打开后弹红字：

```
【NodeEditor】Error: 【严重错误-ID重复】详情如下:
BulletConfig_320032:
  SkillGraph_30222005【木宗门】奇术_地阶_青岚劲.json
  SkillGraph_30214005_烈焰直射.json
ModelConfig_3200088:
  SkillGraph_30222005【木宗门】奇术_地阶_青岚劲.json
  SkillGraph_30214005_烈焰直射.json
```

## 根因

### 1. PoC 时 AI 直接抄了样本里的 BulletConfig.ID

`30214005 烈焰直射.skill.yaml` IR 注释自暴：
- `bullet_id: 320032            # 沿用 PoC 直线子弹 BulletConfig`
- `hit_effect_model: 3200088  # 命中特效 Model (与 PoC 一致)`

PoC 阶段为了快速跑通直接 grep 找了一个真实样本的 BulletConfig=320032 / ModelConfig=3200088 抄进来用。这两个 ID 同时是 **30222005 青岚劲**（同样 IP=32 段策划做的真实在用宗门技能）原生定义的 ID → CheckError 报"严重错误-ID重复"。

### 2. PostMortem #021 明确把 BulletConfig/ModelConfig 留作 v2.6 待办

#021 修复了 effect/cond/select/tag 的全工程唯一扫描，但当时判断"BulletConfig/ModelConfig 跨文件重复**不一定是 bug**——多个技能引用同一 BulletConfig 是合法用例"，留待 v2.6 通过 RefConfigBaseNode 引用机制解决。

实际本次踩坑证明：**AI 主动产出 BulletConfigNode 时永远不要 embed 别人的 ID** — 跨图复用必须走 RefConfigBaseNode（cross-graph 引用节点 / 不算原生定义 / 不参与 ID 唯一性约束）；自己生成的 BulletConfig/ModelConfig **必须用全工程未占用的新 ID**。

### 3. AI 没意识到项目已经预留了"AI 专属 IP 段 250"

`Assets/Thirds/NodeEditor/SkillEditor/Saves/SvnIgnore/AIGeneratorConfig.json` 字段 `AIIpSegment = 250` —— 项目已经为 AI 生成器预留了 IP=250 段，全工程 0 占用，是天然的 AI 专属命名空间。但 skill-designer agent 完全不知道这个段位的存在，凭直觉抄样本 ID。

## ID 命名规则（源码 ground truth）

源码：[Assets/Thirds/NodeEditor/Datas/ConfigIDManager.cs](../../Assets/Thirds/NodeEditor/Datas/ConfigIDManager.cs)
- L26 `defaultConfigIDAdd = 10000`
- L518-526 `GetConfigIDAddNum(configName)`：从 `TableAnnotation.json` 取每张表的 `ConfigIDAdd`，未配置走默认 10000
- L530-540 `GetMin/MaxConfigID(configName, ip)`：`[ip * addNum, (ip+1) * addNum - 1]`
- L345-384 `GetNextConfigID()`：`ip = LocalSettings.Inst.ID`（本机 IP 末段 / 1-255）/ ID = ip * addNum + 已分配集合的最大值 + 1，跳过冲突

每张表的步长（来自 [TableAnnotation.json](../../Assets/Thirds/NodeEditor/SkillEditor/Saves/TableAnnotation.json)）：

| 表 | ConfigIDAdd | IP=250 区间 |
|----|-------------|-------------|
| BulletConfig | **10000** | [2500000, 2509999] |
| ModelConfig | **100000** | [25000000, 25099999] |
| SkillConfig | 10000 | [2500000, 2509999]（但宗门技能 SkillConfig.ID 是策划手填 8 位号系如 30214005，不走自动分配）|
| SkillEffectConfig | **1000000** | [250000000, 250999999] |
| SkillTagsConfig | 10000 | [2500000, 2509999] |
| SkillConditionConfig / SkillSelectConfig / BuffConfig | 10000 | [2500000, 2509999] |

## CheckError 实现（源码 ground truth）

[Assets/Thirds/NodeEditor/Datas/JsonGraphManager.cs:443-468](../../Assets/Thirds/NodeEditor/Datas/JsonGraphManager.cs)
- 检查 `ConfigNameID2GraphInfos`（**只统计常规节点 / 引用节点 RefConfigNameID2GraphInfos 不参与**）
- `kv.Value.Count > 1` 即报错（同一 `<ConfigName>_<ID>` 被多个 SkillGraph 文件原生定义）
- 节流 3 秒一次 / 只在编辑器加载/Reload/Save 时触发

`ConfigBaseNode` 系节点（如 `SkillConfigNode` / `BulletConfigNode` / `ModelConfigNode`）= 常规节点（参与唯一性约束）；`RefConfigBaseNode` = 引用节点（不参与 / 多文件引用同一 ID 合法）。

## 引用复用 vs 独立新建（业界惯例）

scan 火宗 25 个 SkillGraph：**0 个** 通过 RefConfigBaseNode 跨图引用其他 SkillGraph 的 BulletConfig/ModelConfig。

→ **每个技能的子弹/模型都在自己的 SkillGraph 内独立定义独立 ID**。跨图复用 BulletConfig/ModelConfig 是反模式（AI 生成不应该尝试）。

## 修法（30214005 已修）

1. **新 ID 来自 IP=250 AI 专属段**：
   - BulletConfig 320032 → **2500001**
   - ModelConfig 3200088 → **25000001**
2. IR YAML + SkillGraph JSON 各 4 处替换（共 8 处）
3. Lint pass：E=0 W=1（W003 与本修复无关）
4. 全工程 cross-check：`BulletConfig_2500001` / `ModelConfig_25000001` 仅 30214005 一处；`320032` / `3200088` 仅 30222005 一处 / 全工程剩余重复 BulletConfig/ModelConfig = **0 条**

## 沉淀（推广动作）

### A. skill-designer agent 加铁律
[.claude/agents/skill-designer.md](../../.claude/agents/skill-designer.md) 新增第 8 节"配 ID 类节点必先全工程唯一扫描"段，明确：
- BulletConfigNode / ModelConfigNode / SkillTagsConfigNode / SkillEffectConfigNode 等 ConfigBaseNode 子类节点 = **常规节点 / 全工程 ID 唯一**
- AI 生成时**永远使用 IP=250 AI 专属段**，绝不抄样本 ID 直接当 ID 用
- 抄样本只允许抄"参数模板"，**抄到 ID 字段必须替换为新 ID**

### B. SKILL.md GATE-0.5 扩展
[.claude/skills/skill-design/SKILL.md](../../.claude/skills/skill-design/SKILL.md) GATE-0.5 三层枚举校对增加"全工程 ID 占用扫描"步骤，输出占用列表与即将分配的 ID 对比。

### C. skill_compiler.py v2.6（待 v2.6 PR）
- `_scan_global_used_ids` 扩展扫描 `BulletConfigNode` / `ModelConfigNode`
- IdAllocator 引入 `AI_IP_SEGMENT = 250` 常量 / BulletConfig/ModelConfig 自动从 IP=250 段分配
- 持久化缓存（同 #021 推广动作 1）

### D. curator Mode B 提案（GATE-MENTAL-OUT）
升 candidate 不变量 **D-035X**：
> "配 ID 类节点（BulletConfig / ModelConfig / SkillEffectConfig / SkillTagsConfig 等 ConfigBaseNode 子类）必须先做全工程 ID 唯一性扫描；AI 生成永远从 AIGeneratorConfig.AIIpSegment（默认 250）IP 段分配；引用节点 RefConfigBaseNode 跨图复用合法但 AI 不主动跨图引用 BulletConfig/ModelConfig（业界惯例 0 用例）"
>
> 证据：[AssetThirds/NodeEditor/Datas/ConfigIDManager.cs:518-540](../../Assets/Thirds/NodeEditor/Datas/ConfigIDManager.cs) + [JsonGraphManager.cs:443-468](../../Assets/Thirds/NodeEditor/Datas/JsonGraphManager.cs) + [TableAnnotation.json](../../Assets/Thirds/NodeEditor/SkillEditor/Saves/TableAnnotation.json) + [AIGeneratorConfig.json](../../Assets/Thirds/NodeEditor/SkillEditor/Saves/SvnIgnore/AIGeneratorConfig.json) + 30222005/30214005 撞 ID 实证 + 火宗 25 SkillGraph 0 跨图引用 BulletConfig/ModelConfig fs 真扫

## 利
- 兑现 #021 v2.6 待办（BulletConfig/ModelConfig 全工程唯一）
- 引入 AI 专属 IP 段命名空间 / 永久消除 AI 生成与人类策划 ID 撞车风险
- AI 工作守则升级：3 层防线（agent 铁律 + SKILL.md GATE-0.5 + compiler IdAllocator 自动跳）

## 弊
- compiler v2.6 PR 未跟 → 当前修复是手动选 ID（下次 AI 生成 BulletConfig/ModelConfig 仍需手动确保 IP=250 段且累加序号 / 避免和已分配 IP=250 段冲突）
- 启动扫盘开销随 BulletConfig/ModelConfig 加入会继续增加（#021 已 9 秒 / 加入两类预计 +2 秒）

## 噪音风险
低 — 改产物拓扑 0（仅 ID 数字替换） / 改 mental_model 工作流 +1 条不变量

## 历史教训

### #021 留的"待 v2.6"成了 #035 的真踩坑
当时判断"BulletConfig/ModelConfig 跨文件重复不一定是 bug"是部分对的（合法情况 = 多技能 RefConfigBaseNode 引用同一 BulletConfig），但漏说了**部分错的**那半："AI 自动生成 BulletConfigNode 时如果 ID 是抄来的，必撞"。

**教训**：PostMortem 留"待办"时必须明确"在 v2.6 之前 AI 必须临时手动遵守 X 规则"——否则 AI 不知道留的待办意味着自己当下要怎么避坑。

### AI 生成器有专属 IP 段但 AI 不知道
`AIGeneratorConfig.AIIpSegment = 250` 是项目早就预留的安全区，但 mental_model / agent prompt 都没沉淀这条 → AI 凭直觉抄样本 ID 撞车。

**教训**：项目预留的"AI 专属"配置（如 AIIpSegment / AICounter*）必须在 mental_model 显式登记 + agent prompt 引用，不然预留 = 浪费。
