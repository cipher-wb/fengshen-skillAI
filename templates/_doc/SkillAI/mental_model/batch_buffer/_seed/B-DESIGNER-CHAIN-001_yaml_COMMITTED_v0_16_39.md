batch_id: B-DESIGNER-CHAIN-001
mode: PROPOSE  # curator Mode B 任务回流 / 非 fast-path bootstrap / 不走 AI 自决升正式 4-gate
proposed_by: skill-knowledge-curator (Mode B 回流)
proposed_date: "2026-05-13"
trigger:
  source_task: skill-designer agent / SkillGraph_2500001_链状连线指示器.json PoC
  task_summary: |
    端绑型 Beam 链状连线指示器 / IP=250 段 / 纯视觉无伤害 / 60 帧自然 die /
    BulletConfig.BeforeBornSE 嵌套 SE 内挂 FOLLOW_ENTITY + CREATE_BULLET 形成链状钩子
  user_verification: |
    用户原话 2026-05-13："上面的技能验证通过，你可以入库"
    = L2 实测加固（Unity 跑通）+ L1 用户口头裁决（V=1 → V=35 修订）
  related_postmortem: doc/SkillAI/postmortem/2026-05-13-038-nested-skilleffect-main-entity-trap.md (#038)
  prior_draft_artifacts:
    - doc/SkillAI/mental_model/batch_buffer/D-038-nested-skilleffect-main-entity-trap.yaml (D-038 草案 / 本批整合)

# ============================================================================
# 关键守则自检（PROPOSE 前严守）
# ============================================================================
self_check:
  rule_2_永不_silent_delete: passed   # 前轮 V=1 默认归纳 + AI 默认 entity:主体 编译器旧逻辑全保留作思想史
  gate_e_role_boundary: passed         # 本 yaml 仅 PROPOSE / 不写 auditor verdict / 不盖 PASS 章
  gate_f_open_modifier: passed         # claim 用 "嵌套调用栈" "调用栈最近一层" "穿透" 开放词 / 不用 "专属/排他/严约束/仅"
  gate_g_homogeneity_script: n/a       # candidate 阶段不强制 fs 真扫 / 升正式时再跑 verify_homogeneity.py
  ai_自决升正式_4gate: not_invoked     # Mode B 回流 / 仅 1 PoC + 1 金标印证 / 远未到 ≥3 同质例
  candidate_or_formal_classification: all_candidate
  curator_措辞红线_gate_e_v2: passed   # 不使用 "Gate 全 PASS / 升正式分水岭事件 #N 候选 / 升正式建议" 等 verdict 性质判定语

# ============================================================================
# Delta 列表（全员 candidate / 待用户拍板落盘）
# ============================================================================

deltas:

  # ===========================================================================
  - delta_id: D-038
    title: 嵌套 SkillEffect 上下文"主体 V=1"陷阱与"根创建者 V=35"正解
    classification: candidate
    recommend_upgrade: no
    proposed_落盘_位置: "新建子系统页 doc/SkillAI/mental_model/参数与上下文.md §嵌套主体语义"
    integrated_from: doc/SkillAI/mental_model/batch_buffer/D-038-nested-skilleffect-main-entity-trap.yaml

    claim: |
      在 BulletConfig.BeforeBornSE / AfterBornSE / DieSE / TrackEntityNoTargetSE /
      BuffConfig.OnAttachEffect / OnTickEffect / OnRemoveEffect 等
      **嵌套 SkillEffect 调用栈**中，
      `TCPT_MAIN_ENTITY (V=1, PT=5) "主体单位实例ID"`
      指的是**调用栈最近一层的主体**，**不是**"最初释放技能的玩家主角"：
        - 子弹 BulletConfig 的 BornSE 上下文 = 主体是子弹自身
        - Buff 的 OnTick/OnAttach Effect 上下文 = 主体是 Buff 携带者
        - RUN_SKILL_EFFECT 触发的子 effect 上下文 = 主体是上一层 effect 的主体
      要在嵌套上下文获取"最初施法的玩家主角"必须显式使用：
        - **V=35 TCPT_CREATE_ROOT_CREATOR_ENTITY_ID 施法者-根创建者**
          = 整条调用链最初的 caster（穿透多层 buff/嵌套技能/子弹）
        - 备选 V=37 TCPT_MAIN_CREATOR_ENTITY_ID 主体-创建者 = 仅穿透 1 层嵌套
        - 备选 V=3 TCPT_CREATE_ENTITY 施法者实例ID = 易被中间 buff 层覆盖
      推荐优先级：V=35 > V=37 > V=3 > V=1（V=1 在嵌套上下文几乎永远不是玩家主角）

    invariant_scope:
      affects:
        - BulletConfig.{Before,After,Die}BornSkillEffectExecuteInfo
        - BulletConfig.TrackEntityNoTargetSkillEffectConfigID
        - BuffConfig.OnAttach/OnTick/OnRemove Effect
        - 任意 RUN_SKILL_EFFECT 节点的子 effect
      does_not_affect:
        - SkillConfig.SkillEffectExecuteInfo 顶层（V=1 = 玩家主角 / 合法）
        - SkillConfig.SkillEffectPassiveExecuteInfo 顶层（同上）

    evidence:
      - level: L1_user_oracle
        date: "2026-05-13"
        note: |
          用户原话："32001000 里的【被跟随目标单位】，不可以填【常用参数值 -1- 主体单位实例ID】，
          这个的意义是，主体是谁，它就是谁；但这个节点是从子弹链接出来的，所以主体是子弹；
          而我们的目的，这个值要填主角，而主角是子弹的上一级，所以这里应该填：
          常用参数值 35-施法者-根创建者"
      - level: L1_source_code
        path: Assets/Scripts/TableDR_CS/Hotfix/Gen/common.hotfix.cs
        lines: "3777-3968"
        note: TCommonParamType enum 完整 46 项定义 + Description / V=1/3/33/35/37 语义精确
      - level: L1_golden_sample
        path: {{SKILLGRAPH_JSONS_ROOT}}怪物/BOSS/狮妖/SkillGraph_280103_【狮妖】连线.json
        note: |
          280103 BeforeBornSE 的 FOLLOW_ENTITY (28023955) P[1] = V=37 PT=5
          CREATE_BULLET (28023952) P[4] = V=37 PT=5
          → 金标本来就避开 V=1 / 印证嵌套上下文 V=1 陷阱
      - level: L2_user_field_test
        date: "2026-05-13"
        note: |
          SkillGraph_2500001 链状连线指示器 r1 (V=1) 实测错向 →
          修订 r2 (V=35) → Unity 跑通验证（用户口头确认入库）

    sample_count_for_claim: 2  # 1 PoC + 1 金标印证（同方向 V≠1）
    upgrade_to_formal_readiness:
      gate_a_homogeneity: pending
      gate_b_threshold: 1_of_3  # 累积 ≥3 跨子系统反例（BulletConfig + Buff + RUN_SKILL_EFFECT 各 1）
      gate_c_zero_counter_prediction: passed_so_far
      gate_d_no_concept_reversal: passed  # 前 AI 默认归纳是补盲 / 非推翻已有正式不变量
      gate_f_open_modifier: passed
      gate_g_cross_tool_homogeneity_script: pending  # 升正式时跑 fs 全扫统计 V=1 vs V=35 vs V=37 分布
      推荐升正式路径: |
        1. 累积场景扩展：再 2 例（Buff Effect 1 + RUN_SKILL_EFFECT 嵌套 1）
        2. 跑 fs 真扫 SkillGraph 全库 BornSE / OnTickEffect 节点 V= 分布
        3. 若 V=1 在嵌套上下文 0 真用 → 走用户拍板升正式（不走 AI 自决 4-gate，因涉及命名空间语义建模 = 元工程）
        4. 升正式后落 mental_model/README §rule_X 或 §rule_6 v4 候选段（用户拍板）

    thought_history_preservation:
      prior_ai_default: |
        前 designer agent 在 expand_bullet_chain (skill_compiler.py) 中
        硬编码 follow_node = _make_chain_follow_entity_node(resolve_ref("entity:主体"), ...)
        desc="子弹端绑主体(玩家)" — 默认归纳 = "BulletConfig BornSE 主体 = 玩家主角"
        rule_2 严守：编译器 git 历史保留 + D-038 草案 prior_ai_default 段保留 + 本 yaml 保留
      reason_failed: |
        AI 把 SkillConfig 顶层语义("主体=玩家")错误外推到嵌套 BulletConfig.BeforeBornSE
        GATE-0.5 虽读了 280103 金标但只复制 "形态" 未深究 "为什么金标不用 V=1"
      evolution_path:
        v1_AI_默认: "V=1 PT=5 (TCPT_MAIN_ENTITY) / 错"
        v2_用户裁决: "V=35 PT=5 (TCPT_CREATE_ROOT_CREATOR_ENTITY_ID) / 对"
        修订位置:
          - SkillGraph_2500001.json (FOLLOW_ENTITY P[1] + CREATE_BULLET P[4])
          - 链状连线指示器.skill.yaml (新增 bind_master/creator: "施法者根")
          - skill_compiler.py expand_bullet_chain default + _make_chain_follow_entity_node docstring

  # ===========================================================================
  - delta_id: D-039
    title: TCommonParamType 4×4 角色 × 变形矩阵 + ORIGIN/ROOT 系列跨调用栈锁定规律
    classification: candidate
    recommend_upgrade: no
    proposed_落盘_位置: "新建子系统页 doc/SkillAI/mental_model/参数与上下文.md §TCPT 角色变形矩阵"

    claim: |
      TCommonParamType enum 46 项里描述"实体引用"的核心子集呈现规律性的
      **4 角色 × 4 变形 对称矩阵**：

      | 角色 \\ 变形            | 原始 | +伤害归属 | +根创建者 | +直接创建者 |
      |-------------------------|------|-----------|-----------|-------------|
      | 主体 (MAIN)             | 1    | 4         | 33        | 37          |
      | 目标 (TARGET)           | 2    | 5         | 34        | 38          |
      | 施法者 (CREATE)         | 3    | 6         | 35        | 39          |
      | Buff来源 (BUFF_SOURCE)  | -    | 32        | 36        | 40          |

      **ORIGIN/ROOT 系列跨调用栈锁定规律**：
        - `TCPT_ORIGIN_*` 系列（V=7/13/15/16/24/25/26/27/28/30/41/44/45/46）
        - `TCPT_ROOT_*` 系列（V=33/34/35/36/43）
        = **跨嵌套调用栈不漂移** / 永远指向"最初那次施法"
      推论：`CREATE_BULLET P[10] = {V=41, PT=5}` 伤害归属锁最初技能实例
            就是这条规律的具体应用（不被嵌套 buff/bullet 层漂移）

      与 D-038 的耦合：D-038 是规律的反面教材（V=1 = 原始系列 / 跨嵌套漂移）/
      D-039 是规律的正面陈述（ROOT 列 + ORIGIN 系列 = 跨嵌套锁定）

    evidence:
      - level: L1_source_code
        path: Assets/Scripts/TableDR_CS/Hotfix/Gen/common.hotfix.cs
        lines: "3777-3968"
        note: |
          enum 46 项完整 dump 后归纳矩阵 / 4×4 对称结构观察到
          ORIGIN 系列字面包含 "起源/最初" 语义
          ROOT 系列字面包含 "根创建者" 语义
      - level: L2_golden_sample_cross_check
        samples:
          - SkillGraph_280103_【狮妖】连线.json (CREATE_BULLET P[4]=V=37 + P[10]=V=41 锁定模式)
          - SkillGraph_2500001_链状连线指示器.json (CREATE_BULLET P[4]=V=35 + P[10]=V=41)
        note: 两金标 CREATE_BULLET P[10]=V=41 (TCPT_ORIGIN_*) 锁定伤害归属 = ORIGIN 锁定规律具体应用

    sample_count_for_claim: 2_samples_+_1_enum_dump  # 远未到 ≥3 跨子系统多形态印证
    upgrade_to_formal_readiness:
      blocker: |
        矩阵 + 锁定规律是**描述性归纳** / 升正式前需：
        1. fs 真扫 V=4/5/6 (+伤害归属) + V=32/36/40 (BUFF 系列) 全库使用分布
        2. 验证矩阵每格在真实样本里都有印证（44 格中目前仅 V=1/3/35/37/41 5 格有金标）
        3. 升正式更适合作"命名空间约定"层规则（同 v0.16.18 D-3807 模式 / 走用户拍板升格通道）
      推荐路径: 续累积 ≥3 批跨子系统样本 + fs 真扫后走用户拍板升正式 / 不走 AI 自决 4-gate

    thought_history_preservation:
      origin_observation: |
        D-039 矩阵是 D-038 用户裁决事件后 AI 全量 dump TCommonParamType enum 时归纳出的副产品
        归纳触发：用户问 "为什么 V=35 而不是 V=33" → AI dump 全部 46 项 → 发现 4×4 对称
      不删除规律保留: |
        即使后续 fs 真扫发现某格永远 0 命中 / 矩阵不删除 / 该格加注脚 "实战 0 命中" / rule_2 严守

  # ===========================================================================
  - delta_id: D-040
    title: 端绑型 Beam 链状指示器子弹双钩子范式（FOLLOW_ENTITY + CREATE_BULLET 链）
    classification: candidate
    recommend_upgrade: no
    proposed_落盘_位置: "新建子系统页 doc/SkillAI/mental_model/链状指示器子弹.md （独立小页 / D-040 专属）"
    note_on_prior_draft: |
      前轮 designer agent 起草 D-CHAIN-001 但未落 batch_buffer 文件 /
      本 yaml 整合为 D-040 / 主张本体由 curator Mode B 规范化

    claim: |
      端绑型 Beam 链状视觉指示器（无伤害 / 纯视觉）配置范式：
      由**两类钩子**在 BulletConfig.BeforeBornSE 内协作组成链：
        1. **FOLLOW_ENTITY 钩子**：让本段子弹首端跟随上一节点（角色 / 上一段子弹尾）
           - P[1] 被跟随实体 = V=35 (CREATE_ROOT_CREATOR) 锁定最初施法者
           - 或 V=37 (MAIN_CREATOR) 怪物自释场景
        2. **CREATE_BULLET 钩子**：在本段子弹生成尾端时再触发下一段子弹
           - P[4] 创建者 = V=35 / V=37 同 FOLLOW_ENTITY 口径一致
           - P[10] 伤害归属 = V=41 (ORIGIN 系列) 锁最初技能实例

      链长 N 段 = N 个 BulletConfig 实例链式串联 / 每段 BeforeBornSE 各挂一对双钩子 /
      自然 die 通过 60 帧（或 IP=N 段类比）超时控制 / 不需要显式 DESTROY_BULLET

      与 D-038 的耦合：D-040 是"嵌套主体陷阱"在链状指示器场景的具体应用范式 /
      违反 D-038 → D-040 链断（每段子弹绑到自己头上而非主角）

    evidence:
      - level: L1_repro
        path: {{SKILLGRAPH_JSONS_ROOT}}宗门技能/AIGen/SkillGraph_2500001_链状连线指示器.json
        note: PoC 实例 / Unity 跑通验证（用户口头确认 2026-05-13）
      - level: L1_golden_sample
        path: {{SKILLGRAPH_JSONS_ROOT}}怪物/BOSS/狮妖/SkillGraph_280103_【狮妖】连线.json
        note: 怪物自释链状连线金标 / 同范式（V=37 怪物场景变体）
      - level: L2_user_field_test
        date: "2026-05-13"
        note: SkillGraph_2500001 r2 实测跑通入库

    sample_count_for_claim: 2  # 1 宗门 PoC + 1 怪物金标 / 跨阵营但同范式
    upgrade_to_formal_readiness:
      gate_b_threshold: 2_of_3  # 累积 ≥3 跨段位/跨阵营链状样本（再 1 例如玩家技能阵营链状）
      推荐升正式路径: |
        累积第 3 例（建议玩家被动型链状或法宝链状）→ auditor R0 推荐 → 用户拍板升正式
        升正式后落独立子系统页 链状指示器子弹.md（D-040 专属）+ 编译器 expand_bullet_chain 加固

    thought_history_preservation:
      prior_designer_draft_status: |
        前轮 designer agent 在任务报告中起草 D-CHAIN-001 主张但未落 batch_buffer 文件 /
        本 yaml D-040 = 规范化整合版 / 主张本体由 curator Mode B 表述加修
      r1_to_r2_evolution: |
        SkillGraph_2500001 r1 (FOLLOW_ENTITY P[1]=V=1) 链段绑到子弹自身 → 链不形成
        r2 (P[1]=V=35) 链段绑到最初施法者 → 链正确形成 / Unity 验证通过

# ============================================================================
# 落盘位置推荐（候选 4 选 / curator 推荐 + 理由）
# ============================================================================

proposed_landing_layout:

  推荐方案: A_新建参数与上下文页_+_D040_独立小页
  方案_A_合并:
    路径:
      - 新建 doc/SkillAI/mental_model/参数与上下文.md
        ├── §嵌套主体语义 (D-038)
        ├── §TCPT 角色变形矩阵 (D-039)
        └── §ORIGIN/ROOT 跨调用栈锁定规律 (D-039 子段)
      - 新建 doc/SkillAI/mental_model/链状指示器子弹.md (D-040 专属 / 小页)
        └── 内交叉引用 [[参数与上下文]] §嵌套主体语义

  方案_A_理由: |
    1. D-038 + D-039 主题同源（都是 TCPT/PT 系列参数语义）/ 同页内聚最自然
    2. "参数与上下文" 命名跨 BulletConfig + Buff + SkillEffect 子系统通用 /
       未来扩 PT=0/1/2/3/4/5/6 各 type 类型也能放（无 collision）
    3. D-040 链状指示器是 D-038 的应用场景 / 独立成小页方便实战引用 / 但通过交叉引用回链 D-038 主张本体
    4. 现有子系统页清单（9 页）+ 2 新页（参数与上下文 + 链状指示器子弹）= 11 页 / 不冗余
    5. 不污染现有 Buff 系统页 / BulletConfig 子系统页（后者根本还不存在 / 不强建）
    6. 符合 README §6 "实际创建顺序由用户的实际工作驱动"

  对比方案:
    B_嵌套SkillEffect上下文页: 命名太窄 / D-039 矩阵放不进 / 拒
    C_拆 BulletConfig + Buff 各加段: D-038 跨页同义 / 维护复杂 / 拒（且 BulletConfig 子系统页根本不存在）
    D_只建参数与上下文页_合并_D040: D-040 是具体形态范式 / 与 D-038/D-039 抽象语义层不在同粒度 / 同页混杂会污染抽象层 / 拒

# ============================================================================
# 思想史保留登记（rule_2 永不 silent delete）
# ============================================================================

thought_history_preservation_log:
  - id: HM-DESIGNER-001
    location: D-038.thought_history_preservation.prior_ai_default
    summary: 前 designer AI 默认 "BulletConfig BornSE 主体 = 玩家主角" 错误归纳 / 保留 + 修订轨迹完整
    rule_2_严守: 编译器 git 历史 + D-038 草案文件 + 本 yaml 三处冗余保留

  - id: HM-DESIGNER-002
    location: D-040.thought_history_preservation.prior_designer_draft_status
    summary: 前 designer agent D-CHAIN-001 起草未落盘 / 本 yaml 规范化整合为 D-040 / 起草版本路径记录

  - id: HM-DESIGNER-003
    location: D-040.thought_history_preservation.r1_to_r2_evolution
    summary: SkillGraph_2500001 r1→r2 V=1→V=35 演化轨迹 / JSON 内置注释 + Sticky Note 已同步留痕

# ============================================================================
# 升格 readiness 路径汇总
# ============================================================================

upgrade_path_summary:
  D-038:
    当前阶段: candidate (Mode B 入库)
    下一步: 续累积 ≥3 跨子系统例（BulletConfig + Buff + RUN_SKILL_EFFECT）
    升格通道: 用户拍板（不走 AI 自决升正式 4-gate / 涉及命名空间语义建模 / Gate (d) 红线遵守）
    升格落盘: README §rule_X 新立 或 §rule_6 v4 候选段

  D-039:
    当前阶段: candidate (Mode B 入库)
    下一步: fs 真扫全 SkillGraph 库 V=4/5/6/32/36/40 等格分布 + 多形态金标印证
    升格通道: 用户拍板（命名空间约定层 / 元工程发现 / 同 v0.16.18 D-3807 模式）
    升格落盘: README §命名空间速查 新段 或 参数与上下文页正式段

  D-040:
    当前阶段: candidate (Mode B 入库)
    下一步: 累积第 3 例链状样本（建议玩家被动型 或 法宝型）
    升格通道: 用户拍板（具体形态范式 / 不涉及概念反转）
    升格落盘: 链状指示器子弹.md 正式段 + 编译器 expand_bullet_chain 加固

# ============================================================================
# 待用户拍板的开口点（curator 不直接落盘 / 等用户回应）
# ============================================================================

open_questions_for_user:
  Q1_落盘位置:
    问题: 推荐方案 A（新建参数与上下文.md + 链状指示器子弹.md 2 新页）是否同意？
    备选: 方案 B / C / D 见 proposed_landing_layout.对比方案 段
    默认: A

  Q2_全员_candidate_确认:
    问题: D-038 / D-039 / D-040 全员落 candidate / 不走 AI 自决升正式 4-gate / 同意？
    理由: |
      - Mode B 回流场景 / 非 fast-path bootstrap / auditor 未参与 / Gate (a) curator+auditor 共识不满足
      - 当前样本数 1 PoC + 1 金标 = 2 例 / 远未到升正式 ≥3 同质阈值
      - D-039 是描述性归纳 / 升正式涉及元工程命名空间建模 / 应走用户拍板通道
    默认: yes

  Q3_memory_速查条新增:
    问题: 是否同意新增 memory 速查条 reference_nested_main_entity_trap.md ？
    内容简述: |
      "配 BulletConfig.BornSE / Buff Effect / 嵌套 SkillEffect 时
       V=1 主体 = 调用栈最近一层 / 不是玩家主角 / 拿主角必须 V=35 施法者-根创建者"
    默认: yes（PostMortem #038 §预防 段已起草建议）

  Q4_编译器_grep扫描_其他位置:
    问题: |
      PostMortem #038 §预防 列出编译器其他 8 处 resolve_ref("entity:主体") 位置（含 Buff source/host /
      bullet creator / Effect target / follow source 等）/ 是否同意启动编译器全员审计修订？
    默认: 暂缓 / 待 D-038 累积 ≥3 例后再启动 / 避免一次性盲改引发回归

# ============================================================================
# 关联引用
# ============================================================================

related_artifacts:
  - PostMortem #038: doc/SkillAI/postmortem/2026-05-13-038-nested-skilleffect-main-entity-trap.md
  - D-038 草案: doc/SkillAI/mental_model/batch_buffer/D-038-nested-skilleffect-main-entity-trap.yaml
  - PoC 样本: {{SKILLGRAPH_JSONS_ROOT}}宗门技能/AIGen/SkillGraph_2500001_链状连线指示器.json
  - 金标样本: {{SKILLGRAPH_JSONS_ROOT}}怪物/BOSS/狮妖/SkillGraph_280103_【狮妖】连线.json
  - TCPT enum 源: Assets/Scripts/TableDR_CS/Hotfix/Gen/common.hotfix.cs:3777-3968
  - IR YAML: doc/SkillAI/samples/ir/链状连线指示器.skill.yaml
  - 编译器: doc/SkillAI/tools/skill_compiler.py (expand_bullet_chain)
  - memory TCPT 速查: C:/Users/Administrator/.claude/projects/.../memory/reference_tcpt_enum_full.md

# ============================================================================
# 元决策记录
# ============================================================================

meta_decisions:
  - Mode B 回流不走 fast-path peer review 闭环 / 不调用 auditor agent / 用户直接裁决（curator 守则 §1 Mode B 流程）
  - 本批不 bump mental_model 版本号 / 待用户拍板后由 curator 同会话内执行落盘 + bump
  - 不直接编辑现有子系统页（rule §2.1 严守 / 仅 PROPOSE）
  - 不写 auditor verdict 文件（Gate (e) v2 严守第 21 次零越权 / 连续保持）
