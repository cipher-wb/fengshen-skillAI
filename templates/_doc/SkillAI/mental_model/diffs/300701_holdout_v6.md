# 300701 hold-out v0.6 DIFF

**focus**: 样本 1 - drift 检测：D-501 SubType ⊥ Mode 矩阵在 SubType=303 内更多 Mode 上的泛化

## 真值（开卷）

- node_count: 98（与 corpus_scan 一致）
- SkillConfigNode: 1 个（IsTemplate=False）
- 顶层 SkillConfig：ID=300701, **SubType=303, MainType=3, CdType=0, CdTime=360, EnhanceID=0, Icon=""**
- **Active.SkillEffectConfigID = 108003035 ≠ 0**
- **Passive.SkillEffectConfigID = 0**
- → **Mode A 纯 Active**
- BulletConfig=3 (1080120 / 1080121 / 1080123) | ADD_FORCE=2 | SET_COLL=4 | CREATE_ROLE=1 | ORDER=14 | DELAY=6 | REPEAT=3
- RUN_TEMPL=3：调用模板 **136000097（屏幕扭曲特效）/ 136000098（屏幕Layer默认）/ 136000097**（重复）→ 屏幕特效演出，**非伤害模板**
- 高频意外节点：TSKILLSELECT_CIRCLE × 3 / TSET_GET_ORIGIN_SKILL_ID × 4 / TSET_MODIFY_ENTITY_STATE × 6（演出节点 / 法宝实体状态切换）

## 预测 vs 实际

| 维度 | 预测 | 实际 | 评分 |
|------|------|------|-----|
| 节点数 | 98 | 98 | **1.0** |
| 拓扑 | Mode A + 14 ORDER + ADD_FORCE + bullet × 3 + DELAY × 6 + SET_COLL × 4 + REPEAT × 3 + CREATE_ROLE | 全部命中 + 额外 SkillSelect_Circle × 3 / GET_ORIGIN_SKILL_ID × 4 / MODIFY_ENTITY_STATE × 6 | **0.875** |
| 模板 | 175xxx / 1900164xx 三联包 / 44xxx / 18-22xxx | 实际 **136000097/098 屏幕扭曲特效** — **字典外段位 136xxx**！未命中预测 | **0.25** |
| 子系统 | SkillEntry / 模板 / 实体碰撞 / 子弹 / 控制流 / SkillTag 6 个 | 全部命中 | **1.0** |

**sample_score = (1.0 + 0.875 + 0.25 + 1.0) / 4 = 0.781**

## D-501 KPI（核心）

| KPI | 预测 | 实际 | 命中 |
|-----|------|------|-----|
| Mode 预测 | Mode A 纯 Active | Mode A 纯 Active (Active=108003035 / Passive=0) | ✓ |
| SubType=303 内并存 Mode | A 候选高 | A 验证 | ✓ |

**SubType=303 矩阵**（v0.6 D-501 累计 + 本 hold-out）：
- B-005 308071 = Mode A
- B-004 308072 = Mode E
- holdout-v0.5 30073901 = Mode C
- **holdout-v0.6 300701 = Mode A**（第 2 印证 Mode A）

→ **D-501 SubType=303 内 3 种 Mode 并存全部观察**（A / C / E），**无锁定单一模式**。**矩阵泛化 KPI 100% 命中**。

## drift 风险归因

### 真 drift 信号：模板段位字典外（136xxx）

**新现象**：300701 调用 136000097/098（屏幕扭曲 layer 演出特效），**v0.6 模板系统 §段位字典 9 段（14xxx / 175xxx / 18xxx / 186xxx / 19xxx / 22xxx / 28xxx / 38xxx / 44xxx / 66xxx / 146xxx / 190xxx / 220xxx / 225xxx / 308xxx）均未含 136xxx**。

文件名揭示语义：`SkillGraph_屏幕Layer屏幕扭曲.json` / `SkillGraph_屏幕Layer默认.json` —— **136xxx = 屏幕特效演出模板段**，专用于法宝/技能视觉演出。

**影响**：
- 模板系统 §段位字典需扩补 136xxx（演出反馈 / 屏幕特效）
- 与 hold-out v0.5 30073901 GAME_SPEED_CHANGE / CAMERA_SHAKE 等"演出反馈原语家族"主张协同——演出原语 + 演出模板段位是连续的认知盲区

### 非 drift（认知保持稳定）

- D-501 矩阵 SubType=303 内 Mode A 第 2 印证（无 drift 复发）
- D-508 决策树正确分类类别 1 技能（即使法宝目录）
- 入口模式 5 类预测 100% 命中（重大成功 — v0.5 hold-out drift 100% 修复保持）
- 子系统命中率 6/6（无遗漏 / 无误增）

## 子系统页延伸

### 模板系统（候选 delta）

- §段位字典扩补 **136xxx**（演出反馈 / 屏幕特效层模板段，专用于法宝大招/技能视觉演出）
- §仍不确定 / §模板组合模式：**屏幕 Layer 模板 = 法宝/技能演出标准范式？需 B-006 扫描 corpus 多样本量化**

### SkillEntry 系统

- §SubType × Mode 矩阵 SubType=303 行 **Mode A 加印证 300701**（已有 308071 第 1 印证 + 现 300701 第 2 印证）

## 引用

- 真值文件：`{{SKILLGRAPH_JSONS_ROOT}}法宝/SkillGraph_300701_葫芦.json`
- 预测：`predictions/300701_holdout_v6.yaml`
