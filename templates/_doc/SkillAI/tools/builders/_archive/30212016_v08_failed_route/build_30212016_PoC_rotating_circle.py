#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30212016 【木宗门】奇术_人阶_PoC_旋转扩张圈 — SkillConfig 调用方生成器（v1.0 / 2026-05-11）

设计意图（v08 模板首次实战 / 调用方零 SkillTag 范式）：
- 调用 v08 模板（根 ID 32300001 / OnTick init=32300101）。
- 调用方完全 hard-code EXT_PARAM 常量（PT=0），**不声明任何 SkillTag**（PoC 简洁）。
- 调用方内嵌一个 contract-compliant BulletConfig（ID=320XXX，AfterBorn=32300101）。
- BulletConfig.Model = 3200303（复用叶散风行普通飞叶模型 / 用户裁决 / 满足 PostMortem #024 ≥4 要求）。
- SkillConfig 顶层只有 1 个 OnSkillStart effect = TSET_RUN_SKILL_EFFECT_TEMPLATE。

数据来源：
- 用户决策 (GATE-1)：SkillID=30212016 / Name=PoC_旋转扩张圈 / vR=13/帧 (≈400/sec) / lifetime=60帧=2s
- 用户决策 (GATE-1)：BulletModel=3200303 复用 / Icon=Skill/Pugong/PuGong_mu 占位
- spec §3 默认参数：N=8, R0=200, phi=0, vR=13, aR=0, omega=3度/帧, maxR=1200, minR=0, follow=0
- v08 模板 contract：BulletConfig.AfterBorn=32300101 / Speed/Acce/TurnSpeed/TracePathType 全 0

ID 段位（30212016 = 2 千万级，安全 < int32 max=2147483647）：
- SkillConfig ID: 30212016
- 内嵌 BulletConfig ID: 321000（GATE-3.5 自审发现 320190 已被 30222009 占用 → 改用 321000 全局扫描确认未占）
- SkillEffectConfig ID: 32390000+（OnSkillStart ORDER 根）

参考：
- v08 模板：doc/SkillAI/tools/builders/build_rotating_expand_bullet_ring_template_v08.py
- 类似调用方：301104 吴波测试（已找到的唯一现有 32300001 调用方）
- SkillConfig 字段：30212010 叶散风行（同 SubType=102 / 木宗门人阶奇术）

⚠️ 不要再 IR YAML 走（IR v1.0 schema 不支持 template_call + 内嵌 BulletConfig + EXT_PARAM 数组传参原语）
⚠️ Sticky Note v3 模板 5 段
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJ = Path(r"<<PROJECT_ROOT_WIN>>")
OUTPUT = PROJ / "<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212016【木宗门】奇术_人阶_PoC_旋转扩张圈.json"

# v08 模板文件路径（RUN_TEMPLATE.TemplateData.TemplatePath 必须填这个相对工程根路径）
TEMPLATE_FILE_PATH = "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】旋转扩张子弹圈.json"
TEMPLATE_FILE_ABS  = PROJ / TEMPLATE_FILE_PATH
TEMPLATE_DESC_FILE = "SkillGraph_【模板】旋转扩张子弹圈.json"  # RUN_TEMPLATE 节点 Desc 习惯写法（同真实样本 30233003 等）

# ===== 关键 ID =====
SKILL_ID                = 30212016
BULLET_CONFIG_ID        = 321000   # 全局扫描验证未占用（spec §5 假设的 320180+ 段已占满）
EFFECT_BASE             = 32390000 # 全局扫描验证未占用（仅本文件占用）
ROOT_TEMPLATE_EID       = 32300001     # v08 模板根（外部引用，不在本文件声明）
ONTICK_INIT_EID         = 32300101     # v08 模板 OnTick 入口（外部引用）

# ===== TableTash =====
TASH_SKILL_EFFECT    = "0CFA05568A66FEA1DF3BA6FE40DB7080"
TASH_BULLET_CONFIG   = "A4AEA1F4B1BD0FA9FD2F066BE902466F"
TASH_SKILL_CONFIG    = "1B07683FF8D5DAE7F1CB4F2B3F22A2C7"  # 需要确认
TASH_REF_CONFIG      = "F3C5C24F0F7A0042DF7DE9C31B94F4DB"  # RefConfigBase

# ===== TSkillEffectType =====
ET = {
    "ORDER": 1,
    "RUN_TEMPLATE": 118,
}

# ===== TParamType =====
PT_NULL, PT_ATTR, PT_FUNC_RET, PT_SKILL_PARAM, PT_EXTRA_PARAM, PT_COMMON_PARAM = 0, 1, 2, 3, 4, 5

# ===== EXT_PARAM 实参（GATE-1 用户裁决值） =====
EXT_VALUES = [
    # idx, value, 含义
    (1,  8,    "bulletCount N"),
    (2,  200,  "initialRadius R0"),
    (3,  0,    "tangentOffsetAngle phi (度)"),
    (4,  13,   "radialVelocity vR (单位/帧, ≈400/sec)"),
    (5,  0,    "radialAcceleration aR (单位/秒²)"),
    (6,  3,    "angularVelocity omega (度/帧 = 90度/秒)"),
    (7,  1200, "maxRadius"),
    (8,  0,    "minRadius"),
    (9,  0,    "followPlayer (0=锁定中心)"),
    (10, BULLET_CONFIG_ID, "bulletConfig (内嵌 BulletConfig.ID)"),
]


def P(value, pt=PT_NULL, factor=0):
    """构造 Param dict（防 Python bool 透出 — PostMortem #007）"""
    return {
        "Value": int(value) if isinstance(value, bool) else value,
        "ParamType": pt,
        "Factor": factor,
    }


def new_guid() -> str:
    return str(uuid.uuid4())


def load_template_params_from_v08() -> tuple[list, str]:
    """从 v08 模板文件读取 32300001 节点的 TemplateParams，并去掉 ParamUID 字段。

    关键 PostMortem（2026-05-11）：RUN_TEMPLATE 节点的 TemplateData.TemplateParams 必须 1:1
    复制模板入口节点的 TemplateParams 元数据（仅去除 ParamUID 字段 — 该字段只在
    模板入口节点有，调用方端不携带）。否则 SkillEditor 报"模板引用无效"。

    返回：(template_params_list, template_path)
    """
    if not TEMPLATE_FILE_ABS.exists():
        raise FileNotFoundError(f"v08 模板文件未找到: {TEMPLATE_FILE_ABS}")
    d = json.loads(TEMPLATE_FILE_ABS.read_text(encoding="utf-8"))
    for r in d["references"]["RefIds"]:
        if r["data"].get("ID") == ROOT_TEMPLATE_EID and r["data"].get("IsTemplate") is True:
            tps = r["data"].get("TemplateParams", [])
            # 去除 ParamUID（该字段仅在模板入口节点出现，RUN_TEMPLATE.TemplateData.TemplateParams 不含此字段）
            cleaned = []
            for tp in tps:
                copy = {k: v for k, v in tp.items() if k != "ParamUID"}
                cleaned.append(copy)
            return cleaned, TEMPLATE_FILE_PATH
    raise RuntimeError(f"v08 模板根节点 ID={ROOT_TEMPLATE_EID} (IsTemplate=True) 未找到")


def build():
    refs = []
    edges = []
    field_port_edges = []
    guid_of_id: dict[int, str] = {}
    next_rid = 1000
    auto_y = 0

    def add_node(cls: str, config_id: int, payload: dict, *,
                 desc: str = "", table_tash: str = TASH_SKILL_EFFECT,
                 table_name: str = "SkillEffectConfig",
                 effect_type: int = None,
                 extra_data: dict = None,
                 position=None) -> str:
        nonlocal next_rid, auto_y
        guid = new_guid()
        rid = next_rid
        next_rid += 1
        if position is None:
            position = (0.0, float(auto_y))
            auto_y += 100
        data = {
            "GUID": guid,
            "computeOrder": rid - 1000,
            "position": {
                "serializedVersion": "2",
                "x": float(position[0]), "y": float(position[1]),
                "width": 280.0, "height": 200.0,
            },
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": config_id,
            "Desc": desc,
            "IsTemplate": False,
            "TemplateFlags": 0,
            "TemplateParams": [],
            "TemplateParamsDesc": [],
            "TemplateParamsCustomAdd": False,
            "TableTash": table_tash,
            "ConfigJson": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"{table_name}_{config_id}",
        }
        if effect_type is not None:
            data["SkillEffectType"] = effect_type
        if extra_data:
            data.update(extra_data)
        refs.append({
            "rid": rid,
            "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
            "data": data,
        })
        guid_of_id[config_id] = guid
        return guid

    def add_field_port_edge(src_node_id: int, dst_node_id: int, field_path: str):
        """字段端口边：dst.ConfigJson 的 field_path 字段 → 引用 src 节点 ID"""
        field_port_edges.append({
            "GUID": new_guid(),
            "inputNodeGUID": guid_of_id[src_node_id],
            "outputNodeGUID": guid_of_id[dst_node_id],
            "inputFieldName": "ID",
            "outputFieldName": "PackedMembersOutput",
            "inputPortIdentifier": "0",
            "outputPortIdentifier": field_path,
            "isVisible": True,
        })

    # ===== 1. RUN_SKILL_EFFECT_TEMPLATE 调 v08 模板 =====
    # Params layout:
    #   [0] caster=主体 (PT=5 COMMON_PARAM, V=1)
    #   [1] skill (PT=5, V=2)
    #   [2] 模板根 ID = 32300001 (PT=0)
    #   [3..12] = EXT_PARAM[1..10]
    #
    # ⭐ TemplateData 字段必须填写完整（PostMortem 2026-05-11 #027 防御）：
    #   TemplateData.TemplateParams = v08 模板根节点 TemplateParams 1:1 复制（去除 ParamUID）
    #   TemplateData.TemplatePath   = v08 模板文件相对工程根的路径
    # 否则 SkillEditor 报 "模板引用无效:32300001"，节点显示"模板效果(空)"。
    template_params, template_path = load_template_params_from_v08()
    run_template_eid = EFFECT_BASE  # 32390000
    run_template_payload = {
        "ID": run_template_eid,
        "SkillEffectType": ET["RUN_TEMPLATE"],
        "Params": [
            P(1, PT_COMMON_PARAM),                  # [0] 主体
            P(2, PT_COMMON_PARAM),                  # [1] 技能
            P(ROOT_TEMPLATE_EID),                   # [2] 模板根 32300001
        ] + [P(v) for (_, v, _) in EXT_VALUES],     # [3..12] EXT_PARAM[1..10]
    }
    add_node(
        "TSET_RUN_SKILL_EFFECT_TEMPLATE",
        run_template_eid, run_template_payload,
        # Desc 跟真实样本约定 = 模板文件名（不是描述文字）
        desc=TEMPLATE_DESC_FILE,
        effect_type=ET["RUN_TEMPLATE"],
        extra_data={
            "TemplateData": {
                "TemplateParams": template_params,
                "TemplatePath": template_path,
            },
        },
        position=(400, 0),
    )

    # ===== 2. OnSkillStart 顶层 ORDER（即使只有一个子节点，规范要 ORDER 包一层） =====
    # 看 30212010 SkillConfig.SkillEffectExecuteInfo.SkillEffectConfigID 直接指向 32002225（一个 ORDER 节点）。
    # 我们也建一个 ORDER 包 RUN_TEMPLATE，让顶层入口稳定可扩展。
    onstart_order_eid = EFFECT_BASE + 1  # 32390001
    onstart_payload = {
        "ID": onstart_order_eid,
        "SkillEffectType": ET["ORDER"],
        "Params": [P(run_template_eid)],
    }
    add_node(
        "TSET_ORDER_EXECUTE",
        onstart_order_eid, onstart_payload,
        desc=f"OnSkillStart 顶层 ORDER → RUN_TEMPLATE({run_template_eid})",
        effect_type=ET["ORDER"],
        position=(0, 0),
    )

    # ===== 3. 内嵌 contract-compliant BulletConfig =====
    # 关键 contract：AfterBornSkillEffectExecuteInfo.SkillEffectConfigID = 32300101
    # Speed/Acce/TurnSpeed/TracePathType 全 0（位移由 OnTick 接管）
    # Model = 3200303（用户裁决，复用叶散风行普通飞叶模型 / 满足 PostMortem #024 ≥4）
    # LastTime = 60 帧 = 2s, LifeFlag = 2（定时销毁，spec §3 lifetime=2s）
    bullet_payload = {
        "ID": BULLET_CONFIG_ID,
        "Model": 3200303,               # 复用叶散风行飞叶
        "ModelBaseScalePercent": 100,
        "Speed": 0,                     # 位移由 OnTick 接管
        "AcceSpeed": 0,
        "MaxSpeed": 0,
        "TurnSpeed": 0,
        "MaxTurnSpeed": 0,
        "TurnAcceSpeed": 0,
        "PitchTurnSpeed": 0,
        "PitchMaxTurnSpeed": 0,
        "PitchTurnAcceSpeed": 0,
        "TracePathType": 0,             # 不走子弹引擎自带轨迹
        "TracePathParams": [],
        "AngleAdjustType": 0,
        "FlyType": 0,
        "Hp": 0,
        "ATK": 0,
        "MaxDistance": 0,
        "LastTime": 60,                 # 60 帧 = 2 秒（spec §3 lifetime）
        "LifeFlag": 1,                  # 1 = 定时销毁（按 LastTime）— v1.1 修：之前误填 2 = 距离销毁，触发"出生瞬间距离上限=0 销毁"
        "Flags": 0,
        "DestroyWhenCreatorDie": False,
        "IsDieKeepMove": False,
        "IsAiEscape": False,
        "IsCloseTurnAutoHit": False,
        "IsOpenPhysicalReflect": False,
        "PhysicalReflectCount": 0,
        "PhysicalReflectEndActionType": 0,
        "ChaseTargetEnemy_AttachPos": 0,
        "ChaseTargetEnemy_FaceToTarget": False,
        "ChaseTargetEnemy_PitchFaceToTarget": False,
        "ChainModel": 0,
        "ChainModelScalePercent": 100,
        "ChainTilingFactor": 100,
        "TrackEntityNoTargetSkillEffectConfigID": 0,
        # ⭐ contract 关键字段
        "BeforeBornSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "AfterBornSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": ONTICK_INIT_EID},
        "DieSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "DisappearEffect": 0,
        "delayDestroyTime": 0,
    }
    add_node(
        "BulletConfigNode", BULLET_CONFIG_ID, bullet_payload,
        desc=f"内嵌 BulletConfig {BULLET_CONFIG_ID}\n"
             f"Model=3200303 (复用叶散风行飞叶)\n"
             f"Speed/Acce/Turn/Trace 全 0（位移由 OnTick 接管）\n"
             f"LastTime=60帧=2s LifeFlag=2(定时销毁)\n"
             f"⭐ AfterBorn={ONTICK_INIT_EID} → 触发 v08 模板 OnTick 链",
        table_tash=TASH_BULLET_CONFIG,
        table_name="BulletConfig",
        position=(800, 0),
    )

    # ===== 4. BulletConfig.AfterBorn 外部引用 =====
    # 经查 307048 真实样本：BulletConfig.AfterBorn 指向外部 SkillEffect 时
    # 无需 RefConfigBase 占位 + 无需字段端口边。运行时按 ConfigJson 字段值查表即可。
    # 所以这里不再建 RefConfigBase 占位节点。
    # ConfigJson 里 AfterBornSkillEffectExecuteInfo.SkillEffectConfigID = ONTICK_INIT_EID = 32300101 已经是足够的。

    # ===== 5. SkillConfig 顶层 =====
    skill_cfg_payload = {
        "ID": SKILL_ID,
        "SkillNameKey": 0,
        "SkillDescKey": 0,
        "SkillNameEditor": "PoC_旋转扩张圈",
        "SkillDescEditor": "[PoC] 旋转扩张子弹圈测试技能。N=8 颗子弹圆周分布，"
                           "vR=13单位/帧外扩，ω=90度/秒整团旋转，2秒后销毁。",
        "Icon": "Skill/Pugong/PuGong_mu",  # 占位，待用户在 Unity 替换
        "ElementType": 2,                   # 木
        "SkillSchoolResType": 0,
        "FeatureLabel": 0,
        "BDLabels": [],
        "SkillAITags": [],
        "DamageType": 1,                    # 物理
        "SkillMainType": 1,                 # 功法技
        "SkillSubType": 102,                # 木宗门人阶奇术（同 30212010）
        "MPCost": 0,
        "HunLiValue": 0,
        "SectXinfaEnergyValue": 0,
        # ⭐ 时序 4 项（GATE-3.5 自审）
        "SkillCastFrame": 0,
        "SkillBufferStartFrame": 0,
        "SkillBufferFrame": 30,             # buffer 含 base_duration（与 base 相同 → 整段都接受 buffer 输入）
        "SkillBaseDuration": 30,            # 30 帧 = 1 秒 抬手期
        "SkillCastIsNotInterruptable": False,
        "IsSkillBufferFrameCanMove": False,
        "CdType": 1,                        # 普通
        "CdTime": 900,                      # 900 帧 = 30 秒 CD（同 30212010）
        "ComboCdList": [],
        "CDMaxStoreCount": 0,
        "SkillFixCdTime": 0,
        "SkillRange": 1200,                 # = maxRadius
        "SkillMinRange": 0,
        "AISkillRange": 1200,
        "ExtraAlertRange": 0,
        "IsCloseChaseInAlertRange": True,
        "NeedTargetInRange": False,
        "IsSkillCastNoTargetInIdle": False,
        "Condition": 0,
        "AICastCondition": 0,
        # ⭐ 主入口
        "SkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 32390001},
        "SkillEffectPassiveExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "SkillEffectOnUnEquip": 0,
        "ChantCounterValuesList": [],
        "LGDamageValuesList": [],
        "SkillDamageTagsList": [],          # PoC 阶段无伤害（位移测试为主）
        "SkillTagsList": [],                # PoC 阶段调用方零 SkillTag
        "SkillTipsConditionSkillTagsList": [],
        "SkillGrowthDesc": "",
        "TalentKeyWord": [],
        "UseSkillSpeedDownValue": 0,
        "UseSkillSpeedDownTime": 0,
        # ⭐ 指示器（圆形，半径=maxRadius 与 EXT[7] 一致）
        "SkillIndicatorType": 1,            # 圆形 AOE
        "SkillIndicatorParam": [1200],      # = maxRadius
        "SkillIndicatorParamTagConfigIds": [],
        "SkillIndicatorResParam": [0],
        "SkillIndicatorResParamTagConfigIds": [],
        "LockEntityAfterUseSkillDuration": 0,
        "LockEntityPosTypeAfterUseSkill": 0,
        "SkillEffectOnSkillCastInterrupt": 0,
        "UseSkillForbidUpdateFaceDir": False,
        "UseType": 1,                       # 同 30212010
        "ButtonUpConfig": 0,
        "InterruptConfig": 0,
        "ReActiveConfig": 0,
        "SkillQuality": 2,                  # 同 30212010
        "IsPassiveSkillHideCD": False,
        "IsPassiveSkillNotRunByCD": False,
        "SkillProperty": 0,
        "SkillRangeTagConfigId": 0,
        "SkillMinRangeTagConfigId": 0,
        "SmartCastTargetBasePriority": 3,
        "SmartCastTargetCondTemplate": 1,
        "SmartCastTargetMonsterRankCond": [16, 15, 14, 13, 12, 11, 4, 5, 6, 0],
        "SmartCastTargetCampCond": [2],
        "SmartCastNoTargetIndicatorPos": 0,
        "SmartCastNoTargetCancelUse": False,
        "CastTargetCondTemplate": 1,
        "CastTargetMonsterRankCond": [16, 15, 14, 13, 12, 11, 4, 5, 6, 0],
        "CastTargetCampCond": [2],
        "IsHideContinueUseSkillHeadBar": False,
        "SkillPriority": 0,
        "EnhanceSkillBuffConfigID": 0,
        "StatisticsDamageAloneForSummon": False,
        "SkillXinfaType": 0,
    }
    add_node(
        "SkillConfigNode", SKILL_ID, skill_cfg_payload,
        desc=f"30212016 PoC_旋转扩张圈\n"
             f"木宗门人阶奇术 SubType=102\n"
             f"主入口 SkillEffectConfigID=32390001 (ORDER → RUN_TEMPLATE)",
        table_tash=TASH_SKILL_CONFIG,
        table_name="SkillConfig",
        position=(-400, 0),
    )

    return refs, edges, field_port_edges, guid_of_id


def make_sticky_notes() -> list:
    """v3 模板 5 段（团队统一）"""
    content = (
        "[作用]\n"
        "PoC 测试技能：木宗门人阶奇术。释放后在主角周围生成 8 颗飞叶子弹，圆周均匀分布，"
        "整团以 90 度/秒匀速旋转，每颗子弹同时以 13 单位/帧（约 400 单位/秒）的速度径向外扩，"
        "2 秒后超出 maxR=1200 单位边界自动销毁。圆心锁定在释放瞬间位置不跟随主角。\n\n"
        "[流程]\n"
        "OnSkillStart\n"
        "  └→ ORDER\n"
        "      └→ RUN_SKILL_EFFECT_TEMPLATE (调 v08 模板根 32300001)\n"
        "          ├ 模板 spawn 阶段：N 颗子弹同帧创建，phase 角度 2π·i/N 均布\n"
        "          ├ 每颗子弹 BulletConfig.AfterBorn=32300101 → 触发模板 OnTick 链\n"
        "          └ OnTick 每帧：θ+=ω → R+=vR → 改 X/Y → 应用位置 → maxR/minR 检查\n\n"
        "[特殊条件]\n"
        "- followPlayer=0：圆心固定在释放瞬间位置，不跟随主角\n"
        "- BulletConfig.AfterBorn 必须 = 32300101（模板 contract）\n"
        "- 子弹本体 Speed/Acce/TurnSpeed/TracePathType 全 0（位移由 OnTick 接管）\n"
        "- LastTime=60 帧（2s），LifeFlag=1（定时销毁=按 LastTime）兜底\n"
        "- 调用方完全 hard-code 参数（PT=0 常量），不声明任何 SkillTag\n"
        "- PoC 阶段无伤害挂接（验证位移轨迹优先）\n\n"
        "[参数]\n"
        "- bulletCount N = 8\n"
        "- initialRadius R0 = 200 单位 (≈2 米)\n"
        "- tangentOffsetAngle φ = 0 度（长边沿切线 / 花瓣）\n"
        "- radialVelocity vR = 13 单位/帧 (≈ 400 单位/秒)\n"
        "- radialAcceleration aR = 0\n"
        "- angularVelocity ω = 3 度/帧 (= 90 度/秒)\n"
        "- maxRadius = 1200 单位\n"
        "- minRadius = 0\n"
        "- followPlayer = 0\n"
        "- bulletConfig = 321000 (本文件内嵌)\n"
        "- BulletConfig.Model = 3200303 (复用叶散风行飞叶)\n"
        "- BulletConfig.LastTime = 60 帧 / LifeFlag = 1（定时销毁，强证据等级 2，6+真实样本印证）\n"
        "- SkillCastFrame = 0 / BaseDuration = 30 / BufferFrame = 30 / CdTime = 900\n"
        "- IndicatorType = 1 (圆形) / IndicatorParam = [1200] = maxRadius\n\n"
        "[联动]\n"
        "- 强依赖 v08 模板 SkillGraph_【模板】旋转扩张子弹圈.json (根 32300001 / OnTick 32300101)\n"
        "- 强依赖 BulletConfig 321000 的 AfterBorn=32300101 contract\n"
        "- Icon=Skill/Pugong/PuGong_mu 为占位，用户后续在 Unity 中手动替换正式美术\n"
        "- 首次 Ctrl+R 后必须在 SkillEditor 打开本技能 → 点'同步数据'让 32390000/32390001 进运行时表"
    )
    return [{
        "GUID": new_guid(),
        "position": {
            "serializedVersion": "2",
            "x": -800.0, "y": -200.0,
            "width": 700.0, "height": 1500.0,
        },
        "title": "[PoC] 30212016 旋转扩张圈 v1.0 — 调用 v08 模板",
        "content": content,
    }]


def emit(refs, edges, field_port_edges, output_path: Path):
    # 自动派生 PackedParamsOutput 边（参数引用边）
    DYN_PORT = {"TSET_ORDER_EXECUTE", "TSET_NUM_MAX", "TSET_NUM_MIN"}
    SKIP_PARAM_DERIVE = {
        "SkillTagsConfigNode", "BulletConfigNode", "ModelConfigNode",
        "RefConfigBaseNode", "SkillConfigNode",
    }
    guid_of_id = {}
    for r in refs:
        guid_of_id[r["data"]["ID"]] = r["data"]["GUID"]

    derived_edges = list(edges)
    for ref in refs:
        cls = ref["type"]["class"]
        if cls in SKIP_PARAM_DERIVE:
            continue
        try:
            cfg = json.loads(ref["data"]["ConfigJson"])
        except Exception:
            continue
        params = cfg.get("Params", [])
        is_dyn = cls in DYN_PORT
        for i, p in enumerate(params):
            if not isinstance(p, dict):
                continue
            v = p.get("Value", 0)
            pt = p.get("ParamType", 0)
            if pt in (1, 4, 5, 6) or v == 0:
                continue
            if not isinstance(v, int):
                continue
            target_guid = guid_of_id.get(v)
            if target_guid is None:
                continue
            if target_guid == ref["data"]["GUID"]:
                continue
            out_port = "0" if is_dyn else str(i)
            derived_edges.append({
                "GUID": new_guid(),
                "inputNodeGUID": target_guid,
                "outputNodeGUID": ref["data"]["GUID"],
                "inputFieldName": "ID",
                "outputFieldName": "PackedParamsOutput",
                "inputPortIdentifier": "0",
                "outputPortIdentifier": out_port,
                "isVisible": True,
            })

    all_edges = derived_edges + field_port_edges

    notes = make_sticky_notes()

    graph = {
        "serializationData": {
            "SerializedFormat": 0, "SerializedBytes": [],
            "ReferencedUnityObjects": [], "SerializedBytesString": "",
            "Prefab": {"instanceID": 0},
            "PrefabModificationsReferencedUnityObjects": [],
            "PrefabModifications": [], "SerializationNodes": [],
        },
        "nodes": [{"rid": r["rid"]} for r in refs],
        "edges": all_edges,
        "groups": [], "stackNodes": [],
        "pinnedElements": [{
            "position": {"serializedVersion": "2", "x": 0.0, "y": 0.0, "width": 511.0, "height": 629.0},
            "opened": True,
            "editorType": {
                "serializedType": "NodeEditor.ConfigPinnedView, NodeEditor, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null"
            }
        }],
        "exposedParameters": [], "serializedParameterList": [],
        "stickyNotes": notes,
        "curTab": 0,
        "path": str(output_path).replace("\\", "/").replace(str(PROJ).replace("\\", "/") + "/", ""),
        "references": {"version": 2, "RefIds": refs},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(graph, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )
    return all_edges


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    refs, edges, field_port_edges, guid_of_id = build()
    all_edges = emit(refs, edges, field_port_edges, OUTPUT)
    print(f"[OK] 30212016 PoC 旋转扩张圈 生成成功")
    print(f"  路径: {OUTPUT}")
    print(f"  节点数: {len(refs)}")
    print(f"  自动派生 PackedParamsOutput 边: {len(all_edges) - len(field_port_edges)}")
    print(f"  字段端口边: {len(field_port_edges)}")
    print(f"  总边数: {len(all_edges)}")
    ids = [r["data"]["ID"] for r in refs]
    print(f"  ID 列表: {ids}")
    print()
    print(f"  SkillConfig ID: {SKILL_ID}")
    print(f"  BulletConfig ID: {BULLET_CONFIG_ID}")
    print(f"  OnSkillStart ORDER ID: {EFFECT_BASE + 1}")
    print(f"  RUN_TEMPLATE ID: {EFFECT_BASE}")
    print(f"  外部引用 v08 模板根: {ROOT_TEMPLATE_EID}")
    print(f"  外部引用 v08 OnTick init: {ONTICK_INIT_EID}")


if __name__ == "__main__":
    main()
