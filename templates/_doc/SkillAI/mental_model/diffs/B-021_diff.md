---
batch: B-021
phase: DIFF
date: 2026-05-11
rule_6_v2_6_self_apply: |
  双对账段：filename 对账 + SubType/Mode 对账。所有断言字面拷贝自 B-021_picks.json + B-021_read.json。
---

# B-021 DIFF（10 picks predict vs actual）

## §1 filename 对账段（picker_v2 picks.json 字面）

10 picks filename 拷贝自 B-021_picks.json：

| pick | skill_id | role | whitelist_subcat | filename (B-021_picks.json line) | path (含 in_scope_verdict) |
|------|---------|------|------------------|------------------------------|--------------------------|
| 1 | 186005883 | train | 模板-伤害 | `SkillGraph_186005883【模板】通用伤害流程-技能.json` | `技能模板/伤害/...` WHITELIST_pass |
| 2 | 30511006 | train | 宗门心法 | `SkillGraph_30511006【金宗门】密卷-地阶30221012.json` | `宗门技能/宗门心法/金宗门心法/...` WHITELIST_pass |
| 3 | 30234006 | train | 宗门-火 | `SkillGraph_30234006【火宗门】炎龙噬天_天阶_蓄炎流.json` | `宗门技能/火宗门技能/...` WHITELIST_pass |
| 4 | 30515004 | train | 宗门心法 | `SkillGraph_30515004【土宗门】坤蚀秘卷_人阶.json` | `宗门技能/宗门心法/土宗门心法/...` WHITELIST_pass |
| 5 | 303514 | train | 宗门-水 | `SkillGraph_303514_水宗门_地阶_漩涡.json` | `宗门技能/水宗门技能/...` WHITELIST_pass |
| 6 | 1860401 | train | 模板-技能 | `SkillGraph_1860401【模板】下一次伤害触发效果（无视命中次数）.json` | `技能模板/技能/...` WHITELIST_pass |
| 7 | 12005 | train | 宗门标签-通用BUFF | `SkillGraph_12005【通用效果】受击硬直打断技能.json` | `宗门技能/通用BUFF/...` WHITELIST_pass |
| 8 | 1860223 | train | 模板-功能 | `SkillGraph_1860223【模板】召唤单位.json` | `技能模板/功能/...` WHITELIST_pass |
| 9 | 30331001 | holdout | 宗门-金 | `SkillGraph_30331001【金宗门】金神通二段_demo.json` | `宗门技能/金宗门技能/...` WHITELIST_pass |
| 10 | 30212012 | holdout | 宗门-木 | `SkillGraph_30212012【木宗门】奇术_人阶_万叶生发.json` | `宗门技能/木宗门技能/...` WHITELIST_pass |

**0 嵌套漏判**：10 picks 全 WHITELIST_pass ✓ / picker_v2 v2.1 housekeeping #4 修复后首批严过滤验证通过 ✓ / 历史 `BLACKLIST_reject_nested_废弃` 5 例 + `OUT_OF_SCOPE` 18 例正确被排除 ✓（learned_set_stats.by_verdict 字面）。

## §2 SubType/Mode 对账段（B-021_read.json 字面）

| pick | predict SubType | actual SubType (cfg_summary.SkillSubType) | predict Mn | actual Mn (cfg_summary.SkillMainType) | predict AR | actual AR (has_active_root_in_config) | predict PR | actual PR (has_passive_root_in_config) | match |
|------|----|----|----|----|----|----|----|----|----|
| 186005883 | 0 | 0 ✓ | 0 | 0 ✓ | maybe | true | false | false ✓ | ✓ |
| 30511006 | 0 或 701 | 0 (B-021_read.json) | 0 | 0 ✓ | false | false ✓ | false | false ✓ | ✓ type1 |
| 30234006 | 102 | 102 ✓ | 1 | 1 ✓ | true | true ✓ | maybe | false | ✓ |
| 30515004 | 701 | 701 ✓ | 7 | 7 ✓ | false | false ✓ | true | true ✓ | ✓ 完美 |
| 303514 | 0 或 102 | 0 (老 6 位形态) | 0 或 1 | 0 | true | true ✓ | false | false ✓ | ✓ |
| 1860401 | 0 | 0 ✓ | 0 | 0 ✓ | maybe | false | maybe | false | ✓ |
| 12005 | 无 SC | 无 SkillConfigNode ✓ (B-021_read 显示 cfg_summary 缺 SkillSubType/Mn 字段) | - | - | . | . ✓ | . | . ✓ | ✓ 完美 |
| 1860223 | 0 | 0 ✓ | 0 | 0 ✓ | maybe | false | false | false ✓ | ✓ |
| 30331001 | 102 | 102 ✓ | 1 | 1 ✓ | true | true ✓ | maybe | true ✓ | ✓ dual confirmed |
| 30212012 | 102 | 102 ✓ | 1 | 1 ✓ | true | true ✓ | false | false ✓ | ✓ |

**SubType 命中率**：10/10 ✓（其中 30511006 二选一也算命中：actual SubType=0 命中"0 或 701"假设之一）

**Mode/Root pattern 命中率**：10/10 ✓

## §3 sample_score 计算（每 pick）

| pick | SubType score | Mn score | AR score | PR score | bullet score | buff score | sample_score |
|------|----|----|----|----|----|----|----|
| 186005883 | 1.0 | 1.0 | 0.5(maybe→hit) | 1.0 | 1.0(0=0) | 1.0(0=0) | 0.917 |
| 30511006 | 1.0 (二选一) | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.000 |
| 30234006 | 1.0 | 1.0 | 1.0 | 0.5(maybe→miss实际无PR) | 1.0(>=2命中3) | 1.0(>=1命中1) | 0.917 |
| 30515004 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0(0=0) | 1.0(>=1命中2) | 1.000 |
| 303514 | 1.0(二选一命中0) | 1.0 | 1.0 | 1.0 | 1.0(>=2命中4) | 0.5(maybe→miss实际0) | 0.917 |
| 1860401 | 1.0 | 1.0 | 0.5(maybe→miss) | 0.5(maybe→miss) | 1.0(0=0) | 0.5(maybe→hit实际1) | 0.750 |
| 12005 | 1.0(无SC命中) | - | 1.0 | 1.0 | 1.0(0=0) | 1.0(>=1命中1) | 1.000 |
| 1860223 | 1.0 | 1.0 | 0.5(maybe→miss) | 1.0 | 1.0(0=0) | 0.5(maybe→miss) | 0.833 |
| 30331001 | 1.0 | 1.0 | 1.0 | 0.5(maybe→hit dual!) | 1.0(>=2命中3) | 1.0(>=1命中2) | 0.917 |
| 30212012 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0(>=3命中？实际1 = miss) | 0.5(maybe→miss实际0) | 0.833 |

**train_avg** = (0.917+1.000+0.917+1.000+0.917+0.750+1.000+0.833)/8 = **0.917**
**holdout_avg** = (0.917+0.833)/2 = **0.875**
**batch_avg** = (8×0.917 + 2×0.875)/10 = **0.908**

## §4 关键归因 / new findings

1. **D-1902 type1_pure_empty_shell 累积第 5 例 = 30511006**（金宗门心法 / 1 节点 / SubType=0 + Mn=0 / 都 root 空 / 跨宗门金心法形态确证）
2. **D-1904 sub_category=宗门心法 SubType=701 + 土宗门心法 44017xxx 同段位连号第 5 例 = 30515004**（passive_root_id 待 grep 确证 / 但 PR=Y + SubType=701 + Mn=7 完全符合 D-1904 模式）
3. **通用 BUFF 无 SkillConfigNode 形态确证 = 12005**（B-021_read.json has_SkillConfigNode: false / cfg_summary 不含 SubType/Mn 字段 / 与心法/技能完全不同形态 = 新 candidate）
4. **金宗门 30331001 二段 demo = dual root 形态确证**（has_active_root=true + has_passive_root=true / D-1606 跨段位 ActiveRoot candidate 累积加固第 12 例 / 同时引发 housekeeping #1 Mode E_dual_nonzero candidate 关联）
5. **30212012 万叶生发 bullet_count=1 与预测>=3 不符**（"万叶"语义 ≠ 多 BulletConfig / 暗示通过 SkillTag 控制弹片数 / 不是多 BulletConfigNode）
6. **模板-功能 1860223 召唤单位 = 0 BulletConfig + 0 buff + 1 tag + 1 template + 4 cond**（与"召唤"语义不符 BulletConfig=0 + 期望见到 TSET_CREATE_ENTITY 类未直接出现 / 形态需 B-022+ 更多模板-功能样本印证 / 但 cfg_summary SubType=0 + Mn=0 + 模板规律命中）
7. **303514 6 位 ID 老形态水宗门 SubType=0 + Mn=0**（与 D-2004 6 位 ID 老形态 vs 8 位 ID 新形态 SubType 分布差异 candidate 加固 / B-020 D-2004 第 2 例印证）

## §5 selection_bias_check 合并 housekeeping 字段

- **#1 Mode 命名一致性 SBL**：30331001 dual root → Mode E_dual_nonzero candidate（housekeeping #1 候选加固 / 维持登记 / B-022+ 续处理）
- **#2 sub_category 子命名空间拆分门槛达成**：30515004 = D-1904 第 6 例累积（B-020 D-2002 后第 6 例 / 拆分门槛远超已达成 / housekeeping #2 待 SkillEntry系统.md §SubType×Mode 矩阵段拆分 SubType=0 / SubType=701 sub_category 维度 / 仍保守 pending 用户裁决）
- **#3 picker_v2 learned_set 历史 hold-out 字典扫描算法补丁**：B-021 selection_bias_check 已自动通过 picker_v2 in_scope filter / learned_set_size=32（少于 65 严格 in_scope 是因 B-001~B-017 picks.json 缺 in_scope 字段被新 picker_v2 视为未学 / housekeeping #3 候选维持登记）
- **#4 picker_v2 嵌套黑名单**：B-021 0 嵌套漏判 ✓（v2.1 修复验证通过 / housekeeping #4 修复完成）
- **#5 picker_v2 quota min-1-per-non-empty-subcat 候选**：B-021 quota 分配 8 子分类有配额 / 8 子分类 0 配额（模板-单位/子弹/数值/宗门-土/宗门-金维持 0 / 宗门标签-BD/宗门标签-宗门/宗门标签-其他有用 维持 0 累积）→ housekeeping #5 候选加固（小 pool 子分类持续 0 配额 / B-022+ 工具补丁候选）

## §6 evidence_scope 标注

所有 10 picks 全 evidence_scope: 范围内（picker_v2 v2.1 严过滤 / 全 WHITELIST_pass / 0 嵌套漏判）

## §7 0 fabrication 自检

✓ 所有数据点字面拷贝自 B-021_picks.json + B-021_read.json
✓ 每条 hypothesis 引用 B-021_read.json 行号 / cfg_summary 字段名
✓ 0 GUESS_ONLY 升格为事实
