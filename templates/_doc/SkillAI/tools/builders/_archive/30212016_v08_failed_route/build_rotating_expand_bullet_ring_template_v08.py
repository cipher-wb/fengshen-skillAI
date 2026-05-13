#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旋转扩张子弹圈 — SkillEditor 通用技能模板生成器（v1.0）

设计结论（2026-05-09）：
- 老模板废弃，不再内置凭空 BulletConfig，也不暴露不消费的 lifetime / damagePerHit / pierceCount。
- 模板只负责几何运动：N 颗子弹同帧出生，圆周均布，AfterBorn 后逐帧按
  θ += angularVelocity、R += radialVelocity + radialAcceleration / 30 更新位置。
- 子弹外观、寿命、伤害、穿透和命中链路全部归调用方传入的 BulletConfig 管。
- 调用方传入的 BulletConfig 必须满足 contract：
  AfterBornSkillEffectExecuteInfo.SkillEffectConfigID = 32300101。

TemplateParams（全部真消费）：
[1]  bulletCount                 默认 8     REPEAT 同帧出生次数，建议 <= 50
[2]  initialRadius               默认 200   项目坐标单位，1 米 = 100 单位
[3]  tangentOffsetAngle          默认 0     度，0=长边沿切线，90=长边沿径向
[4]  radialVelocity              默认 10    单位/帧，正外扩，负内收
[5]  radialAcceleration          默认 0     单位/秒²，模板内每帧加 aR / 30
[6]  angularVelocity             默认 3     度/帧，正逆时针，负顺时针
[7]  maxRadius                   默认 1500  R > maxRadius 时销毁子弹
[8]  minRadius                   默认 0     R < minRadius 时销毁子弹
[9]  followPlayer                默认 0     0=锁定释放瞬间圆心，1=圆心逐帧跟随主角
[10] bulletConfig                必填       真实 BulletConfig.ID，需接 AfterBorn=32300101

参考：
- 30212010 叶散风行：AfterBorn 驱动每帧更新链路原型。
- 108_0001 环形扩散子弹：外部 BulletConfig + contract 模式参考。
- PostMortem #023：lifetime / damagePerHit 归 BulletConfig，模板不越权。
- PostMortem #026：同帧 RepeatExecute 次数建议 <= 50。
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJ = Path(r"<<PROJECT_ROOT_WIN>>")
OUTPUT = PROJ / "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】旋转扩张子弹圈.json"

# ===== ID 段位 =====
ROOT_TEMPLATE_EID = 32300001  # 模板根 EID（固定）
EFFECT_BASE       = 32300002
COND_BASE         = 32300500
TAG_BASE          = 32300700
ONTICK_INIT_EID   = 32300101  # OnTick contract 入口，外部 BulletConfig.AfterBorn 指向这里

TAG_IDS = {
    "i":            TAG_BASE + 0,
    "curTheta":     TAG_BASE + 1,
    "curAbsAngle":  TAG_BASE + 2,
    "curHeading":   TAG_BASE + 3,
    "casterX":      TAG_BASE + 4,
    "casterY":      TAG_BASE + 5,
    "trajR":             TAG_BASE + 10,
    "trajTheta":         TAG_BASE + 11,
    "currentRadialSpeed": TAG_BASE + 12,
}

# ===== TableTash =====
TASH_SKILL_EFFECT    = "0CFA05568A66FEA1DF3BA6FE40DB7080"
TASH_SKILL_TAGS      = "6A8A6883BDFDA1411BB2461E65CB2D9B"
TASH_SKILL_CONDITION = "ED89F46EAB95F7ACF5C1911A5A375278"
TASH_BULLET_CONFIG   = "A4AEA1F4B1BD0FA9FD2F066BE902466F"  # 来自 1860216 BulletConfigNode
TASH_MODEL_CONFIG    = "7BA4FA1BC830D2432EDD3669D84C3C9A"  # 来自 30212009 ModelConfigNode

# ===== TSkillEffectType =====
ET = {
    "ORDER":          1,
    "DELAY":          2,
    "REPEAT":         3,
    "BULLET":         8,
    "GET_FIXTURE_CENTER_Z": 367,
    "ANGLE_DIST_X":  73,
    "ANGLE_DIST_Y":  74,
    "CALC":          31,
    "GET_ATTR":      32,
    "MODIFY_TAG":    46,
    "GET_TAG":       48,
    "MODIFY_ATTR":   12,
    "CHANGE_POS":    22,
    "MATH_SIN":      50,
    "MATH_COS":      51,
    "ANGLE_BETWEEN": 59,
    "ADD_TAG":       97,
    "CONDITION_EXECUTE": 47,
    "DESTROY_ENTITY":    24,
}

# ===== TSkillConditionType =====
CT = {
    "AND":           1,
    "VALUE_COMPARE": 7,
}

# ===== TConditionOperator (C# 真值，common.nothotfix.cs L7929) =====
CMP_EQ, CMP_NEQ, CMP_GT, CMP_GE, CMP_LT, CMP_LE = 1, 2, 3, 4, 5, 6
# 数值运算符 TNumOperators
OP_ADD, OP_MINUS, OP_MULTI, OP_DIV = 3, 4, 5, 6
# ParamType (TParamType)
PT_NULL, PT_ATTR, PT_FUNC_RET, PT_SKILL_PARAM, PT_EXTRA_PARAM, PT_COMMON_PARAM = 0, 1, 2, 3, 4, 5


# ===== Builder =====
class TplBuilder:
    def __init__(self):
        self.refs = []
        self.edges = []
        self.field_port_edges = []  # 字段端口边（当前 v1.0 不使用，保留通用 builder 能力）
        self.next_rid = 1000
        self.next_eid = EFFECT_BASE
        self.next_cid = COND_BASE
        self.guid_of_id: dict[int, str] = {}
        self._auto_y = 0

    def _new_guid(self) -> str:
        return str(uuid.uuid4())

    def _alloc_rid(self) -> int:
        v = self.next_rid; self.next_rid += 1; return v

    def alloc_eid(self) -> int:
        v = self.next_eid; self.next_eid += 1; return v

    def alloc_cid(self) -> int:
        v = self.next_cid; self.next_cid += 1; return v

    def add_node(self, cls: str, config_id: int, config_payload: dict,
                 *, is_template: bool = False, template_params: list = None,
                 desc: str = "", table_tash: str = TASH_SKILL_EFFECT,
                 effect_type: int = None, condition_type: int = None,
                 position=None,
                 table_name_for_config2id: str = "SkillEffectConfig",
                 extra_data: dict = None) -> str:
        guid = self._new_guid()
        rid = self._alloc_rid()
        if position is None:
            position = (0.0, float(self._auto_y))
            self._auto_y += 100
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
            "IsTemplate": is_template,
            "TemplateFlags": 0,
            "TemplateParams": template_params or [],
            "TemplateParamsDesc": [p["Name"] for p in (template_params or [])],
            "TemplateParamsCustomAdd": False,
            "TableTash": table_tash,
            "ConfigJson": json.dumps(config_payload, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"{table_name_for_config2id}_{config_id}",
        }
        if effect_type is not None:
            data["SkillEffectType"] = effect_type
        if condition_type is not None:
            data["SkillConditionType"] = condition_type
        if extra_data:
            data.update(extra_data)
        self.refs.append({
            "rid": rid,
            "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
            "data": data,
        })
        self.guid_of_id[config_id] = guid
        return guid

    def add_field_port_edge(self, src_node_id: int, dst_node_id: int, field_path: str):
        """在两个节点间添加字段端口边。
        edge.outputFieldName = "PackedMembersOutput"
        edge.outputPortIdentifier = field_path  (如 "Model" 或 "AfterBornSkillEffectExecuteInfo.SkillEffectConfigID")
        语义：dst_node 的 ConfigJson 字段 field_path 引用 src_node 的 ID。
        """
        src_guid = self.guid_of_id[src_node_id]
        dst_guid = self.guid_of_id[dst_node_id]
        self.field_port_edges.append({
            "GUID": self._new_guid(),
            "inputNodeGUID": src_guid,         # ID 输入端（被引用方，自身 ID 出端口连入）
            "outputNodeGUID": dst_guid,        # 拥有字段的节点（如 BulletConfig）
            "inputFieldName": "ID",
            "outputFieldName": "PackedMembersOutput",
            "inputPortIdentifier": "0",
            "outputPortIdentifier": field_path,
            "isVisible": True,
        })

    def emit(self, output_path: Path, sticky_notes: list = None):
        # 自动建边（PackedParamsOutput 参数引用）
        DYN_PORT = {"TSET_ORDER_EXECUTE", "TSET_NUM_MAX", "TSET_NUM_MIN"}
        SKIP_PARAM_DERIVE = {
            "SkillTagsConfigNode", "BulletConfigNode", "ModelConfigNode",
            "RefConfigBaseNode",
        }
        for ref in self.refs:
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
                target_guid = self.guid_of_id.get(v)
                if target_guid is None:
                    continue
                if target_guid == ref["data"]["GUID"]:
                    continue
                out_port = "0" if is_dyn else str(i)
                self.edges.append({
                    "GUID": self._new_guid(),
                    "inputNodeGUID": target_guid,
                    "outputNodeGUID": ref["data"]["GUID"],
                    "inputFieldName": "ID",
                    "outputFieldName": "PackedParamsOutput",
                    "inputPortIdentifier": "0",
                    "outputPortIdentifier": out_port,
                    "isVisible": True,
                })

        # 合并字段端口边到 edges 列表。
        all_edges = self.edges + self.field_port_edges

        graph = {
            "serializationData": {
                "SerializedFormat": 0, "SerializedBytes": [],
                "ReferencedUnityObjects": [], "SerializedBytesString": "",
                "Prefab": {"instanceID": 0},
                "PrefabModificationsReferencedUnityObjects": [],
                "PrefabModifications": [], "SerializationNodes": [],
            },
            "nodes": [{"rid": r["rid"]} for r in self.refs],
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
            "stickyNotes": sticky_notes or [],
            "curTab": 0,
            "path": str(output_path).replace("\\", "/").replace(str(PROJ).replace("\\", "/") + "/", ""),
            "references": {"version": 2, "RefIds": self.refs},
        }
        output_path.write_text(
            json.dumps(graph, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )


def P(value, pt=PT_NULL, factor=0):
    """构造 Param dict（防 Python bool 透出 — PostMortem #007）"""
    return {
        "Value": int(value) if isinstance(value, bool) else value,
        "ParamType": pt,
        "Factor": factor,
    }


# 模板参数索引 (1-based, PT=4 EXTRA_PARAM)
EXT_N           = 1
EXT_R0          = 2
EXT_PHI         = 3
EXT_VR          = 4
EXT_AR          = 5
EXT_OMEGA       = 6
EXT_MAX_R       = 7
EXT_MIN_R       = 8
EXT_FOLLOW      = 9
EXT_BULLET_CFG  = 10  # CREATE_BULLET.Params[0] 引用此槽位，必须传真实 BulletConfig.ID


# 用户层提示：1 米 = 100 单位 / 1 秒 = 30 帧。
# lifetime / damagePerHit / pierceCount 由 BulletConfig 自己管，不在模板参数里暴露。
TPARAMS = [
    # [1] bulletCount N
    {"DefaultValueDesc": "bulletCount：子弹数量 N。单帧同时生成的子弹个数（spawn 循环 RepeatExecute 次数）。\n"
                         "⚠️ N ≤ 50 安全；超过 100 触发引擎保护。超过 ~100 会触发 C++ 引擎 RepeatExecute 单帧次数上限保护"
                         "（报错 \"Execute Count Too Big\"，详见 PostMortem #026）。",
     "Name": "[阵型] bulletCount 子弹数N", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":8,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [2] initialRadius R0
    {"DefaultValueDesc": "initialRadius：起始半径。单位为项目坐标单位，1 米 = 100 单位；默认 200 单位 = 2 米。",
     "Name": "[阵型] initialRadius 初始半径R0",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":200,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [3] tangentOffsetAngle φ
    {"DefaultValueDesc": "tangentOffsetAngle：切线偏移角，单位度。0=长边沿切线（花瓣），90=长边沿径向。",
     "Name": "[阵型] tangentOffsetAngle 切线偏移角φ(度)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [4] radialVelocity vR
    {"DefaultValueDesc": "radialVelocity：径向速度，单位/帧。正值=向外飞，负值=向内收。默认 10/帧 ≈ 300单位/秒。",
     "Name": "[运动] radialVelocity 径向速度vR(单位/帧)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":10,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [5] radialAcceleration aR
    {"DefaultValueDesc": "radialAcceleration：径向加速度，单位/秒²。模板内每帧把 currentRadialSpeed 增加 aR/30。",
     "Name": "[运动] radialAcceleration 径向加速度aR(单位/秒²)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [6] angularVelocity ω
    {"DefaultValueDesc": "angularVelocity：整团角速度，单位度/帧。正值=逆时针，负值=顺时针。默认 3°/帧 = 90°/秒。",
     "Name": "[运动] angularVelocity 整团角速度ω(度/帧)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":3,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [7] maxRadius
    {"DefaultValueDesc": "maxRadius：最大半径上限，单位为项目坐标单位。R 超过则销毁子弹。默认 1500 单位 = 15 米。",
     "Name": "[终止] maxRadius(最大半径)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":1500,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [8] minRadius
    {"DefaultValueDesc": "minRadius：最小半径下限，单位为项目坐标单位。R 小于则销毁子弹；收缩玩法建议调高。",
     "Name": "[终止] minRadius(最小半径)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [9] followPlayer
    {"DefaultValueDesc": "followPlayer：0=圆心固定在释放瞬间位置；1=每帧跟随 caster。默认 0，符合需求文档的脱手解耦。",
     "Name": "[运动] followPlayer(是否跟随主角)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [10] bulletConfig
    {"DefaultValueDesc": "bulletConfig：必填。传入一个真实存在于 BulletConfig 表的子弹 ID。\n"
                         "前提条件（contract）：该 BulletConfig 的 "
                         "AfterBornSkillEffectExecuteInfo.SkillEffectConfigID 必须 = 32300101。\n"
                         "32300101 是本模板暴露的 OnTick 入口 effect。\n"
                         "不满足此约定 → 子弹能创建但不会绕主角旋转扩张（OnTick 链不触发）。\n"
                         "lifetime / damagePerHit / pierceCount 均在该 BulletConfig 或其命中链路里配置。",
     "Name": "[子弹] bulletConfig 子弹ID(BulletConfig)",
     "RefTypeName": "BulletConfig", "RefPortTypeNames": "",
     "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": True, "isEnum": False,
     "RefTableFullName": "TableDR.BulletConfig",
     "RefTableManagerName": "TableDR.BulletConfigManager",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
]


def build():
    b = TplBuilder()

    # ----- SkillTagsConfigNode 集合：9 个运行时中间量 -----
    for name, tid in TAG_IDS.items():
        payload = {"ID": tid, "TagType": 0, "Desc": f"_旋转扩张_{name}",
                   "NameKey": 0, "DefaultValue": 0, "FinalValueEffectID": 0,
                   "RetainWhenDie": False}
        b.add_node("SkillTagsConfigNode", tid, payload,
                   desc=f"_旋转扩张_{name}",
                   table_tash=TASH_SKILL_TAGS,
                   table_name_for_config2id="SkillTagsConfig")

    # ===== Helper =====
    def make_modify_tag(tag_id, value_param, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["MODIFY_TAG"],
                   "Params": [P(108, PT_ATTR), P(7, PT_COMMON_PARAM),
                              P(tag_id), value_param, P(1)]}
        b.add_node("TSET_MODIFY_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["MODIFY_TAG"])
        return eid

    def make_get_tag(tag_id, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_TAG"],
                   "Params": [P(108, PT_ATTR), P(7, PT_COMMON_PARAM),
                              P(tag_id), P(1), P(0)]}
        b.add_node("TSET_GET_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_TAG"])
        return eid

    def make_modify_entity_tag(tag_id, value_param, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["MODIFY_TAG"],
                   "Params": [P(1, PT_COMMON_PARAM), P(41, PT_COMMON_PARAM),
                              P(tag_id), value_param, P(1)]}
        b.add_node("TSET_MODIFY_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["MODIFY_TAG"])
        return eid

    def make_get_entity_tag(tag_id, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_TAG"],
                   "Params": [P(1, PT_COMMON_PARAM), P(41, PT_COMMON_PARAM),
                              P(tag_id), P(1), P(0)]}
        b.add_node("TSET_GET_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_TAG"])
        return eid

    def make_add_entity_tag(tag_id, delta_param, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["ADD_TAG"],
                   "Params": [P(1, PT_COMMON_PARAM), P(41, PT_COMMON_PARAM),
                              P(tag_id), delta_param, P(1)]}
        b.add_node("TSET_ADD_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["ADD_TAG"])
        return eid

    def make_get_attr(attr_id, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_ATTR"],
                   "Params": [P(75, PT_ATTR), P(attr_id)]}
        b.add_node("TSET_GET_ENTITY_ATTR_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_ATTR"])
        return eid

    def make_get_self_attr(attr_id, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_ATTR"],
                   "Params": [P(1, PT_COMMON_PARAM), P(attr_id)]}
        b.add_node("TSET_GET_ENTITY_ATTR_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_ATTR"])
        return eid

    def make_modify_entity_attr(attr_id, value_param, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["MODIFY_ATTR"],
                   "Params": [P(1, PT_COMMON_PARAM), P(attr_id), value_param]}
        b.add_node("TSET_MODIFY_ENTITY_ATTR_VALUE", eid, payload,
                   desc=desc, effect_type=ET["MODIFY_ATTR"])
        return eid

    def make_change_entity_position(x_param, y_param, z_param=None, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["CHANGE_POS"],
                   "Params": [P(1, PT_COMMON_PARAM), x_param, y_param,
                              P(2), z_param or P(0)]}
        b.add_node("TSET_CHANGE_ENTITY_POSITION", eid, payload,
                   desc=desc, effect_type=ET["CHANGE_POS"])
        return eid

    def make_math_cos(angle_param, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["MATH_COS"],
                   "Params": [angle_param]}
        b.add_node("TSET_MATH_COS", eid, payload,
                   desc=desc, effect_type=ET["MATH_COS"])
        return eid

    def make_math_sin(angle_param, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["MATH_SIN"],
                   "Params": [angle_param]}
        b.add_node("TSET_MATH_SIN", eid, payload,
                   desc=desc, effect_type=ET["MATH_SIN"])
        return eid

    def make_calc(params, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["CALC"], "Params": params}
        b.add_node("TSET_NUM_CALCULATE", eid, payload,
                   desc=desc, effect_type=ET["CALC"])
        return eid

    def make_order(child_ids, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["ORDER"],
                   "Params": [P(c) for c in child_ids]}
        b.add_node("TSET_ORDER_EXECUTE", eid, payload,
                   desc=desc, effect_type=ET["ORDER"])
        return eid

    def make_repeat_each_frame(child_id, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["REPEAT"],
                   "Params": [P(1), P(-1), P(0), P(child_id),
                              P(0), P(0), P(0), P(0), P(0), P(1)]}
        b.add_node("TSET_REPEAT_EXECUTE", eid, payload,
                   desc=desc, effect_type=ET["REPEAT"])
        return eid

    def make_angle_dist_x(cx, cy, ang, dist, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["ANGLE_DIST_X"],
                   "Params": [cx, cy, ang, dist, P(0)]}
        b.add_node("TSET_GET_POS_X_BY_ANGLE_DISTANCE", eid, payload,
                   desc=desc, effect_type=ET["ANGLE_DIST_X"])
        return eid

    def make_angle_dist_y(cx, cy, ang, dist, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["ANGLE_DIST_Y"],
                   "Params": [cx, cy, ang, dist, P(0)]}
        b.add_node("TSET_GET_POS_Y_BY_ANGLE_DISTANCE", eid, payload,
                   desc=desc, effect_type=ET["ANGLE_DIST_Y"])
        return eid

    def make_value_compare(left_param, op, right_param, desc=""):
        cid = b.alloc_cid()
        payload = {"ID": cid, "SkillConditionType": CT["VALUE_COMPARE"],
                   "Params": [left_param, P(op), right_param]}
        b.add_node("TSCT_VALUE_COMPARE", cid, payload,
                   desc=desc, condition_type=CT["VALUE_COMPARE"],
                   table_tash=TASH_SKILL_CONDITION,
                   table_name_for_config2id="SkillConditionConfig")
        return cid

    def make_condition_execute(cond_id, then_eid, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["CONDITION_EXECUTE"],
                   "Params": [P(cond_id), P(then_eid), P(0)]}
        b.add_node("TSET_CONDITION_EXECUTE", eid, payload,
                   desc=desc, effect_type=ET["CONDITION_EXECUTE"])
        return eid

    def make_destroy_entity(desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["DESTROY_ENTITY"],
                   "Params": [P(75, PT_ATTR), P(1), P(0)]}
        b.add_node("TSET_DESTROY_ENTITY", eid, payload,
                   desc=desc, effect_type=ET["DESTROY_ENTITY"])
        return eid

    # ===== 主流程 =====
    init_i = make_modify_tag(TAG_IDS["i"], P(0), desc="初始化 i=0")
    init_order = make_order([init_i], desc="预初始化 (i=0)")

    get_i_for_inc = make_get_tag(TAG_IDS["i"], desc="读 i (准备 i++)")
    calc_inc_i = make_calc(
        [P(get_i_for_inc, PT_FUNC_RET), P(OP_ADD), P(1)],
        desc="i + 1")
    inc_i = make_modify_tag(TAG_IDS["i"], P(calc_inc_i, PT_FUNC_RET), desc="i = i + 1")

    get_i_for_theta = make_get_tag(TAG_IDS["i"], desc="读 i (算 θ)")
    calc_theta = make_calc(
        [P(get_i_for_theta, PT_FUNC_RET), P(OP_MINUS), P(1),
         P(OP_MULTI), P(360),
         P(OP_DIV), P(EXT_N, PT_EXTRA_PARAM)],
        desc="θ_i = (i-1) * 360 / N")
    set_theta = make_modify_tag(TAG_IDS["curTheta"], P(calc_theta, PT_FUNC_RET),
                                  desc="curTheta = (i-1)·360/N")

    facing_eid = make_get_attr(91, desc="caster.facing")
    get_theta_for_abs = make_get_tag(TAG_IDS["curTheta"], desc="读 curTheta")
    calc_abs_angle = make_calc(
        [P(facing_eid, PT_FUNC_RET), P(OP_ADD), P(get_theta_for_abs, PT_FUNC_RET)],
        desc="abs_angle = facing + θ_i")
    set_abs_angle = make_modify_tag(TAG_IDS["curAbsAngle"], P(calc_abs_angle, PT_FUNC_RET),
                                      desc="curAbsAngle")

    get_abs_for_heading = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle (heading)")
    calc_heading = make_calc(
        [P(get_abs_for_heading, PT_FUNC_RET), P(OP_ADD), P(90),
         P(OP_ADD), P(EXT_PHI, PT_EXTRA_PARAM)],
        desc="heading = abs_angle + 90 + φ")
    set_heading = make_modify_tag(TAG_IDS["curHeading"], P(calc_heading, PT_FUNC_RET),
                                    desc="curHeading")

    caster_x = make_get_attr(59, desc="caster.X")
    caster_y_for_x = make_get_attr(60, desc="caster.Y (备用-X)")
    get_abs_for_x = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle (spawn_X)")
    spawn_x_eid = make_angle_dist_x(
        P(caster_x, PT_FUNC_RET), P(caster_y_for_x, PT_FUNC_RET),
        P(get_abs_for_x, PT_FUNC_RET), P(EXT_R0, PT_EXTRA_PARAM),
        desc="spawn_X = caster.X + R0·cos(abs_angle)")

    caster_x_for_y = make_get_attr(59, desc="caster.X (备用-Y)")
    caster_y = make_get_attr(60, desc="caster.Y")
    get_abs_for_y = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle (spawn_Y)")
    spawn_y_eid = make_angle_dist_y(
        P(caster_x_for_y, PT_FUNC_RET), P(caster_y, PT_FUNC_RET),
        P(get_abs_for_y, PT_FUNC_RET), P(EXT_R0, PT_EXTRA_PARAM),
        desc="spawn_Y = caster.Y + R0·sin(abs_angle)")

    bullet_height_eid = b.alloc_eid()
    bullet_height_payload = {
        "ID": bullet_height_eid, "SkillEffectType": ET["GET_FIXTURE_CENTER_Z"],
        "Params": [P(75, PT_ATTR), P(1)]}
    b.add_node("TSET_GET_FIXTURE_CENTER_Z", bullet_height_eid, bullet_height_payload,
               desc="出手点假高度 Z (caster 胶囊中点)",
               effect_type=ET["GET_FIXTURE_CENTER_Z"])

    get_heading_for_bullet = make_get_tag(TAG_IDS["curHeading"], desc="读 curHeading (子弹朝向)")

    # CREATE_BULLET.Params[0] 读 EXT_PARAM[10]，由调用方传真实 BulletConfig.ID。
    bullet_eid = b.alloc_eid()
    bullet_payload = {
        "ID": bullet_eid, "SkillEffectType": ET["BULLET"],
        "Params": [
            P(EXT_BULLET_CFG, PT_EXTRA_PARAM),      # 0  bulletConfig
            P(get_heading_for_bullet, PT_FUNC_RET), # 1  朝向
            P(spawn_x_eid, PT_FUNC_RET),            # 2  spawn_X
            P(spawn_y_eid, PT_FUNC_RET),            # 3  spawn_Y
            P(1, PT_COMMON_PARAM),                  # 4  位置类型
            P(0), P(0),                             # 5,6
            P(0), P(0), P(0),                       # 7,8,9
            P(41, PT_COMMON_PARAM),                 # 10 角度类型
            P(0),                                   # 11
            P(bullet_height_eid, PT_FUNC_RET),      # 12 Z
            P(0), P(1),                             # 13,14
        ],
    }
    b.add_node("TSET_CREATE_BULLET", bullet_eid, bullet_payload,
               desc="创建第 i 颗子弹（BulletConfig 由 EXT_PARAM[10] 决定）",
               effect_type=ET["BULLET"])

    single_order = make_order(
        [inc_i, set_theta, set_abs_angle, set_heading, bullet_eid],
        desc="单发流程: i++ → θ → abs_angle → heading → spawn")

    repeat_eid = b.alloc_eid()
    repeat_payload = {
        "ID": repeat_eid, "SkillEffectType": ET["REPEAT"],
        "Params": [P(0), P(EXT_N, PT_EXTRA_PARAM), P(1), P(single_order),
                   P(0), P(0), P(0), P(0), P(0), P(1)]}
    b.add_node("TSET_REPEAT_EXECUTE", repeat_eid, repeat_payload,
               desc="重复 N 次（每次发一颗）", effect_type=ET["REPEAT"])

    # ===== OnTick 工具子图：作为 32300101 effect 暴露给外部 BulletConfig.AfterBorn =====
    init_R = make_modify_entity_tag(
        TAG_IDS["trajR"], P(EXT_R0, PT_EXTRA_PARAM),
        desc="init: trajR = R0（实体级，挂子弹）")
    self_facing_for_init = make_get_self_attr(91, desc="读子弹自身 facing (init)")
    calc_init_theta = make_calc(
        [P(self_facing_for_init, PT_FUNC_RET), P(OP_MINUS), P(90),
         P(OP_MINUS), P(EXT_PHI, PT_EXTRA_PARAM)],
        desc="init: θ_0 = facing - 90 - φ")
    init_theta = make_modify_entity_tag(
        TAG_IDS["trajTheta"], P(calc_init_theta, PT_FUNC_RET),
        desc="init: trajTheta = θ_0")
    caster_x_init = make_get_attr(59, desc="读 caster.X (init center)")
    caster_y_init = make_get_attr(60, desc="读 caster.Y (init center)")
    init_X0 = make_modify_entity_tag(
        TAG_IDS["casterX"], P(caster_x_init, PT_FUNC_RET),
        desc="init: X0 = caster.X")
    init_Y0 = make_modify_entity_tag(
        TAG_IDS["casterY"], P(caster_y_init, PT_FUNC_RET),
        desc="init: Y0 = caster.Y")
    init_curRadSpd = make_modify_entity_tag(
        TAG_IDS["currentRadialSpeed"], P(EXT_VR, PT_EXTRA_PARAM),
        desc="init: currentRadialSpeed = vR")

    add_theta = make_add_entity_tag(
        TAG_IDS["trajTheta"], P(EXT_OMEGA, PT_EXTRA_PARAM),
        desc="frame: θ += ω/帧")
    calc_aR_per_frame = make_calc(
        [P(EXT_AR, PT_EXTRA_PARAM), P(OP_DIV), P(30)],
        desc="frame: aR/30 (每帧增量)")
    add_curRadSpd = make_add_entity_tag(
        TAG_IDS["currentRadialSpeed"], P(calc_aR_per_frame, PT_FUNC_RET),
        desc="frame: currentRadialSpeed += aR/30")
    get_curRadSpd_for_R = make_get_entity_tag(
        TAG_IDS["currentRadialSpeed"], desc="frame: 读 currentRadialSpeed")
    add_R = make_add_entity_tag(
        TAG_IDS["trajR"], P(get_curRadSpd_for_R, PT_FUNC_RET),
        desc="frame: R += currentRadialSpeed")

    follow_get_caster_x = make_get_attr(59, desc="frame: caster.X (followPlayer)")
    follow_get_caster_y = make_get_attr(60, desc="frame: caster.Y (followPlayer)")
    follow_write_X0 = make_modify_entity_tag(
        TAG_IDS["casterX"], P(follow_get_caster_x, PT_FUNC_RET),
        desc="frame: X0 = caster.X")
    follow_write_Y0 = make_modify_entity_tag(
        TAG_IDS["casterY"], P(follow_get_caster_y, PT_FUNC_RET),
        desc="frame: Y0 = caster.Y")
    follow_then_order = make_order(
        [follow_write_X0, follow_write_Y0],
        desc="frame: followPlayer=1 时刷新 X0/Y0")
    follow_cond = make_value_compare(
        P(EXT_FOLLOW, PT_EXTRA_PARAM), CMP_NEQ, P(0),
        desc="frame: followPlayer != 0 ?")
    follow_branch = make_condition_execute(
        follow_cond, follow_then_order,
        desc="frame: if followPlayer != 0 then refresh X0/Y0")

    get_theta_tick = make_get_entity_tag(TAG_IDS["trajTheta"], desc="frame: 读 trajTheta")
    get_R_tick = make_get_entity_tag(TAG_IDS["trajR"], desc="frame: 读 trajR")
    cos_theta = make_math_cos(P(get_theta_tick, PT_FUNC_RET), desc="frame: cos(θ)*10000")
    sin_theta = make_math_sin(P(get_theta_tick, PT_FUNC_RET), desc="frame: sin(θ)*10000")

    get_X0 = make_get_entity_tag(TAG_IDS["casterX"], desc="frame: 读 X0")
    get_Y0 = make_get_entity_tag(TAG_IDS["casterY"], desc="frame: 读 Y0")
    calc_new_X = make_calc(
        [P(get_X0, PT_FUNC_RET), P(OP_ADD), P(get_R_tick, PT_FUNC_RET),
         P(OP_MULTI), P(cos_theta, PT_FUNC_RET), P(OP_DIV), P(10000)],
        desc="frame: newX = X0 + R·cos(θ)/10000")
    calc_new_Y = make_calc(
        [P(get_Y0, PT_FUNC_RET), P(OP_ADD), P(get_R_tick, PT_FUNC_RET),
         P(OP_MULTI), P(sin_theta, PT_FUNC_RET), P(OP_DIV), P(10000)],
        desc="frame: newY = Y0 + R·sin(θ)/10000")
    write_X = make_modify_entity_attr(59, P(calc_new_X, PT_FUNC_RET), desc="frame: 子弹.X = newX")
    write_Y = make_modify_entity_attr(60, P(calc_new_Y, PT_FUNC_RET), desc="frame: 子弹.Y = newY")
    change_pos = make_change_entity_position(
        P(calc_new_X, PT_FUNC_RET), P(calc_new_Y, PT_FUNC_RET),
        desc="frame: 应用位置")

    destroy_eff = make_destroy_entity(desc="frame: 销毁子弹自身")
    get_R_for_max = make_get_entity_tag(
        TAG_IDS["trajR"], desc="frame: 读 trajR (maxR 检查)")
    cond_max = make_value_compare(
        P(get_R_for_max, PT_FUNC_RET), CMP_GT,
        P(EXT_MAX_R, PT_EXTRA_PARAM),
        desc="frame: R > maxRadius ?")
    branch_max = make_condition_execute(
        cond_max, destroy_eff,
        desc="frame: if R>maxR then DESTROY")
    get_R_for_min = make_get_entity_tag(
        TAG_IDS["trajR"], desc="frame: 读 trajR (minR 检查)")
    cond_min = make_value_compare(
        P(get_R_for_min, PT_FUNC_RET), CMP_LT,
        P(EXT_MIN_R, PT_EXTRA_PARAM),
        desc="frame: R < minRadius ?")
    branch_min = make_condition_execute(
        cond_min, destroy_eff,
        desc="frame: if R<minR then DESTROY")

    ontick_frame = make_order(
        [add_theta, add_curRadSpd, add_R, follow_branch,
         write_X, write_Y, change_pos,
         branch_max, branch_min],
        desc="OnTick 单帧：θ+=ω → curRadSpd+=aR/30 → R+=curRadSpd → "
             "followPlayer 分支 → 改 X/Y → 应用位置 → maxR/minR 双条件检查")

    ontick_repeat = make_repeat_each_frame(ontick_frame, desc="OnTick REPEAT (每帧)")

    # OnTick init 根：外部 BulletConfig.AfterBornSkillEffectExecuteInfo.SkillEffectConfigID 应指向 32300101。
    ontick_init_payload = {
        "ID": ONTICK_INIT_EID, "SkillEffectType": ET["ORDER"],
        "Params": [P(init_R), P(init_theta), P(init_X0), P(init_Y0),
                   P(init_curRadSpd), P(ontick_repeat)]}
    b.add_node(
        "TSET_ORDER_EXECUTE", ONTICK_INIT_EID, ontick_init_payload,
        desc="OnTick init: 初始化 R0/θ_0/X0/Y0/curRadSpd + 启动每帧 REPEAT\n"
             "外部 BulletConfig.AfterBorn 应指向本节点 ID=32300101",
        effect_type=ET["ORDER"])

    # ===== 模板根 ORDER (IsTemplate=true) =====
    root_eid = ROOT_TEMPLATE_EID
    root_payload = {
        "ID": root_eid, "SkillEffectType": ET["ORDER"],
        "Params": [P(init_order), P(repeat_eid)]}
    b.add_node(
        "TSET_ORDER_EXECUTE", root_eid, root_payload,
        is_template=True, template_params=TPARAMS,
        desc="旋转扩张子弹圈模板根 v1.0（9 项运动/边界参数 + [10] bulletConfig）",
        effect_type=ET["ORDER"])

    # v1.0 不内置 BulletConfigNode：
    # - 子弹寿命、伤害、穿透和命中链归调用方 BulletConfig 管。
    # - 调用方传入的 BulletConfig 必须把 AfterBorn 指向 ONTICK_INIT_EID。

    return b


def make_sticky_notes() -> list:
    """v1.0 sticky note — 几何运动模板 + BulletConfig contract"""
    overview = (
        "[作用]\n"
        "通用 N 颗独立子弹绕主角旋转扩张模板。模板只负责几何运动；子弹寿命、伤害、穿透和命中链路由 BulletConfig 负责。\n\n"
        "[使用前必读]\n"
        "本模板要求调用方满足以下 contract：\n"
        "  传入的 BulletConfig 必须事先在表里配:\n"
        "    AfterBornSkillEffectExecuteInfo.SkillEffectConfigID = 32300101\n"
        "  其中 32300101 = 本模板暴露的 OnTick 入口 effect。\n"
        "首次使用前必做：\n"
        "  1. SkillEditor 打开本模板 → 点「同步数据」让 32300101 进运行时 SkillEffectConfig 表\n"
        "  2. 配（或修改已有）一个 BulletConfig，把它的 AfterBorn 字段指向 32300101\n"
        "  3. 重启 Unity Editor 让运行时表重新加载\n\n"
        "[流程]\n"
        "1. 调用方拖入模板，EXT_PARAM[10] 传一个 contract-compliant BulletConfig.ID\n"
        "2. 模板 spawn 阶段：N 颗子弹同帧创建，phase_i = 2π·i/N 角度均匀分布\n"
        "3. 子弹生成后子弹的 BulletConfig.AfterBorn (=32300101) 自动触发 OnTick 链\n"
        "4. OnTick 每帧：θ_i += ω, R += vR + aR/30, 重算每颗位置\n"
        "5. 子弹长边沿切线（φ=0）或偏移 φ 角朝向\n"
        "6. R > maxR / R < minR → 销毁该颗子弹\n\n"
        "[特殊条件]\n"
        "- followPlayer=0 → 圆心固定在释放瞬间位置（默认）；=1 → 每帧跟随主角\n"
        "- aR<0 配合 vR>0 → 先扩后缩玩法\n"
        "- φ=90° → 子弹长边指向圆心外（'刺向外'）\n"
        "- 单位约定：1 米 = 100 单位，1 秒 = 30 帧\n"
        "  R0/maxR/minR 单位「项目坐标系单位」\n"
        "  vR 单位「单位/帧」（正=外飞，负=内收）\n"
        "  ω 单位「度/帧」（正=逆时针，负=顺时针）\n"
        "  aR 单位「单位/秒²」（每帧加 aR/30）\n\n"
        "[参数] 10 项 EXT_PARAM（全部真消费）\n"
        "[阵型] bulletCount 子弹数N                  默认 8（≤50 安全，>100 触发引擎保护）\n"
        "[阵型] initialRadius 初始半径R0             默认 200 单位 (≈2 米)\n"
        "[阵型] tangentOffsetAngle 切线偏移角φ       默认 0 度\n"
        "[运动] radialVelocity 径向速度vR            默认 10 单位/帧\n"
        "[运动] radialAcceleration 径向加速度aR      默认 0 单位/秒²\n"
        "[运动] angularVelocity 整团角速度ω          默认 3 度/帧\n"
        "[终止] maxRadius 最大半径                   默认 1500 单位\n"
        "[终止] minRadius 最小半径                   默认 0 单位\n"
        "[运动] followPlayer 是否跟随主角            默认 0\n"
        "[子弹] bulletConfig 子弹ID(BulletConfig)    必填，需满足 AfterBorn=32300101\n\n"
        "[联动]\n"
        "- 调用方必须先配好 contract-compliant BulletConfig（一次性工作，可复用到多个技能）\n"
        "- 调用方使用 TSET_RUN_SKILL_EFFECT_TEMPLATE (SET=118) 引用本模板根 32300001\n"
        "- 调用方在自己的 SkillConfig.SkillDamageTagsList 加伤害 tag 给子弹挂伤害\n"
        "- lifetime / damagePerHit / pierceCount 不在模板里暴露，统一由 BulletConfig 或命中链配置\n\n"
        "[v1.0 设计]\n"
        "删除旧模板的内置 BulletConfig / ModelConfig 方案，只保留运动学模板 + 外部 bulletConfig contract。\n"
        "followPlayer 默认 0，符合需求文档中“脱手即与主角解耦”的默认语义。\n\n"
        "[参考真实样本]\n"
        "108_0001 环形扩散子弹：本模板的设计参考（双根 + 用户传 BulletConfig + AfterBorn 接 OnTick 入口）\n"
        "30212010 叶散风行：OnTick 链原型，BulletConfig 320112 AfterBorn=32003149 模式\n"
        "扇形分层弹幕模板：BulletConfig EXT_PARAM 声明格式参考"
    )
    return [{
        "GUID": str(uuid.uuid4()),
        "position": {
            "serializedVersion": "2",
            "x": -180.0, "y": 60.0,
            "width": 800.0, "height": 2400.0,
        },
        "title": "[概览] 旋转扩张子弹圈 v1.0 — 运动模板 + BulletConfig contract",
        "content": overview,
    }]


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    b = build()
    notes = make_sticky_notes()
    b.emit(OUTPUT, sticky_notes=notes)
    print(f"v1.0 模板生成成功 -> {OUTPUT}")
    print(f"  节点数: {len(b.refs)}")
    print(f"  自动派生 PackedParamsOutput 边数: {len(b.edges)}")
    print(f"  字段端口边数: {len(b.field_port_edges)}")
    print(f"  总边数: {len(b.edges) + len(b.field_port_edges)}")
    ids = [r["data"]["ID"] for r in b.refs]
    print(f"  ID 范围: {min(ids)} ~ {max(ids)}")
    print(f"  模板根 ID: {ROOT_TEMPLATE_EID}")
    print(f"  OnTick init effect ID: {ONTICK_INIT_EID}")
    print(f"  TemplateParams 数量: {len(TPARAMS)} (9 个运动/边界参数 + bulletConfig)")


if __name__ == "__main__":
    main()
