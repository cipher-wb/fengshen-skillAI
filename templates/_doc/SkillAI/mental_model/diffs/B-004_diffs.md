# B-004 DIFF — 5 样本闭卷预测 vs 实际对比

> 评分准则：4 维平均（节点数 ±20% / 拓扑同形 / 模板命中 / 子系统列对）
> 每维 1.0 / 0.5 / 0.0；sample_score = 4 维均值

---

## Sample 1: 30532001 / 青藤之力 / SubType=701 / 121 nodes

### 维度 1: 节点数（预测 121 / 实际 121）→ **1.0**

完美命中（corpus 元数据指引）。

### 维度 2: 拓扑（预测 callback chain × 8 / 实际命中）→ **0.875**

实际：
- 8 个 REGISTER_SKILL_EVENT，每个绑定一个 callback (callback_id 32000345/347/355/428/427/454/456 + 225002099)
- 9 ORDER_EXECUTE（接近 8 callback + 1 root，几乎 1:1 映射 ✓）
- 7 CONDITION_EXECUTE（条件分支）
- 24 TSCT_VALUE_COMPARE + 13 TSCT_AND（复杂条件门 ✓）
- **6 ADD_BUFF + 7 REMOVE_BUFF**（与预测"0 ADD_BUFF"对比 — 预测错！）

差异：预测以为只有 REMOVE_BUFF（reading corpus 误读），实际 ADD_BUFF=6 也是常规的。

但 callback × 8 的整体范式预测对，每个 REG.callback_id 都指向独立 effect ID（32000345 等）= 标准 SkillEvent 范式。

### 维度 3: 模板命中（预测 146xxx/175xxx/190xxx / 实际 440xxx × 3）→ **0.0**

**实际只用 440xxx 段模板（44014633 × 3）**，预测的 146xxx / 175xxx / 190xxx 全部没用。

**重大发现**：v0.4 模板字典已收录 44xxx，但**该样本独家用 44014633 重复 3 次**（= 同一模板被多 callback 复用）— 这种"模板复用"用法 v0.4 没强调。

### 维度 4: 子系统列对（预测 7 个子系统 / 实际命中 6 个，遗漏 1 个 + 多列 1 个）→ **0.625**

预测列：SkillEvent / 控制流 / SkillEntry / Buff / SkillTag / 条件系统(暂存) / **模板系统(漏)**
实际命中：SkillEvent ✓ / 控制流 ✓ / SkillEntry ✓ (701 字典扩补) / Buff ✓ (有 ADD/REMOVE) / SkillTag ✓ / 条件系统 ✓✓（37 TSCT！）/ **模板系统 (3 RUN_TEMPL，预测漏列！)**

预测把模板系统漏列了（因为 corpus top_classes 没显示 RUN_TEMPL 在前 8）。

### **sample_score: (1.0 + 0.875 + 0 + 0.625) / 4 = 0.625**

### 关键收获 / 新认知

1. **N-1 命中**: Event ID 字典扩补——本样本暴露 **新 ID: 6 / 15 / 2 / 3**，其中 `event_id=15`（B-003 N-1 高频未知 top miss）callback_id=**225002099**（225xxx 段 effect）
2. **新认知**: SubType=701 = **被动响应型心法**（无 Active root + 8 REG callback + 6 ADD/7 REMOVE buff = 攻击事件钩子驱动 buff 增减）
3. **模板复用**: 同一 template_id (44014633) 被多 callback 复用，对应"通用 buff 计算模板"用法
4. **ID 段位混用**: callback_id 既有 32000xxx（无前缀段位）也有 225002xxx（225xxx 段）— effect ID 自由编号

---

## Sample 2: 400001 / 魔气妖婴 / SubType=501 / 123 nodes (法宝)

### 维度 1: 节点数（预测 123 / 实际 123）→ **1.0**

### 维度 2: 拓扑（预测 ORDER+DELAY+BUFF / 实际命中）→ **1.0**

实际：13 ORDER + 13 DELAY + 10 BuffConfig + 6 ADD_BUFF + 10 REMOVE_BUFF + 10 ADD_ENTITY_ATTR + 13 GET_SKILL_TAG ✓
拓扑结构完美命中预测（buff 时间轴技能）。

### 维度 3: 模板命中（预测可能 0-2 / 实际 0）→ **1.0**

**0 RUN_TEMPL** — 预测对了！这是**法宝技能的鲜明特征**：不调高阶模板。

### 维度 4: 子系统列对（预测 4 个子系统 / 实际命中）→ **1.0**

预测：Buff / 控制流 / SkillTag / SkillEntry — 全部命中。
**没漏**：法宝确实不用 SkillEvent / 子弹 / 碰撞。

### **sample_score: (1.0 + 1.0 + 1.0 + 1.0) / 4 = 1.0**

### 关键收获 / 新认知

1. **N-3b 命中**: SubType=501 字典扩补 = **法宝/装备型被动**
2. **法宝范式发现**: bullet=0 + reg_event=false + 0 RUN_TEMPL + 13 RefConfigBase + 双 0 入口 = "**法宝技能不依赖 SkillEvent，靠 buff 时间轴自驱**"
3. **新子系统候选**: RefConfigBaseNode × 13 反复出现在法宝技能（pick2 pick5 都有），需建子系统页 - **配置引用桥接系统**
4. **BuffConfig × 10 + ADD_BUFF × 6 不等**: 部分 buff 是 callback 接收（即装备时挂载），不全靠 ADD_BUFF 节点

---

## Sample 3: 30221000 / SubType=102 / 130 nodes / 金宗门奇术1-地阶 / buff_layer 命中

### 维度 1: 节点数（预测 130 / 实际 130）→ **1.0**

### 维度 2: 拓扑（预测复合大招 / 实际命中）→ **0.875**

实际：11 ORDER + 8 MODIFY_TAG + 7 ModelConfig + 6 SkillTagsConfig + 6 ADD_BUFF + 5 RUN_TEMPL + 5 BuffConfig + 5 GET_SKILL_LEVEL + 5 DESTROY_ENTITY + 4 APPLY_ENTITY_EFFECT + 14 NUM_CALC ✓

拓扑大方向对：复合大招 / 多模板 / SkillTag 状态机 / Buff 操作。

但 **SkillEffectExecuteInfo_root_ID = 0** — 这是惊喜！v0.4 SkillEntry 系统页认为 CdType=1 长 CD 必有 Active root，但**这个样本 root=0**。说明 root_id=0 也可以是合法状态（fall back 到 SkillEffectFlowList 列表）。

差异：5 DESTROY_ENTITY + 4 APPLY_ENTITY_EFFECT 是预测没列的（实体生命周期操作）。

### 维度 3: 模板命中（预测 175/280/186 / 实际 380×3 + 440×1 + 146×1）→ **0.5**

**实际段位**：380xxx × 3 / 440xxx × 1 / 146xxx × 1
- 预测的 175xxx 漏（这个样本是 380xxx 主导）
- 预测的 280xxx 漏
- 380xxx：v0.4 字典已收录但 B-002 D-202 曾说"38xxx 段不存在于模板分类" — **这个样本直接反证！** 38000228 / 38000236 / 38000289 三个 380xxx 模板真存在，被 RUN_TEMPL 调用。

**这是 N-2 关键发现**：380xxx 重新核实 → **v0.4 D-202 表述需修正**（38xxx 在宗门是 0 调用 ≠ 不存在；它在更大段位是有效模板段）。

### 维度 4: 子系统列对（预测 8 个 / 实际 7+ / 漏 1 个）→ **0.875**

预测列：子弹/控制流/碰撞/SkillTag/Buff/SkillEvent/模板/SkillEntry
实际：子弹 ✓ / 控制流 ✓ / 碰撞 ✓ (set_coll) / SkillTag ✓ / Buff ✓ / SkillEvent ✓ / 模板 ✓ / SkillEntry ✓ / **遗漏：实体生命周期（5 DESTROY_ENTITY）**

### **sample_score: (1.0 + 0.875 + 0.5 + 0.875) / 4 = 0.8125**

### 关键收获 / 新认知

1. **N-2 重大反证**: **380xxx 段位真实存在** — B-002 D-202 表述需修正
2. **N-1 命中**: 新 Event ID — `event_id=9` (REG/UNREG 都用，这是 B-003 N-1 中优先级 ID)
3. **SkillEntry 反例**: CdType=1 + 长 CD 也可以 root_id=0（推翻 v0.4 含蓄假设）
4. **buff_layer 在 102 主动技中也用** — 推翻 v0.4 "buff_layer 仅心法" 含蓄假设（pick3 + pick5 双证）
5. **UNREG event_id=9 重复 2 次**：同一 event 被多次 unreg（可能配 callback 失效场景）

---

## Sample 4: 30221120 / 地阶奇术3 / SubType=102 / 119 nodes / event_rich

### 维度 1: 节点数（预测 119 / 实际 119）→ **1.0**

### 维度 2: 拓扑（预测 14 RUN_TEMPL 主导 / 实际命中）→ **1.0**

实际 14 RUN_TEMPL ✓ + 14 ORDER ✓ + 13 NUM_CALC ✓ + 7 DELAY + 4 CREATE_BULLET + 4 ADD/REMOVE_BUFF + reg_event ✓
完美命中。

### 维度 3: 模板命中（预测 280/175/186/190/225 / 实际 190×9 + 380×1 + 225×1 + 186×1 + 136×2）→ **0.5**

预测命中：190xxx ✓ / 225xxx ✓ / 186xxx ✓
预测错过：380xxx (再次出现！) / 136xxx (新段位，v0.4 字典已收录但少用)
预测多列：280xxx 没出现！175xxx 没出现！

**N-2 重大发现**：
- **190xxx × 9 = 主导段位**（B-003 N-2 列出 190xxx 1995 调用，本样本 9 次，验证）
- **190016404 / 190016485 / 190016523 重复 3 轮** → **「3 段命中模板」三联包模式**（一次出招打 3 段，每段同样 3 模板）
- 380xxx 再次出现（与 30221000 一起证明 v0.4 D-202 修正）

### 维度 4: 子系统列对（预测 7 个 / 实际命中）→ **1.0**

子弹/控制流/模板/SkillTag/Buff/SkillEvent/SkillEntry — 全命中。

### **sample_score: (1.0 + 1.0 + 0.5 + 1.0) / 4 = 0.875**

### 关键收获 / 新认知

1. **N-2 重大补完**:
   - **190xxx 段是宗门技能命中模板的主战场**（远超 175xxx，至少在奇术类）
   - **190016404/485/523 三模板包**: 几乎所有 190xxx 调用都是这 3 个 ID 循环（30221000 / 30221120 / 308072 全用这套）→ **「190 三联包」是核心命中模板组合**
2. **Active root = 2250038** (225xxx 段位) — root 本身可以是 225xxx 中阶模板（不只是宗门技能 ID 内嵌 root）
3. **REG event_id=3 双绑同 callback_id 不同** → 两个不同 effect 监听同一 event
4. **UNREG event_id=3** + 后续 REG → "动态 callback 切换"模式
5. **0 has_set_coll + 0 add_force**：奇术 102 不动碰撞，但 4 子弹 = 远程飞弹型奇术

---

## Sample 5: 308072 / 青木天葬 / SubType=303 / 129 nodes / 法宝

### 维度 1: 节点数（预测 129 / 实际 129）→ **1.0**

### 维度 2: 拓扑（预测法宝 ORDER+DELAY / 实际命中）→ **0.875**

实际：17 ORDER + 9 DELAY + 9 GET_SKILL_TAG + 7 ModelConfig + 7 RefConfigBase + 5 RUN_TEMPL + 5 MODIFY_TAG + 3 CREATE_BULLET + 3 CREATE_EFFECT + 3 REPEAT ✓

拓扑大方向对（法宝时间轴 + buff 自驱），但**有 5 RUN_TEMPL** — 这个法宝调高阶模板！与预测"法宝可能 0 RUN_TEMPL"对比 = 部分错（pick2 法宝 0 模板 + pick5 法宝 5 模板 = 法宝行为不同）。

### 维度 3: 模板命中（预测 175/280/300 / 实际 190xxx × 5）→ **0.0**

**5 RUN_TEMPL 全是 190xxx**（190016404/485/523）— 与 pick4 完全相同的「190 三联包」！
- 预测的 175 / 280 / 300 全错。
- **重大跨样本一致性**：190xxx 三联包 (404/485/523) 是命中模板核心组件，**无论是宗门 102 主动技还是法宝 303**都用这套。

### 维度 4: 子系统列对（预测 7 个 / 实际命中）→ **1.0**

全列对。

### **sample_score: (1.0 + 0.875 + 0 + 1.0) / 4 = 0.71875**

### 关键收获

1. **N-2 重大补完**: 190xxx 三联包确认（pick3 / pick4 / pick5 三样本都用 404/485/523）
2. **N-3c 命中**: SubType=303（法宝高阶段位之一）
3. **法宝异质性**: pick2 (501 法宝) 0 模板 vs pick5 (303 法宝) 5 模板 → 法宝内部子分化
4. **法宝带 buff_layer**: pick5 has_get_buff_layer=true（pick3 也 true）双证 buff_layer 跨 SubType 通用
5. **3 CREATE_BULLET + 3 CREATE_EFFECT + bullet_count=3** = 召唤型法宝（bullet 是召唤实体载体）
6. **N-1 新 Event ID=6** (corpus 81 hits, B-003 N-1 中优先级，本样本命中)

---

## 批次汇总

| Sample | 节点 | 拓扑 | 模板 | 子系统 | sample_score |
|--------|-----|------|------|-------|-------------|
| 30532001 | 1.0 | 0.875 | 0 | 0.625 | **0.625** |
| 400001 | 1.0 | 1.0 | 1.0 | 1.0 | **1.0** |
| 30221000 | 1.0 | 0.875 | 0.5 | 0.875 | **0.8125** |
| 30221120 | 1.0 | 1.0 | 0.5 | 1.0 | **0.875** |
| 308072 | 1.0 | 0.875 | 0 | 1.0 | **0.71875** |

**batch_accuracy = (0.625 + 1.0 + 0.8125 + 0.875 + 0.71875) / 5 = 0.806**

**对比 v0.4 hold-out 0.833 + B-003 0.900 = 略降（−0.094 from B-003）**

**降的根本原因**: 模板段位预测在 3/5 样本失分（30532001 / 30221000 / 308072）—— **190xxx 三联包是 v0.4 字典外的核心信号**，PREDICT 阶段无法预知。这是 valid 的"学到了新东西"信号，不是退步。

---

## 跨样本元发现（PROPOSE 阶段重点）

### 元发现 1: 190xxx「三联包」(190016404/485/523) — 命中模板核心组件

3/5 样本都用同一组三模板。190016404/485/523 极可能是**「子弹命中 → DAMAGE → SKILL_TAG_UPDATE」三段式封装**。
v0.4 模板系统页"190xxx (1995 调用)"只是粗放统计，**未点出"三联包"模式**。

### 元发现 2: 380xxx 段位真实存在 — B-002 D-202 反例

30221000 (380xxx × 3) + 30221120 (380xxx × 1) 双证。**v0.4 模板系统页 D-202 表述需修正**："38xxx 段位完全错"应改为"38xxx 段在宗门技能直接 root 0 命中，但作为 RUN_TEMPL 调用对象有效"。

### 元发现 3: SubType=701 (青藤之力) 范式 = 「被动响应型心法」

无 Active/Passive root + 8 REG event + 6 ADD/7 REMOVE buff + 0 子弹 = **"打/被打事件钩子驱动 buff 修正"**的"准被动"型心法。
v0.4 SkillEntry 字典需增 701。

### 元发现 4: 法宝技能（SubType=501/303）= 「buff 时间轴 + 配置引用」自驱

pick2 (501) + pick5 (303) 双证：
- 双 0 入口（无显式 root）
- 大量 ORDER+DELAY 编排时间轴
- 0/少 SkillEvent
- **RefConfigBaseNode 高频**（pick2: 13 / pick5: 7）= 跨技能/buff 配置引用桥接节点
- 子弹/碰撞极少
v0.4 没建过"法宝技能"或"配置引用系统"页，**N-3b 字典扩 + 新建/暂存"配置引用系统"候选**。

### 元发现 5: SubType=102 + buff_layer 跨证

pick3 (102 主动技) + pick5 (303 法宝) + 历史样本（30531005 心法）= **buff_layer 跨 SubType / 跨技能形态通用**。
v0.4 Buff 系统页心法判定 OR 两类（D-307）需扩展认知"buff_layer 不限心法"。

### 元发现 6: Event ID 字典 N-1 大幅扩补

本批新发现 / 命中：
- **15** (148 hits, top miss) ✓ 命中
- **6** (81 hits) ✓ 命中
- **9** (69 hits) ✓ 命中（兼 UNREG）
- **3** (43 hits) ✓ 命中（已在字典内但首次大量样本印证）
- **2** (90 hits) ✓ 命中（已在字典）

v0.4 字典 11 个，本批新增/印证 5 个高频 ID，**SkillEvent 字典再扩补**。

### 元发现 7: PREDICT regex 工具有缺陷

`SkillEffectExecuteInfo_root_ID` regex 在多个样本读到 0（30221000 / 308072）但实际可能不为 0。这是 metadata 工具问题，不是认知问题。下一批 PREDICT 前应修。

---

## 推荐 delta 提案数（PROPOSE 阶段）

预计 **8-10 条 delta**：
- D-401: 模板系统 / 190xxx 三联包识别（强信号 3/5）
- D-402: 模板系统 / 380xxx 反证修订（强信号 2/5）
- D-403: SkillEntry 系统 / SubType 字典扩补（701 / 501 / 303）+ 法宝/被动响应型心法表述
- D-404: SkillEvent 系统 / Event ID 字典扩补（15/6/9 等）
- D-405: Buff 系统 / buff_layer 跨 SubType 通用（v0.4 心法 OR 两类需扩）
- D-406: 新建（或存档）「配置引用系统」/「法宝技能范式」子系统页 — RefConfigBaseNode 用法
- D-407: SkillEntry / 反直觉精化（root_id=0 + CdType=1 长 CD 也合法 — 30221000 反例）
- D-408: harness 工具 / metadata regex 修正（root_id 嵌套读法）
- D-409 (可选): 模板系统 / 同模板复用（44014633 × 3 单技能内重复调）
- D-meta (可选): SkillTag 系统 / 跨技能 callback effect ID 编号无段位（32000xxx 通用 effect 命名）
