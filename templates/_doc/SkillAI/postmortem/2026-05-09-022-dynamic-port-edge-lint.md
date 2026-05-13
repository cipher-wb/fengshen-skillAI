---
type: 复盘页
summary: 旋转扩张子弹圈模板"很多节点没连线"的根因排查 + skill_lint 加 E020/W006 防线
date: 2026-05-09
tags: [PostMortem, lint, dynamic-port, builder, 反向反思]
---

# PostMortem #2026-05-09-022 — Dynamic Port 出边自检 + 双根模板视觉澄清

## 触发

用户在 Unity SkillEditor 打开 `SkillGraph_【模板】旋转扩张子弹圈.json` 后反馈：
> 为什么我打开模板看到有很多节点都没有连线

接力的主流程 agent 直接把问题归因到 **PostMortem #001 经典症状**——dynamic port 节点（ORDER/REPEAT/NUM_MAX/NUM_MIN）出边 outputPortIdentifier 必须为 "0"，并要求红队 agent：

1. 在 builder 里加 `TSET_REPEAT_EXECUTE` 到 dynamic port 名单
2. 重生成 JSON，期望从 7 个 dynamic 节点出去的边全部 outputPortIdentifier="0"

---

## 调查结果（与接力诊断不一致）

### 红队的求证步骤

**Step 1 — 复核 skill_compiler 权威名单**：

[skill_compiler.py:2663](../tools/skill_compiler.py#L2663) 上的 `DYNAMIC_PORT_NODES = {"TSET_ORDER_EXECUTE", "TSET_NUM_MAX", "TSET_NUM_MIN"}` —— **没有 REPEAT**。

skill-design SKILL.md L363 上也明确写：
> "TSET_ORDER_EXECUTE 是 dynamic port — 所有出边的 outputPortIdentifier 必须是 `'0'`（编译器已处理）"

只是 ORDER。

**Step 2 — 真实样本统计**（3573 个真实 SkillGraph 文件）：

| outputPortIdentifier | 出现次数 | 含义 |
|---|---|---|
| `'0'` | 62 | 边角案例（可能 REPEAT 子效果配在 Params[0]，但 schema 上 Params[0]=间隔帧不是子效果） |
| `'1'` | 306 | 一些样本把"次数"当 dynamic 子效果 |
| **`'3'`** | **3337** | **绝对多数 = 子效果在 Params[3]** |
| `'4'` | 1290 | 中断/筛选 |
| `'5'` | 265 | |
| `'7'` | 95 | |

涉及 1415 个使用 REPEAT 的 SkillGraph，**全部都用 Params 索引而非"0" 锚点**。

进一步抽样真实样本 30212010（叶散风行，rotating 模板的参考样本）：6 条 REPEAT 出边，outputPortIdentifier 取 "1"/"3"/"4"/"5"，**没有一条是 "0"**。

**结论**：REPEAT_EXECUTE 不是 dynamic port，它有固定 schema（间隔帧 / 次数 / 立即 / 子效果 / 筛选 / 中断 / ...），出边按 Params 索引正确。接力诊断错误。

### 真正的视觉悬空根因

进一步对 `SkillGraph_【模板】旋转扩张子弹圈.json` 做拓扑分析：

| 指标 | rotating | fan_layered（视觉已验证 OK 的对照） |
|------|----------|-----|
| 节点数 | 61 | 347 |
| 边数 | 77 | 523 |
| **完全悬空节点数** | **0** | **0** |
| 仅无入边节点（roots） | 2 | 1 |
| 仅无出边节点（leaves） | 9 | 18 |

可达性 BFS（从两个根 BFS 求并集）：

- 模板根 32300001 可达 29 个非 SkillTag 节点
- OnTick init 根 32300101 可达 24 个非 SkillTag 节点
- 53 个非 SkillTag 节点 = 29 + 24（**无重叠，全部可达**）

**rotating 模板设计上是双根**（在 [build_rotating_expand_bullet_ring_template.py:709-851](../tools/builders/build_rotating_expand_bullet_ring_template.py#L709-L851) 注释明确说明）：调用方需要把 OnTick init effect ID=32300101 手动配到 BulletConfig.AfterBornSkillEffectExecuteInfo。这是设计意图，不是 bug。

**真正的"很多节点没连线"主因有 3 种可能**（用户没贴图 / 没用屏幕标注，红队只能推断）：

1. **SkillTagsConfigNode 节点（8 个）**：定义节点，画布上只有"被引用"的入边，没出边——这是 SkillEditor 的固有显示形式，每个其他模板都一样
2. **OnTick 子图独立成支**：用户在画布上看到 OnTick init 32300101 那 24 个节点和模板根 32300001 那 29 个节点之间没有任何连线（设计如此），看起来像"两块独立的部分"
3. **节点位置策略 x=0 单列**：所有节点 y 递增堆叠成一长条（同 fan_layered 模板），编辑器需要手动 Tab+布局优化才能看清

---

## 新规则 / 防线

虽然 builder 没 bug，但这次踩坑暴露了**未来策划/AI 仿写 builder 时极易踩**的两件事：

### 规则 1：E020 — Dynamic Port 出边强制 "0"

**新规则**：skill_lint.py 加 E020 — 任何动态端口节点（TSET_ORDER_EXECUTE/TSET_NUM_MAX/TSET_NUM_MIN）的出边 `outputPortIdentifier` 必须等于 `"0"`。

**根因**：动态端口节点在编辑器里只暴露一个锚点端口 "0"，所有 Params 共用。出边写成 "1"/"2"/... 会让编辑器加载时丢边——**画布上看不到边但 JSON 里有，运行时仍正确**——这就是接力消息描述的"视觉悬空但数据正常"症状。

**REPEAT/DELAY/CONDITION/SWITCH 等不在此名单**：它们有固定 schema，子效果/case/分支在固定的 Params 索引上，出边用索引值正确（参考 30212010 等真实样本）。

**实现**：[skill_lint.py:613-633](../tools/skill_lint.py)（`check_e020_dynamic_port_edge`）。

**护栏验证**：手动注入故障（把 rotating 所有 ORDER 出边改成 "1"）→ Lint 输出 18 条 E020 ERROR，干净拦截。

### 规则 2：W006 — 完全孤立节点告警（降级为可选）

**新规则草案**：节点既无入边也无出边，又不属于 SkillTagsConfigNode/RefConfigBaseNode/SkillConfigNode/BulletConfigNode/SkillInterruptConfigNode/IsTemplate=true 这些合法 isolate cls，则告警 W006。

**根因**：策划仿写 builder 时常漏写 Params 引用导致编译器没建出边——节点写在 refs 里但孤儿化。

**实现**：[skill_lint.py](../tools/skill_lint.py)（`check_w006_isolated_node`，函数已实现但**默认未注册到 lint_file**）。

**降级原因（实测）**：把 W006 加进默认管线后，在 `{{SKILLGRAPH_JSONS_ROOT}}技能模板` 目录递归 lint **产生了 30 条假阳性**——这些子模板大量使用"外部连线引用"模式（节点放画布上但通过跨文件 Effect 数字 ID 引用，画布上看不到边）。代表案例：`TSET_PROC_DAMAGE_66001191 ID=146003932`，Desc 直白写着"外部连线直接引用的该节点"。

**当前状态**：函数保留，调用语句已注释。仅在 builder 新建模板时手动 `check_w006_isolated_node(graph, refs, report)` 调用，避免污染默认 lint 管线。

**rotating 模板验证**：默认管线 E=0 W=0 PASS。E020 在故障注入测试下捕获 18 条 ERROR。整个 templates 目录递归 E020/W006 假阳性 0 条。

---

## 反向反思（最重要的一条）

**接力诊断错误本质**：把"凡是用户说画布有问题 → 一定是 dynamic port 问题"当成默认假设，没先验证 REPEAT 是否真的属于 dynamic port 名单，也没先做拓扑分析判断到底有多少节点真孤立。

**红队应有的反应（已做到）**：
1. 不直接照单全收"修 builder"的指令
2. 先用 3573 个真实样本统计 REPEAT 出边的实际分布
3. 对 rotating 模板做完整可达性分析，确认所有节点都连得好好的
4. 推断真正的视觉误读来自"双根模板设计"
5. 即便 builder 没错，仍然把"防止以后写错"的低成本 lint 规则加上

**这条反思要沉淀到 SKILL.md GATE-0.5 还是 GATE-3.5**：
- GATE-0.5 已有"先验研究找 3 个真实样本"——这次要补"接到任务先验证主流程的诊断是否成立，不要照单全收"
- 推荐沉淀位置：`memory/feedback_skill_compiler_pitfalls.md` 加一条"接力消息的诊断也要先求证再修"

---

## 建议沉淀位置

- [x] **doc/SkillAI/tools/skill_lint.py** — 已固化为 E020 / W006（v2.5）
- [ ] **doc/SkillAI/docs/易错点速查.md** — 加一条"REPEAT 不是 dynamic port，它的 Params 索引出边用 '3'/'4'/'5'/...是合法的"
- [ ] **memory/feedback_skill_compiler_pitfalls.md** — 加一条"接到接力任务先验证诊断"
- [ ] **`.claude/skills/skill-design/SKILL.md`** GATE-0.5 — 补一句"接力消息的诊断要先用真实样本验证"

## 利 / 弊 / 噪音风险

**利**：
- E020 是绝对正确的硬规则——以后任何 builder 误把 ORDER 出边写成非 "0" 立刻被挡
- W006 在策划仿写 builder 时漏写 Params 引用的场景下能立刻报警
- 反向反思机制本身有价值（避免对接力消息盲信）

**弊 / 噪音风险**：
- W006 对"工具子图根"友好（必须是 IsTemplate=true 才豁免）——如果未来有"既非 IsTemplate 也无入边"的合法工具子图，要么改成 IsTemplate=true，要么扩大 EXEMPT_CLS 名单。**风险评估：低**——目前所有真实样本的工具子图都通过 IsTemplate=true 标记。

## 决定项

- [ ] 入库（保留 E020 + W006，文档/memory 暂不更新）
- [ ] 入库 + 补 docs/易错点速查.md REPEAT 条目
- [ ] 入库 + 补 memory + SKILL.md GATE-0.5 反向求证规则
- [ ] 修改后入库（建议改成：...）
- [ ] 部分入库（指定要保留哪些）

## 索引登记

- 编号：2026-05-09-022
- 状态：待用户决定
- 已生成的代码护栏：[skill_lint.py](../tools/skill_lint.py) E020 + W006（已通过故障注入测试 + rotating/fan_layered 回归 PASS）

## 交叉引用

- [[2026-05-08-005-firstpass-quality]] — 流程纪律（GATE-0.5 / GATE-3.5）
- [[2026-05-08-007-boomerang-redesign]] — derive_edges 修生命周期边丢失（同样涉及"边可达性"）
- [[../tools/skill_lint]] — 实现位置
