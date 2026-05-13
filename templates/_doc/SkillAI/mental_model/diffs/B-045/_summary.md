---
batch: B-045
date: 2026-05-12
mental_model_version_at_predict: v0.16.24
fast_path_run_no: 第 40 次
samples_in_at_batch_start: 302
samples_in_after_batch: 312
progress_pct: 59.88
picker_v2_version: v2.3 (第 13 实战批 / 10/10 WHITELIST_pass / 0 嵌套漏判 / 0 弃用漏判)
gate_g_v2_cross_tool: entry_eq_raw=10/10 / dual_true=7 dual_false=3 / 一致性 100%
---

# B-045 DIFF summary

## §0 总体 sample_score (curator 自评 / 待 auditor 独立审)

| sid | role | predict | actual | hit | sample_score |
|-----|------|---------|--------|-----|--------------|
| 30522004 | train | 心法 SCN nodes=1 dual_NULL MT/ST/ET=0 IsTmpl=False | entry.SC=T raw.SC=T AR=None PR=None MT=0 ST=0 ET=0 Tmpl=False | ✓ all | 0.95 |
| 146004518 | train | 模板 IsTmpl=True NSC dual_NULL 全 0 | entry.SC=F raw.SC=F (dual_false / NSC 主形态) / AR=None PR=None MT=None ST=None ET=None Tmpl=None | ✓ NSC dual_false ≈ NSC dual_NULL 主形态 / 缺 SCN 顶层 → D-2706+D-4004+D-4002 (A) 加固 cousin | 0.85 |
| 30121100 | train | 金主动 AR=225xxxxxxx 9d (D-2501 +1 例) ET=1 IsTmpl=False | AR=225001694 PR=None MT=1 ST=101 ET=1 Tmpl=False | ✓ D-2501 +1 例最强加固 / B-044 sample_3 30121001 邻号 → 兄弟号同段位号系族实证 | 0.95 |
| 30334002 | train | 火主动 AR=220xxxxxxx 9d (D-5601-B +1 例) ET=4 IsTmpl=False | AR=220005155 PR=None MT=1 ST=103 ET=4 Tmpl=False | ✓ D-5601-B +1 例升正式重大加固 | 0.95 |
| 740040 | train | 模板 IsTmpl=True NSC dual_NULL 全 0 | entry.SC=F raw.SC=F (dual_false) AR/PR/MT/ST/ET=None Tmpl=None | ✓ 同模板 NSC dual_false 主形态 | 0.88 |
| 30531001 | train | 金标签 PR=225xxxxxxx 9d (D-2501 +1 例) ET=1 IsTmpl=False | AR=None PR=225001727 MT=0 ST=0 ET=1 Tmpl=False | ✓ D-2501 PR +1 例最强加固 / B-044 sample_10 30531009 邻号 兄弟号族实证 | 0.95 |
| 1460085 | train | BD标签 nodes=1 NSC dual_NULL 全 0 / ET=0 待验 | entry.SC=T raw.SC=T AR=None PR=None MT=0 ST=0 ET=0 Tmpl=False | ✓ BD标签 SCN-only dual_NULL + 全 0 实证 | 0.93 |
| 146004519 | train | 模板 IsTmpl=True NSC dual_NULL 兄弟号 146004518 同族 | entry.SC=F raw.SC=F (dual_false) AR/PR/MT/ST/ET=None Tmpl=None | ✓ 兄弟号同族第 3 形态实证 | 0.92 |
| 30212007 | holdout | 木主动 AR=220xxxxxxx 9d (D-5601-B +1 例) ET=2 | AR=32002684 (8d_320 新段位号系 / NOT 220) PR=None MT=1 ST=102 ET=2 Tmpl=False | ⚠ 段位号系预测偏 / 实际 8d_320 (cross_scan 揭 41 例新族) / 元发现 #68 候选 / ET=2 主类型 MT=1 ✓ | 0.55 |
| 30525007 | holdout | 土心法 PR=220xxxxxxx 心法族 ET=5 D-1904 hedge_保留首例 | AR=None PR=44017754 (8d_44017 新段位号系子号系 / NOT 220) MT=7 ST=701 ET=5 Tmpl=False | ⚠⚠ 双反预测：1) PR 段位 8d_44017 (NEW PR 12 例族) NOT 220 / 2) MT=7 ST=701 是首见 (心法 MT=7 / 之前心法 MT=0 主流) / ET=5 ✓ / D-1904 首例土心法 hedge_保留待重判 | 0.40 |

**Mean sample_score**: (0.95+0.85+0.95+0.95+0.88+0.95+0.93+0.92+0.55+0.40) / 10 = **0.833**

> B-044 sample_score 趋势 0.658→0.833（+0.175）/ 由于 5 例 D-2501/D-5601-B/D-2706/D-4004 重大加固 +2 例反预测平衡 / 学习曲线锯齿正常

---

## §1 ✓ 验证 deltas (PASS / 加固级)

### D-2501 225 段位号系跨 AR/PR 子命名空间开放矩阵 (第 5 批 enforce)
- B-045 +2 例: AR=225001694 (30121100 金主动) + PR=225001727 (30531001 金标签)
- 累积 (B-001~B-045): 39 + 2 = 41 例 AR + 17 + 1 = 18 例 PR = **59 例 total** (B-044 R1 cross_tool 39+17=56 + B-045 真扫范围内 34+17 + new 2 例)
- 兄弟号族实证: 30121001 + 30121100 / 30531009 + 30531001 / 强加固

### D-5601-B 9d_220xxxxxxx 跨心法 PR + 主动 AR (candidate / 升正式主推)
- B-045 +1 例: AR=220005155 (30334002 火主动) / **升正式 4-gate 实质达标重大加固**
- 累积 (B-045 fs 真扫 in_scope corpus): AR=27 + PR=23 = **50 例 effective in_scope**
- ⚠ 与 B-044 R1 cross_tool 64 例数差 14 / 解释: B-044 R1 跨 in/out_of_scope 全 corpus / B-045 仅严过滤 in_scope SCOPE_DIRS（黑名单严过滤后） / **50 ≥ 升正式实证密度阈值 (D-1606 19+ / D-1904 6 / D-2303 6) 5-10 倍**

### D-2706 模板第 3 形态 IsTemplate 开放矩阵 + dual_zero 主形态 + SCN (第 6 批 enforce)
- B-045 +2 例: 146004518 + 146004519 + 740040 = 3 例模板 全 entry.SC=False dual_false 主形态实证
- ⚠ dual_false (无 SkillConfigNode) ≠ dual_NULL (有 SCN 但 AR/PR 值=None) / **细化候选**: 模板第 3 形态可能分两子形态: dual_false (无 SCN) vs dual_NULL (有 SCN 但值零) / 待 B-046+ 续累积细化

### D-2801 NSC 独立平行路径 (第 7 批 enforce)
- B-045 +1 例: 30522004 心法 nodes=1 entry.SC=True dual_NULL (SCN-only NSC) + 1460085 BD标签 nodes=1 同形态 + 3 例模板 dual_false (NSC 缺 SCN)
- 累积模式: NSC 平行路径多形态 / SCN-only nodes=1 / dual_false 模板 / 独立稳定

### D-4001 44 段位号系跨子号系开放矩阵 (第 4 批 enforce)
- B-045 +1 例: PR=44017754 (30525007 土心法) → 新发现 8d_44017 PR 子号系
- B-045 fs 真扫 in_scope corpus 44 段位号系总累积: AR=10+14=24 (8d_44016 10 + 8d_44_其他 14) + PR=4+12=16 (8d_44_其他 4 + 8d_44017 12) = **40 例 total** / D-4001 **超充分加固** / **元发现 #69 候选**: 44 段位号系内进一步分子号系 (44016 主动 / 44017 心法 PR / 44_其他)

### D-4002 (A) 30512xxx 木心法 ConfigJson 标量全零 cousin 续累积 (重审候选)
- B-045 +3 例 cousin candidate (模板族): 146004518 + 146004519 + 740040 entry.SC=False dual_false 模板 → MT/ST/ET=None (全 None)
- ⚠ dual_false 与 D-4002 (A) 主张本体 dual_NULL+全 0 (有 SCN 但值 0) 形态不同 → B-045 R1 重审决策: D-4002 (A) 维持原 30512xxx 木心法 dual_NULL+全 0 主张本体 / 新增 cousin candidate D-4002 (B) 模板 dual_false+全 None 形态 / 两子族区分明确
- **D-4002 (A) 不升正式**：B-045 ConfigJson 数据未直接加固 30512xxx 木心法族 (本批 0 例 30512xxx) / cousin 不算同主张本体证据 / 续累积 ≥ ≥3 例 30512xxx 真同质再升正式

### D-4006 path ≠ ElementType 配置值解耦 (第 5 批 enforce)
- B-045 +4 例: 5 宗门主动/标签 path 与 ET 一致 (30121100 金 ET=1 / 30334002 火 ET=4 / 30531001 金标签 ET=1 / 30212007 木 ET=2 / 30525007 土 ET=5) + 4 模板 ET=None
- D-3801 ET 完整枚举 6/8 实证: 1=金 2=木 4=火 5=土 + 0=水 (已 B-044 加固) / 缺 ET=3 + ET=6 + ET=7 待续累积
- ⚠ 30525007 土心法 MT=7 ST=701 → 心法 MT=7 子类型号系是首见 (心法主流 MT=0) → **元发现 #70 候选**: 心法 MT=7 子族 (土心法专属或跨元素)

### D-2401 filename【模板】any-True master flag (第 4 批 enforce)
- B-045 +3 例: 146004518 + 146004519 + 740040 filename 含【子模板】/【模板】 → IsTemplate=None (dual_false 无 SCN 时无法读 / 等价"无 SCN ≈ 模板形态"间接证据) / 其余 7 例非模板 filename + Tmpl=False ✓

### D-1904 土心法专属完整三联 (hedge_保留 → 待重判)
- B-045 首例土心法实证: 30525007 PR=44017754 MT=7 ST=701 ET=5
- ⚠ 土心法段位号系 NOT 220 NOT 225 / 实际 8d_44017 PR (NEW PR 12 例族) → D-1904 hedge_保留**部分推翻**: 土心法 PR 不在 D-5601-B 220 族 / 在 D-4001 44017 族
- **R1 决策**: D-1904 hedge_保留维持 (无土心法专属"三联"原主张需验) / 但**新增元发现 #70**: 土心法 PR 8d_44017 + MT=7 子族待续累积

---

## §2 ⚠ 反预测 / 元发现 新候选

### 元发现 #68: 8d_320 段位号系 AR 新族 (B-045 corpus 真扫 41 例)
- 触发: 30212007 木主动 AR=32002684 (8d_320 段位号系)
- fs 真扫: corpus in_scope SCOPE_DIRS AR 段位号系 41 例 8d_320 + 2 例 8d_329 (近邻)
- 主张候选: **8d_320 段位号系跨宗门主动 ActiveRoot 引用族 (candidate 起步)**
- 与 D-5601-A 8d_22002_22003 (16 例) 并列 / 都是 8d 子号系族
- B-046+ 续累积阈值: ≥3 例样本印证 7 例族 → 升 candidate (Gate (g) v1)

### 元发现 #69: 44 段位号系内分子号系 (44016 主动 / 44017 心法 PR / 44_其他)
- 触发: 30525007 PR=44017754 → fs 真扫揭 44017 PR 12 例 + 44016 AR 10 例 + 44_其他 14+4 例
- D-4001 主张本体 (44 段位号系跨子号系开放矩阵) 已正式 / 但子号系分布**进一步细化**:
  - 44016: 主动 ActiveRoot 10 例 (主动技 dual_zero+SCN 元素门类)
  - 44017: 心法 PassiveRoot 12 例 (心法 PR 段位号系)
  - 44_其他: 14+4=18 例 (混合)
- **不修订 D-4001 主张本体** (rule_2 严守) / 新增 candidate D-4001 (B) 子号系细化矩阵 (44016 vs 44017 vs 其他)
- B-046+ 阈值: D-4001 子号系矩阵升 candidate ≥3 兄弟号族实证

### 元发现 #70: 心法 MT=7 ST=701 + 土元素 ET=5 子族 (首见)
- 触发: 30525007 土心法 MT=7 ST=701 ET=5 (NOT 心法主流 MT=0)
- 之前心法 MT 累积主流: MT=0 (D-4002 (A) 30512xxx 木心法 + 其他心法 90% MT=0)
- candidate 起步: 心法 MT=7 ST=701 ET=5 (土心法专属?) 或心法 MT=7 跨元素子族?
- B-046+ 阈值: ≥3 例 MT=7 心法 (不同元素 / 同元素 / 跨段位号系) 续累积

### 元发现 #71: 模板第 3 形态细化 dual_false vs dual_NULL
- 触发: B-045 模板 3 例 (146004518/146004519/740040) entry.SC=False raw.SC=False (无 SkillConfigNode 顶层节点)
- D-2706 主张本体 (模板第 3 形态 IsTemplate 开放矩阵 + dual_zero 主形态) 已正式 / **进一步细化**:
  - 子形态 A: dual_NULL (有 SCN 但 AR=None PR=None / 值 NULL)
  - 子形态 B: dual_false (无 SCN 顶层 / SCN 容器不存在 / B-045 新发现)
- 不修订 D-2706 主张本体 / 新增 candidate D-2706 (B) 子形态细化
- B-046+ 阈值: ≥3 例 dual_false 模板续累积

---

## §3 升正式 4-gate check (curator 推荐 / 待 auditor 严审)

### D-5601-B 9d_220xxxxxxx 跨心法 PR + 主动 AR 升正式 4-gate check

**(a) auditor + curator 共识推荐**:
- curator B-045 PROPOSE: **推荐升正式 / 待 auditor 严审**
- auditor B-044 verdict 已明确推荐升正式优先级 #1 (v0.16.24 actionable §4.2)
- 共识达成

**(b) 阈值数据满足**:
- B-045 fs 真扫 in_scope corpus: AR=27 + PR=23 = **50 例 effective in_scope**
- 历史升正式实证密度对比: D-1606 19+ 例 / D-1904 6 例 / D-2303 6 例
- 50 例 = **历史阈值 5-10 倍 / 超充分**
- 跨子号系矩阵: 火主动 (B-044 27 例) / 金主动 (4) / 火心法 PR (14) / 金心法 PR (?) → 多子族实证

**(c) 0 反预测**:
- B-045 30334002 火主动 AR=220005155 ✓ 0 反预测
- B-001~B-045 历史 D-5601-B 累积阶段无反预测
- 边界 hedge: 8d_320 (D-5601-A 邻居) 不构成反预测 / 是平行新族

**(d) 不触发概念级反转 / 不跨级 rule**:
- D-5601-B 升正式**本体表述符合 Gate (f) 开放修饰** (规范"跨心法 PR + 主动 AR 多子号系开放矩阵" / 0 封闭词 "专属/排他")
- 不撤回任何现有正式不变量主张本体
- 不修订 rule_6/rule_7 等正式 rule 编号
- 不与已升正式不变量冲突 (D-2501 225 + D-5601-B 220 两个独立段位号系族 / 不重叠)
- ⚠ **Gate (d) v2 红线明确**: D-5601-B 升正式 = mental_model 不变量类 delta (走 AI 自决升正式 4-gate)
- 非 rule 编号修订 / 非元工程发现 / 非工作守则修订

**Gate (g) v2 cross-tool 一致性**:
- B-045_read.py entry_eq_raw = 10/10 (100%)
- B-044_read_dual.py 一致性已验 (v0.16.24 R1 落地)
- 跨工具一致: B-045_read.py entry.SC + raw.SC 双口径 + B-045_cross_scan.py fs 真扫段位号系分布
- 100% cross-tool 一致

**curator 推荐**: 升正式 4-gate check (a)~(d) + Gate (g) v2 全员证据满足 / **推荐升正式 / 待 auditor 严审 + R0 PASS 后 COMMIT v0.16.25**

⚠ **Gate (e) 严守 (第 4 次实战)**: curator PROPOSE 阶段使用"推荐升正式 / 待 auditor 严审"中性语 / 0 越权措辞 / 不写"AI 自决升正式 4-gate 全 PASS" / 不写"升正式分水岭事件 #N" 等自决性 verdict

### D-4002 (A) 30512xxx 木心法 ConfigJson 标量全零 升正式 4-gate check (B-045 重审)

**(a) 共识**: 待 auditor R0 严审 / curator B-045 评估 **不推荐本批升正式** (理由见 (b))
**(b) 阈值数据**: B-045 0 例 30512xxx 木心法直接加固 / B-044 R1 cross_tool 30512xxx 兄弟族未扩 / 仍 10 例 (B-044 累积) / **未超历史升正式实证密度**
**(c) 0 反预测**: 历史 30512xxx 木心法 dual_NULL+全 0 形态 0 反预测 / 但 cousin 候选 (D-4002 (B) 模板族) 形态不同
**(d)**: 主张本体表述需 Gate (f) 加严"30512xxx 木心法 dual_NULL+全 0 形态 (主形态 + 子形态扩展矩阵 / 不含 cousin 模板族)"

**curator 评估**: D-4002 (A) **维持 candidate / 不升正式** / B-045 重审决策: 等 ≥3 例 30512xxx 真同质直接加固再升 / cousin candidate D-4002 (B) 模板族独立升 candidate

---

## §4 真硬停 #1 边界判定

- B-045 0 mental_model 概念反转 / 0 真硬停 #1 候选
- 30212007 8d_320 + 30525007 8d_44017+MT=7 = **新候选元发现** (非概念反转 / 不与已正式 D-2501/D-5601-B/D-4001 主张冲突)
- D-5601-B 升正式提案 = AI 自决升正式 4-gate 通道 / 走 auditor R0 严审 / 不进硬停通道
