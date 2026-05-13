#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30212016 【木宗门】奇术_人阶_PoC_旋转扩张圈 — v2.0 锚点子弹路线（2026-05-11 重写版）

v1 (v08 模板路线) 失败 5 轮后用户裁决重写，路线 A：
- 完全 inline v08 模板的所有 80 节点到本 SkillConfig，不再走外部模板
- ID 段位平移：32300xxx → 32390xxx (+90000)，全 8 位 ID 体系
- 所有 EXT_PARAM (PT=4) 引用替换为常量 (PT=0)，因为没有"模板调用方-参数"二元关系了
- BulletConfig.AfterBorn 指向**本 graph 内**的 OnTick init 节点 (32390101)，不再跨文件引用
- spawn 8 次 + Count=8 + Interval=1 实现"同一帧 8 颗子弹同时创建"的同步语义（假设 A，待 Unity 实测验证）

v1 失败根因 (PostMortem #030 候选)：
- BulletConfig.AfterBorn 跨文件引用模板节点 ID = 反模式 / 模板节点在调用方上下文未实例化 /
  spawn 后 OnTick 一次都没跑过 / 子弹 60 帧后 ghost 销毁

v2 关键设计：
1. 单一 BulletConfig (321000)，AfterBorn=32390101 = 本 graph 内 OnTick init ORDER
2. spawn 阶段在 caster 上下文跑：i=0 → REPEAT N 次 → 每次累 i / 算 phase / spawn 1 颗子弹
3. 每颗子弹 born 瞬间 AfterBorn 触发 OnTick init (在 entity 上下文)，跑 32390101 → 32390167 链
4. SkillTag 段 32390700-32390712 共 9 个（i / curTheta / curAbsAngle / curHeading / casterX / casterY / trajR / trajTheta / currentRadialSpeed）

数据来源：
- 用户决策 (GATE-1)：SkillID=30212016 / N=8 / R0=200 / vR=13 / ω=3度/帧 / maxR=1200
- BulletModel=3200303 复用叶散风行普通飞叶（满足 PostMortem #024 ≥4 要求）
- LastTime=60帧=2s, LifeFlag=1（定时销毁）
- v08 模板 80 节点结构 1:1 inline，仅做 ID 重映射 + EXT_PARAM 替换为常量

ID 段分配 (32390000~32390999)：
- 32390000-32390002 = OnSkillStart 包装 (RUN_TEMPLATE 已废 / 改为直接 ORDER 包模板根)
- 32390001 = OnSkillStart ORDER (主入口 / 替换原 32390001 用途)
- 32390003-32390067 = inline 模板节点 (32300003-32300067 + 90000 平移)
- 32390101 = OnTick init (被 BulletConfig.AfterBorn 引用)
- 32390500-32390502 = TSCT 比较 (32300500-502 + 90000 平移)
- 32390700-32390712 = SkillTag (32300700-712 + 90000 平移)

⚠️ Sticky Note v3 模板 5 段
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJ = Path(r"<<PROJECT_ROOT_WIN>>")
OUTPUT = PROJ / "<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212016【木宗门】奇术_人阶_PoC_旋转扩张圈.json"

V08_TEMPLATE = PROJ / "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】旋转扩张子弹圈.json"

# ===== 关键 ID =====
SKILL_ID                = 30212016
BULLET_CONFIG_ID        = 321000     # 全局扫描验证未占用
ID_SHIFT                = 90000      # 32300xxx -> 32390xxx 平移量
ONSTART_ORDER_ID        = 32390001   # OnSkillStart ORDER 主入口（包装模板根 32390001 — 注意 32300001 + 90000 = 32390001 自然冲突 / 我们让其同义复用）
TEMPLATE_ROOT_REMAP     = 32300001 + ID_SHIFT  # 32390001 = 模板根 / 也是 OnSkillStart 入口
ONTICK_INIT_REMAP       = 32300101 + ID_SHIFT  # 32390101 = BulletConfig.AfterBorn 目标

# ===== TableTash =====
TASH_SKILL_EFFECT    = "0CFA05568A66FEA1DF3BA6FE40DB7080"
TASH_BULLET_CONFIG   = "A4AEA1F4B1BD0FA9FD2F066BE902466F"
TASH_SKILL_CONFIG    = "1B07683FF8D5DAE7F1CB4F2B3F22A2C7"
TASH_SKILL_TAG       = "DE5DE0DAE6F02D63DB4810E3DD96C4A5"  # 待校核 / 用模板里 SkillTag 节点真实 TableTash

# ===== TSkillEffectType =====
ET_ORDER, ET_REPEAT = 1, 3

# ===== TParamType =====
PT_NULL, PT_ATTR, PT_FUNC_RET, PT_SKILL_PARAM, PT_EXTRA_PARAM, PT_COMMON_PARAM = 0, 1, 2, 3, 4, 5

# ===== EXT_PARAM 实参 (GATE-1 用户裁决值) =====
# 模板里所有 PT=4 V=k 替换为 PT=0 V=EXT_VALUES[k]
EXT_VALUES = {
    1:  8,    # bulletCount N
    2:  200,  # initialRadius R0
    3:  0,    # tangentOffsetAngle phi
    4:  13,   # radialVelocity vR
    5:  0,    # radialAcceleration aR
    6:  3,    # angularVelocity omega (度/帧)
    7:  1200, # maxRadius
    8:  0,    # minRadius
    9:  0,    # followPlayer
    10: BULLET_CONFIG_ID,  # 内嵌 bulletConfig
}


def new_guid() -> str:
    return str(uuid.uuid4())


def remap_value(value: int, param_type: int) -> tuple[int, int]:
    """ID 平移 + EXT_PARAM 替换。返回 (new_value, new_param_type)"""
    # PT=4 (EXT_PARAM) -> PT=0 常量
    if param_type == PT_EXTRA_PARAM and value in EXT_VALUES:
        return EXT_VALUES[value], PT_NULL

    # PT=0 (常量直接 ID) / PT=2 (函数返回引用) — 如果值在 32300xxx 段则平移
    if param_type in (PT_NULL, PT_FUNC_RET):
        if isinstance(value, int) and 32300001 <= value <= 32300999:
            return value + ID_SHIFT, param_type

    return value, param_type


def remap_payload_ids(cfg: dict) -> dict:
    """对 ConfigJson 整个 payload 做 ID 平移：ID 字段 + Params 数组里的 ID 引用"""
    new_cfg = {}
    for k, v in cfg.items():
        if k == "ID" and isinstance(v, int) and 32300001 <= v <= 32300999:
            new_cfg[k] = v + ID_SHIFT
        elif k == "Params" and isinstance(v, list):
            new_params = []
            for p in v:
                if isinstance(p, dict):
                    new_v, new_pt = remap_value(p.get("Value", 0), p.get("ParamType", 0))
                    new_params.append({
                        "Value": new_v,
                        "ParamType": new_pt,
                        "Factor": p.get("Factor", 0),
                    })
                else:
                    new_params.append(p)
            new_cfg[k] = new_params
        else:
            new_cfg[k] = v
    return new_cfg


def load_template_nodes() -> list[dict]:
    """读 v08 模板，返回所有 80 节点（深拷贝），ID 已平移 + EXT_PARAM 已替换为常量"""
    if not V08_TEMPLATE.exists():
        raise FileNotFoundError(f"v08 模板不存在: {V08_TEMPLATE}")
    d = json.loads(V08_TEMPLATE.read_text(encoding="utf-8"))
    src_refs = d["references"]["RefIds"]

    out_nodes = []
    for sref in src_refs:
        cls = sref["type"]["class"]
        sdata = sref["data"]
        sid = sdata.get("ID")

        # 跳过模板根节点本身（32300001）— 我们会用 32390001 作 OnSkillStart 入口替代
        # 但要保留它的 ConfigJson 内容（即 ORDER → [32300003, 32300029] 这个调用链结构）
        # 所以这里不跳过 / 只是 IsTemplate 改 False / 把它当普通 ORDER 节点
        new_data = dict(sdata)
        new_id = sid + ID_SHIFT if isinstance(sid, int) and 32300001 <= sid <= 32300999 else sid
        new_data["ID"] = new_id
        new_data["GUID"] = new_guid()
        new_data["IsTemplate"] = False
        new_data["TemplateFlags"] = 0
        new_data["TemplateParams"] = []
        new_data["TemplateParamsDesc"] = []
        new_data["TemplateParamsCustomAdd"] = False

        # 重映射 ConfigJson 里的 ID + Params
        try:
            cfg = json.loads(sdata["ConfigJson"])
            new_cfg = remap_payload_ids(cfg)
            new_data["ConfigJson"] = json.dumps(new_cfg, ensure_ascii=False, separators=(",", ":"))
            new_data["Config2ID"] = f"{_table_for_cls(cls)}_{new_id}"
        except Exception as e:
            print(f"[WARN] cls={cls} id={sid} ConfigJson parse 失败: {e}")

        # 修正 Desc 编码 (源文件有 GBK 乱码)
        old_desc = sdata.get("Desc", "")
        if isinstance(old_desc, str):
            new_data["Desc"] = old_desc  # 保留原文 / 否则会丢

        out_nodes.append({
            "rid": None,  # 留空 / 在最终组装时统一分配
            "type": dict(sref["type"]),
            "data": new_data,
        })
    return out_nodes


def _table_for_cls(cls: str) -> str:
    """class -> 表名（用于 Config2ID 拼接）"""
    if cls in ("SkillConfigNode",):
        return "SkillConfig"
    if cls in ("BulletConfigNode",):
        return "BulletConfig"
    if cls in ("SkillTagsConfigNode",):
        return "SkillTagsConfig"
    if cls in ("ModelConfigNode",):
        return "ModelConfig"
    if cls in ("BuffConfigNode",):
        return "BuffConfig"
    if cls in ("RefConfigBaseNode",):
        return "RefConfig"
    return "SkillEffectConfig"


def _tash_for_cls(cls: str) -> str:
    """class -> TableTash"""
    if cls == "SkillConfigNode":
        return TASH_SKILL_CONFIG
    if cls == "BulletConfigNode":
        return TASH_BULLET_CONFIG
    if cls == "SkillTagsConfigNode":
        return TASH_SKILL_TAG
    return TASH_SKILL_EFFECT


def build():
    refs = []
    next_rid = 1000

    def assign_rid_and_position(node: dict, position=None) -> dict:
        nonlocal next_rid
        node["rid"] = next_rid
        next_rid += 1
        d = node["data"]
        d["computeOrder"] = node["rid"] - 1000
        if position is not None:
            d.setdefault("position", {})
            d["position"] = {
                "serializedVersion": "2",
                "x": float(position[0]), "y": float(position[1]),
                "width": 280.0, "height": 200.0,
            }
        else:
            # 保留模板里的相对位置 + 整体偏移避免和新节点重叠
            d.setdefault("position", {})
            cur = d.get("position", {})
            d["position"] = {
                "serializedVersion": "2",
                "x": float(cur.get("x", 0.0)) + 1500.0,
                "y": float(cur.get("y", 0.0)),
                "width": float(cur.get("width", 280.0)),
                "height": float(cur.get("height", 200.0)),
            }
        # 默认字段
        for k, dv in [("expanded", False), ("debug", False), ("nodeLock", False),
                       ("visible", True), ("hideChildNodes", False),
                       ("hideCounter", 0)]:
            d.setdefault(k, dv)
        d.setdefault("hidePos", {"x": 0.0, "y": 0.0})
        # 修正 TableTash（模板里 SkillTag 等节点 TableTash 我们覆写为本工程认定值）
        cls = node["type"]["class"]
        # 不强行改 TableTash / 保留模板原始
        return node

    # ===== 1. 加载并 inline 模板 80 节点 =====
    template_nodes = load_template_nodes()

    # 把模板根 (原 32300001 / 平移后 32390001) 单独找出来，标记为 OnSkillStart 入口
    # 其余按原顺序 append
    for n in template_nodes:
        assign_rid_and_position(n)
        refs.append(n)

    # ===== 2. 内嵌 BulletConfig (321000) =====
    bullet_payload = {
        "ID": BULLET_CONFIG_ID,
        "Model": 3200303,                # 复用叶散风行飞叶
        "ModelBaseScalePercent": 100,
        "Speed": 0,                      # 位移由 OnTick 接管
        "AcceSpeed": 0,
        "MaxSpeed": 0,
        "TurnSpeed": 0,
        "MaxTurnSpeed": 0,
        "TurnAcceSpeed": 0,
        "PitchTurnSpeed": 0,
        "PitchMaxTurnSpeed": 0,
        "PitchTurnAcceSpeed": 0,
        "TracePathType": 0,
        "TracePathParams": [],
        "AngleAdjustType": 0,
        "FlyType": 0,
        "Hp": 0,
        "ATK": 0,
        "MaxDistance": 0,
        "LastTime": 60,                  # 60 帧 = 2 秒
        "LifeFlag": 1,                   # 1 = 定时销毁
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
        "BeforeBornSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "AfterBornSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": ONTICK_INIT_REMAP},  # ⭐ 32390101
        "DieSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "DisappearEffect": 0,
        "delayDestroyTime": 0,
    }
    bullet_node = {
        "rid": next_rid,
        "type": {"class": "BulletConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": new_guid(),
            "computeOrder": next_rid - 1000,
            "position": {"serializedVersion": "2", "x": -2000.0, "y": 0.0, "width": 280.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": BULLET_CONFIG_ID,
            "Desc": (f"内嵌 BulletConfig {BULLET_CONFIG_ID}\n"
                     f"Model=3200303 (复用叶散风行飞叶)\n"
                     f"Speed/Acce/Turn/Trace 全 0 (位移由 OnTick 接管)\n"
                     f"LastTime=60帧=2s LifeFlag=1(定时销毁)\n"
                     f"⭐ AfterBorn={ONTICK_INIT_REMAP} → 触发 inline OnTick init"),
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": TASH_BULLET_CONFIG,
            "ConfigJson": json.dumps(bullet_payload, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"BulletConfig_{BULLET_CONFIG_ID}",
        },
    }
    refs.append(bullet_node)
    next_rid += 1

    # ===== 3. SkillConfig 顶层 =====
    skill_cfg_payload = {
        "ID": SKILL_ID,
        "SkillNameKey": 0,
        "SkillDescKey": 0,
        "SkillNameEditor": "PoC_旋转扩张圈",
        "SkillDescEditor": "[PoC v2 锚点子弹路线] 旋转扩张子弹圈测试技能。N=8 颗子弹圆周分布，"
                           "vR=13单位/帧外扩，ω=90度/秒整团旋转，2秒后销毁。",
        "Icon": "Skill/Pugong/PuGong_mu",
        "ElementType": 2,                # 木
        "SkillSchoolResType": 0,
        "FeatureLabel": 0,
        "BDLabels": [],
        "SkillAITags": [],
        "DamageType": 1,                 # 物理
        "SkillMainType": 1,              # 功法技
        "SkillSubType": 102,             # 木宗门人阶奇术
        "MPCost": 0,
        "HunLiValue": 0,
        "SectXinfaEnergyValue": 0,
        "SkillCastFrame": 0,
        "SkillBufferStartFrame": 0,
        "SkillBufferFrame": 30,
        "SkillBaseDuration": 30,
        "SkillCastIsNotInterruptable": False,
        "IsSkillBufferFrameCanMove": False,
        "CdType": 1,
        "CdTime": 900,
        "ComboCdList": [],
        "CDMaxStoreCount": 0,
        "SkillFixCdTime": 0,
        "SkillRange": 1200,              # = maxRadius
        "SkillMinRange": 0,
        "AISkillRange": 1200,
        "ExtraAlertRange": 0,
        "IsCloseChaseInAlertRange": True,
        "NeedTargetInRange": False,
        "IsSkillCastNoTargetInIdle": False,
        "Condition": 0,
        "AICastCondition": 0,
        # ⭐ 主入口：直接指向模板根 (已平移到 32390001)，它本身就是 ORDER → [预初始化, REPEAT]
        "SkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": TEMPLATE_ROOT_REMAP},
        "SkillEffectPassiveExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "SkillEffectOnUnEquip": 0,
        "ChantCounterValuesList": [],
        "LGDamageValuesList": [],
        "SkillDamageTagsList": [],
        "SkillTagsList": [],             # PoC 阶段无技能级 SkillTag (entity 级 9 个已 inline)
        "SkillTipsConditionSkillTagsList": [],
        "SkillGrowthDesc": "",
        "TalentKeyWord": [],
        "UseSkillSpeedDownValue": 0,
        "UseSkillSpeedDownTime": 0,
        "SkillIndicatorType": 1,         # 圆形 AOE
        "SkillIndicatorParam": [1200],
        "SkillIndicatorParamTagConfigIds": [],
        "SkillIndicatorResParam": [0],
        "SkillIndicatorResParamTagConfigIds": [],
        "LockEntityAfterUseSkillDuration": 0,
        "LockEntityPosTypeAfterUseSkill": 0,
        "SkillEffectOnSkillCastInterrupt": 0,
        "UseSkillForbidUpdateFaceDir": False,
        "UseType": 1,
        "ButtonUpConfig": 0,
        "InterruptConfig": 0,
        "ReActiveConfig": 0,
        "SkillQuality": 2,
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
    skill_node = {
        "rid": next_rid,
        "type": {"class": "SkillConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": new_guid(),
            "computeOrder": next_rid - 1000,
            "position": {"serializedVersion": "2", "x": -2400.0, "y": 0.0, "width": 280.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": SKILL_ID,
            "Desc": (f"30212016 PoC_旋转扩张圈 v2 锚点子弹路线\n"
                     f"木宗门人阶奇术 SubType=102\n"
                     f"主入口 SkillEffectConfigID={TEMPLATE_ROOT_REMAP} (inline ORDER → 预初始化 + REPEAT N)"),
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": TASH_SKILL_CONFIG,
            "ConfigJson": json.dumps(skill_cfg_payload, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillConfig_{SKILL_ID}",
        },
    }
    refs.append(skill_node)
    next_rid += 1

    return refs


def make_sticky_notes() -> list:
    """v3 模板 5 段（团队统一） — v2 锚点子弹路线"""
    content = (
        "[作用]\n"
        "PoC 测试技能：木宗门人阶奇术 v2 锚点子弹路线。释放后在主角周围生成 8 颗飞叶子弹，"
        "圆周均匀分布，整团以 90 度/秒匀速旋转，每颗子弹同时以 13 单位/帧（约 400 单位/秒）的"
        "速度径向外扩，2 秒后超出 maxR=1200 单位边界自动销毁。圆心锁定释放瞬间位置不跟随。\n\n"

        "[流程]\n"
        "OnSkillStart\n"
        "  └→ ORDER (32390001) - 模板根 inline\n"
        "      ├→ 预初始化 (32390003) - 设 i=0 (entity 级 SkillTag)\n"
        "      └→ REPEAT N=8 (32390029) - 每次 i++ → 算 phase → spawn 子弹\n"
        "          └→ ORDER (32390028) - 单次发射子链\n"
        "              ├→ i++ (累计当前序号)\n"
        "              ├→ 算 θ_i = (i-1) × 360 / N (角度均布)\n"
        "              ├→ 算 abs_angle = caster.facing + θ_i\n"
        "              ├→ 算 heading = abs_angle + 90 + φ (切线方向)\n"
        "              ├→ 算 spawn_X = caster.X + R0 × cos(abs_angle)\n"
        "              ├→ 算 spawn_Y = caster.Y + R0 × sin(abs_angle)\n"
        "              └→ CREATE_BULLET 321000 (heading=切线 / X=spawn_X / Y=spawn_Y)\n"
        "                  └→ AfterBorn (entity 上下文) = 32390101 OnTick init\n"
        "                      ├→ trajR = R0 (实弹级)\n"
        "                      ├→ trajTheta = facing - 90 - φ (弹自身参数 θ_0)\n"
        "                      ├→ X0 = caster.X / Y0 = caster.Y\n"
        "                      ├→ currentRadialSpeed = vR\n"
        "                      └→ OnTick REPEAT 32390067 (每帧)\n"
        "                          └→ ORDER 32390066 (frame 链):\n"
        "                              ├ θ += ω/帧\n"
        "                              ├ curRadSpd += aR/30\n"
        "                              ├ R += curRadSpd\n"
        "                              ├ if followPlayer: 刷新 X0/Y0\n"
        "                              ├ newX = X0 + R × cos(θ) / 10000\n"
        "                              ├ newY = Y0 + R × sin(θ) / 10000\n"
        "                              ├ 子弹.X = newX / 子弹.Y = newY\n"
        "                              ├ 应用位置变更\n"
        "                              ├ if R > maxR: DESTROY\n"
        "                              └ if R < minR: DESTROY\n\n"

        "[特殊条件]\n"
        "- followPlayer=0：圆心固定在释放瞬间位置，不跟随主角\n"
        "- BulletConfig.AfterBorn 必须 = 32390101 (本 graph inline OnTick init)\n"
        "- 子弹本体 Speed/Acce/TurnSpeed/TracePathType 全 0 (位移由 OnTick 接管)\n"
        "- LastTime=60 帧 (2s) / LifeFlag=1 (定时销毁) 兜底\n"
        "- 8 颗子弹同帧 spawn (REPEAT Count=8 + Interval=1)，OnTick 同步对齐 (假设 A，待 Unity 实测)\n"
        "- 调用方完全 hard-code 参数 (PT=0 常量)，无 EXT_PARAM 间接 / 无外部模板依赖\n"
        "- PoC 阶段无伤害挂接 (验证位移轨迹优先)\n\n"

        "[参数]\n"
        "- bulletCount N = 8\n"
        "- initialRadius R0 = 200 (≈2 米)\n"
        "- tangentOffsetAngle φ = 0 度 (沿切线 / 花瓣)\n"
        "- radialVelocity vR = 13 单位/帧 (≈ 400 单位/秒)\n"
        "- radialAcceleration aR = 0\n"
        "- angularVelocity ω = 3 度/帧 (= 90 度/秒)\n"
        "- maxRadius = 1200\n"
        "- minRadius = 0\n"
        "- followPlayer = 0\n"
        "- bulletConfig = 321000 (本文件内嵌)\n"
        "- BulletConfig.Model = 3200303 (复用叶散风行飞叶)\n"
        "- BulletConfig.LastTime = 60 帧 / LifeFlag = 1\n"
        "- SkillCastFrame = 0 / BaseDuration = 30 / BufferFrame = 30 / CdTime = 900\n"
        "- IndicatorType = 1 (圆形) / IndicatorParam = [1200] = maxRadius\n\n"

        "[联动]\n"
        "- v1 v08 模板路线已废 (备份于 doc/SkillAI/samples/json/SkillGraph_30212016_v1_failed_*.json)\n"
        "- v2 自给自足：所有 80 节点 inline / 无外部 SkillEffect 引用 / 无 RUN_TEMPLATE 调用\n"
        "- ID 段位 32390000-32390999 / SkillTag 段 32390700-32390712 (9 个 entity 级)\n"
        "- Icon=Skill/Pugong/PuGong_mu 占位 / 用户后续在 Unity 替换正式美术\n"
        "- 首次 Ctrl+R 后必须在 SkillEditor 打开本技能 → 点 '同步数据' 让所有 32390xxx 进运行时表"
    )
    return [{
        "GUID": new_guid(),
        "position": {
            "serializedVersion": "2",
            "x": -2800.0, "y": -300.0,
            "width": 800.0, "height": 1900.0,
        },
        "title": "[PoC v2] 30212016 旋转扩张圈 — 锚点子弹路线（80 节点全 inline）",
        "content": content,
    }]


def emit(refs: list, output_path: Path):
    # 自动派生 PackedParamsOutput 边
    DYN_PORT = {"TSET_ORDER_EXECUTE", "TSET_REPEAT_EXECUTE", "TSET_NUM_MAX", "TSET_NUM_MIN"}
    SKIP_PARAM_DERIVE = {
        "SkillTagsConfigNode", "BulletConfigNode", "ModelConfigNode",
        "RefConfigBaseNode", "SkillConfigNode",
    }

    guid_of_id: dict[int, str] = {}
    for r in refs:
        rid_id = r["data"].get("ID")
        if rid_id is not None:
            guid_of_id[rid_id] = r["data"]["GUID"]

    edges = []
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
            edges.append({
                "GUID": new_guid(),
                "inputNodeGUID": target_guid,
                "outputNodeGUID": ref["data"]["GUID"],
                "inputFieldName": "ID",
                "outputFieldName": "PackedParamsOutput",
                "inputPortIdentifier": "0",
                "outputPortIdentifier": out_port,
                "isVisible": True,
            })

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
        "edges": edges,
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
    return edges


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    refs = build()
    edges = emit(refs, OUTPUT)
    print(f"[OK] 30212016 PoC v2 锚点子弹路线 生成成功")
    print(f"  路径: {OUTPUT}")
    print(f"  节点数: {len(refs)}")
    print(f"  自动派生 PackedParamsOutput 边: {len(edges)}")
    print()
    print(f"  SkillConfig ID: {SKILL_ID}")
    print(f"  BulletConfig ID: {BULLET_CONFIG_ID}")
    print(f"  OnSkillStart 入口 (= 模板根 inline): {TEMPLATE_ROOT_REMAP}")
    print(f"  BulletConfig.AfterBorn → OnTick init: {ONTICK_INIT_REMAP}")
    print()
    # 节点分类统计
    cls_count = {}
    for r in refs:
        cls = r["type"]["class"]
        cls_count[cls] = cls_count.get(cls, 0) + 1
    print(f"  节点分类:")
    for cls, c in sorted(cls_count.items(), key=lambda x: -x[1]):
        print(f"    {cls}: {c}")


if __name__ == "__main__":
    main()
