#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扇形分层弹幕模板生成器 (阶段 2.2a: K=1~3 完整版)

需求来源：F:/AI/草稿/扇形分层弹幕算法.md

阶段进度：
- ✅ 阶段 1：纯节点 + REPEAT + cos/sin 位置 + CREATE_BULLET 全链路（48 节点）
- ✅ 阶段 2.1+2.3：K=2 真分支 + 偶数层错位（64 节点）
- ✅ 阶段 2.2a：K=1~3 完整版（185 节点，覆盖 N=1~21）
- ✅ 阶段 2.2b：扩到 K=4~5（本版本，~290 节点，覆盖 N=22+）

阶段 2.2a 实现的算法步骤（按用户算法 §3）：
- Step 1：算 K（阈值表 [3, 9] 三档）
- Step 2：算 distances[1..3]
- Step 3：算 totalDist（按 K 分支）
- Step 4：算 fanAngles[1..3]（按 K 分支，K=1 时 fan_1=fanMax；K=2 时 [fanMin, fanMax]；K=3 时 [fanMin, mid, fanMax]）
- Step 5：算 counts[1..3]（按 K 分支 + floor(N*dist/total) + 最后一层 = N - sum）
- Step 6：算 cumulative[1..3]
- Step 7-9：单发循环 i++ → 反查 r → 算 angle → 创建子弹

模板参数 6 个：
  [0] BulletID (BulletConfig)
  [1] N (整数)
  [2] fanMin (默认 30)
  [3] fanMax (默认 90)
  [4] baseDist (默认 100)
  [5] layerStep (默认 100)

关键经验（已沉淀在 memory/feedback_skill_compiler_pitfalls.md 第 10 条）：
- TSCT_VALUE_COMPARE 必须用 SkillCondition 表的 TableTash (ED89...)
- 顶层 SkillConditionType 字段必须有
- Config2ID 前缀必须是 SkillConditionConfig_<id>
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJ = Path(r"<<PROJECT_ROOT_WIN>>")
OUTPUT = PROJ / "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】扇形分层弹幕.json"

# ===== ID 段位 =====
ROOT_TEMPLATE_EID = 32100001 # 模板根节点固定 ID（**不能改**，否则编辑器 template2Nodes 缓存会积累旧 ID）
EFFECT_BASE = 32100002       # SkillEffectConfig 起始（让出 32100001 给 ROOT_TEMPLATE_EID）
COND_BASE   = 32100500       # SkillConditionConfig 起始（避开 effect 段位）

TAG_IDS = {
    # 工作变量（每发循环用）
    "i":             320900,
    "curJ":          320901,
    "curFan":        320902,
    "curDist":       320903,
    "curCnt":        320904,
    "curStagger":    320905,
    "curAbsAngle":   320906,
    # 预计算结果（init 算一次后整轮 REPEAT 共享）
    "K":             320908,
    "dist_1":        320909,
    "dist_2":        320910,
    "dist_3":        320911,
    "dist_4":        320922,  # 阶段 2.2b 新增
    "dist_5":        320923,
    "fan_1":         320912,
    "fan_2":         320913,
    "fan_3":         320914,
    "fan_4":         320924,
    "fan_5":         320925,
    "total":         320915,
    "count_1":       320916,
    "count_2":       320917,
    "count_3":       320918,
    "count_4":       320926,
    "count_5":       320927,
    "cum_1":         320919,
    "cum_2":         320920,
    "cum_3":         320921,
    "cum_4":         320928,
    "cum_5":         320929,
    # 临时存储 (fanMax - fanMin) 以避免重复计算
    "_fan_diff":     320930,
}

# ===== TableTash =====
TASH_SKILL_EFFECT    = "0CFA05568A66FEA1DF3BA6FE40DB7080"
TASH_SKILL_TAGS      = "6A8A6883BDFDA1411BB2461E65CB2D9B"
TASH_SKILL_CONDITION = "ED89F46EAB95F7ACF5C1911A5A375278"  # 关键：与 SkillEffect 不同！

# ===== TSkillEffectType =====
ET = {
    "ORDER":      1, "DELAY": 2, "REPEAT": 3, "BULLET": 8,
    "CALC":       31, "GET_ATTR": 32,
    "MODIFY_TAG": 46, "GET_TAG": 48,
    "SIN":        50, "COS": 51,
    "COND_EXEC":  47,
    "GET_FIXTURE_CENTER_Z": 367,    # 获取单位胶囊碰撞器中点的假高度 Z
}

# TSkillConditionType
CT_VALUE_COMPARE = 7

# 数值运算符 TNumOperators
OP_CEIL, OP_FLOOR, OP_ADD, OP_MINUS, OP_MULTI, OP_DIV, OP_MOD, OP_ABS = 1, 2, 3, 4, 5, 6, 7, 8

# 比较运算符 TCompareType（从 30222005 真实样本观察 + 推测）
CMP_EQ = 1   # 等于
CMP_GE = 4   # 大于等于（用 P0=A, P1=4, P2=B 表示 A ≥ B）

# ParamType
PT_NULL, PT_ATTR, PT_FUNC_RET, PT_SKILL_PARAM, PT_EXTRA_PARAM, PT_COMMON_PARAM, PT_EVENT_PARAM = 0,1,2,3,4,5,6


# ===== Builder =====
class TplBuilder:
    def __init__(self):
        self.refs = []
        self.edges = []
        self.next_rid = 1000
        self.next_eid = EFFECT_BASE
        self.next_cid = COND_BASE
        self.guid_of_id: dict[int, str] = {}
        self._auto_y = 0  # 简单的 y 自增用于排版

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
                 table_name_for_config2id: str = "SkillEffectConfig") -> str:
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
        self.refs.append({
            "rid": rid,
            "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
            "data": data,
        })
        self.guid_of_id[config_id] = guid
        return guid

    def emit(self, output_path: Path):
        # 自动建边
        DYN_PORT = {"TSET_ORDER_EXECUTE", "TSET_NUM_MAX", "TSET_NUM_MIN"}
        for ref in self.refs:
            cls = ref["type"]["class"]
            if cls in {"SkillTagsConfigNode"}:
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

        graph = {
            "serializationData": {
                "SerializedFormat": 0, "SerializedBytes": [],
                "ReferencedUnityObjects": [], "SerializedBytesString": "",
                "Prefab": {"instanceID": 0},
                "PrefabModificationsReferencedUnityObjects": [],
                "PrefabModifications": [], "SerializationNodes": [],
            },
            "nodes": [{"rid": r["rid"]} for r in self.refs],
            "edges": self.edges,
            "groups": [], "stackNodes": [],
            "pinnedElements": [{
                "position": {"serializedVersion": "2", "x": 0.0, "y": 0.0, "width": 511.0, "height": 629.0},
                "opened": True,
                "editorType": {
                    "serializedType": "NodeEditor.ConfigPinnedView, NodeEditor, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null"
                }
            }],
            "exposedParameters": [], "serializedParameterList": [], "stickyNotes": [],
            "curTab": 0,
            "path": str(output_path).replace("\\", "/").replace(str(PROJ).replace("\\", "/") + "/", ""),
            "references": {"version": 2, "RefIds": self.refs},
        }
        output_path.write_text(
            json.dumps(graph, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )


def P(value, pt=PT_NULL, factor=0):
    """构造 Param dict（防 Python bool 透出）"""
    return {
        "Value": int(value) if isinstance(value, bool) else value,
        "ParamType": pt,
        "Factor": factor,
    }


# 模板参数索引 (1-based, PT=4)
EXT_BULLET_ID  = 1
EXT_N          = 2
EXT_FAN_MIN    = 3
EXT_FAN_MAX    = 4
EXT_BASE_DIST  = 5
EXT_LAYER_STEP = 6

TPARAMS = [
    {"DefaultValueDesc": "", "Name": "子弹ID", "RefTypeName": "BulletConfig",
     "RefPortTypeNames": "", "DefalutParam": {}, "DefalutParamJson": "",
     "isConfigId": True, "isEnum": False,
     "RefTableFullName": "TableDR.BulletConfig",
     "RefTableManagerName": "TableDR.BulletConfigManager",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    {"DefaultValueDesc": "", "Name": "总子弹数N", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":10,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    {"DefaultValueDesc": "", "Name": "内层扇角fanMin", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":30,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    {"DefaultValueDesc": "", "Name": "外层扇角fanMax", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":90,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    {"DefaultValueDesc": "", "Name": "基础距离baseDist", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":100,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    {"DefaultValueDesc": "", "Name": "层距步进layerStep", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":100,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
]


def build():
    b = TplBuilder()

    # ----- SkillTagsConfigNode 集合 -----
    for name, tid in TAG_IDS.items():
        payload = {"ID": tid, "TagType": 0, "Desc": f"_扇形分层_{name}",
                   "NameKey": 0, "DefaultValue": 0, "FinalValueEffectID": 0,
                   "RetainWhenDie": False}
        b.add_node("SkillTagsConfigNode", tid, payload,
                   desc=f"_扇形分层_{name}",
                   table_tash=TASH_SKILL_TAGS,
                   table_name_for_config2id="SkillTagsConfig")

    # ===== 通用 helper =====
    def make_modify_tag(tag_id: int, value_param: dict, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["MODIFY_TAG"],
                   "Params": [
                       P(108, PT_ATTR), P(7, PT_COMMON_PARAM),
                       P(tag_id), value_param, P(1),
                   ]}
        b.add_node("TSET_MODIFY_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["MODIFY_TAG"])
        return eid

    def make_get_tag(tag_id: int, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_TAG"],
                   "Params": [
                       P(108, PT_ATTR), P(7, PT_COMMON_PARAM),
                       P(tag_id), P(1), P(0),
                   ]}
        b.add_node("TSET_GET_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_TAG"])
        return eid

    def make_get_attr(attr_id: int, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_ATTR"],
                   "Params": [P(75, PT_ATTR), P(attr_id)]}
        b.add_node("TSET_GET_ENTITY_ATTR_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_ATTR"])
        return eid

    def make_calc(params: list, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["CALC"], "Params": params}
        b.add_node("TSET_NUM_CALCULATE", eid, payload,
                   desc=desc, effect_type=ET["CALC"])
        return eid

    def make_order(child_ids: list[int], desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["ORDER"],
                   "Params": [P(c) for c in child_ids]}
        b.add_node("TSET_ORDER_EXECUTE", eid, payload,
                   desc=desc, effect_type=ET["ORDER"])
        return eid

    def make_value_compare(p0_param, op: int, p2_param, desc=""):
        """生成 SkillConditionConfig 节点 — 用 SkillCondition 段位 + TableTash"""
        cid = b.alloc_cid()
        payload = {"ID": cid, "SkillConditionType": CT_VALUE_COMPARE,
                   "Params": [p0_param, P(op), p2_param]}
        b.add_node("TSCT_VALUE_COMPARE", cid, payload,
                   desc=desc,
                   table_tash=TASH_SKILL_CONDITION,
                   condition_type=CT_VALUE_COMPARE,
                   table_name_for_config2id="SkillConditionConfig")
        return cid

    def make_cond_exec(cond_id: int, then_eid: int, else_eid: int, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["COND_EXEC"],
                   "Params": [P(cond_id), P(then_eid), P(else_eid)]}
        b.add_node("TSET_CONDITION_EXECUTE", eid, payload,
                   desc=desc, effect_type=ET["COND_EXEC"])
        return eid

    # ===== Step 1：算 K（按阈值表 [3, 9, 21, 40]，五档）=====
    # if N≤3→K=1; elif N≤9→K=2; elif N≤21→K=3; elif N≤40→K=4; else K=5
    set_K1 = make_modify_tag(TAG_IDS["K"], P(1), desc="K=1")
    set_K2 = make_modify_tag(TAG_IDS["K"], P(2), desc="K=2")
    set_K3 = make_modify_tag(TAG_IDS["K"], P(3), desc="K=3")
    set_K4 = make_modify_tag(TAG_IDS["K"], P(4), desc="K=4")
    set_K5 = make_modify_tag(TAG_IDS["K"], P(5), desc="K=5")

    cmp_N_le_40 = make_value_compare(P(40), CMP_GE, P(EXT_N, PT_EXTRA_PARAM), desc="N ≤ 40 ?")
    cond_K4_or_5 = make_cond_exec(cmp_N_le_40, set_K4, set_K5, desc="if N≤40 then K=4 else K=5")

    cmp_N_le_21 = make_value_compare(P(21), CMP_GE, P(EXT_N, PT_EXTRA_PARAM), desc="N ≤ 21 ?")
    cond_K3_or_higher = make_cond_exec(cmp_N_le_21, set_K3, cond_K4_or_5,
                                         desc="if N≤21 then K=3 else 分支 K=4/5")

    cmp_N_le_9 = make_value_compare(P(9), CMP_GE, P(EXT_N, PT_EXTRA_PARAM), desc="N ≤ 9 ?")
    cond_K2_or_higher = make_cond_exec(cmp_N_le_9, set_K2, cond_K3_or_higher,
                                         desc="if N≤9 then K=2 else 分支 K=3/4/5")

    cmp_N_le_3 = make_value_compare(P(3), CMP_GE, P(EXT_N, PT_EXTRA_PARAM), desc="N ≤ 3 ?")
    cond_K = make_cond_exec(cmp_N_le_3, set_K1, cond_K2_or_higher,
                             desc="if N≤3 then K=1 else 分支 K=2/3/4/5")

    # ===== Step 2：算 distances[1..5] =====
    set_dist_1 = make_modify_tag(TAG_IDS["dist_1"], P(EXT_BASE_DIST, PT_EXTRA_PARAM), desc="dist_1=baseDist")
    calc_dist_2 = make_calc([P(EXT_BASE_DIST, PT_EXTRA_PARAM), P(OP_ADD), P(EXT_LAYER_STEP, PT_EXTRA_PARAM)],
                            desc="baseDist+layerStep")
    set_dist_2 = make_modify_tag(TAG_IDS["dist_2"], P(calc_dist_2, PT_FUNC_RET), desc="dist_2")
    calc_dist_3 = make_calc([P(EXT_LAYER_STEP, PT_EXTRA_PARAM), P(OP_MULTI), P(2),
                             P(OP_ADD), P(EXT_BASE_DIST, PT_EXTRA_PARAM)],
                            desc="baseDist+2*layerStep")
    set_dist_3 = make_modify_tag(TAG_IDS["dist_3"], P(calc_dist_3, PT_FUNC_RET), desc="dist_3")
    calc_dist_4 = make_calc([P(EXT_LAYER_STEP, PT_EXTRA_PARAM), P(OP_MULTI), P(3),
                             P(OP_ADD), P(EXT_BASE_DIST, PT_EXTRA_PARAM)],
                            desc="baseDist+3*layerStep")
    set_dist_4 = make_modify_tag(TAG_IDS["dist_4"], P(calc_dist_4, PT_FUNC_RET), desc="dist_4")
    calc_dist_5 = make_calc([P(EXT_LAYER_STEP, PT_EXTRA_PARAM), P(OP_MULTI), P(4),
                             P(OP_ADD), P(EXT_BASE_DIST, PT_EXTRA_PARAM)],
                            desc="baseDist+4*layerStep")
    set_dist_5 = make_modify_tag(TAG_IDS["dist_5"], P(calc_dist_5, PT_FUNC_RET), desc="dist_5")

    compute_dists = make_order([set_dist_1, set_dist_2, set_dist_3, set_dist_4, set_dist_5],
                                 desc="算 distances")

    # ===== Step 3：算 totalDist（按 K 分支，5 档）=====
    # K=1: total = dist_1
    get_d1_K1 = make_get_tag(TAG_IDS["dist_1"], desc="读 dist_1(K1 total)")
    set_total_K1 = make_modify_tag(TAG_IDS["total"], P(get_d1_K1, PT_FUNC_RET), desc="total=dist_1")

    # K=2: total = dist_1 + dist_2
    get_d1_K2 = make_get_tag(TAG_IDS["dist_1"], desc="读 dist_1(K2 total)")
    get_d2_K2 = make_get_tag(TAG_IDS["dist_2"], desc="读 dist_2(K2 total)")
    calc_total_K2 = make_calc(
        [P(get_d1_K2, PT_FUNC_RET), P(OP_ADD), P(get_d2_K2, PT_FUNC_RET)],
        desc="K2: d1+d2",
    )
    set_total_K2 = make_modify_tag(TAG_IDS["total"], P(calc_total_K2, PT_FUNC_RET), desc="total(K2)")

    # K=3: total = d1+d2+d3
    get_d1_K3 = make_get_tag(TAG_IDS["dist_1"], desc="读 dist_1(K3 total)")
    get_d2_K3 = make_get_tag(TAG_IDS["dist_2"], desc="读 dist_2(K3 total)")
    get_d3_K3 = make_get_tag(TAG_IDS["dist_3"], desc="读 dist_3(K3 total)")
    calc_total_K3 = make_calc(
        [P(get_d1_K3, PT_FUNC_RET),
         P(OP_ADD), P(get_d2_K3, PT_FUNC_RET),
         P(OP_ADD), P(get_d3_K3, PT_FUNC_RET)],
        desc="K3: d1+d2+d3",
    )
    set_total_K3 = make_modify_tag(TAG_IDS["total"], P(calc_total_K3, PT_FUNC_RET), desc="total(K3)")

    # K=4: total = d1+d2+d3+d4
    get_d1_K4 = make_get_tag(TAG_IDS["dist_1"], desc="读 dist_1(K4 total)")
    get_d2_K4 = make_get_tag(TAG_IDS["dist_2"], desc="读 dist_2(K4 total)")
    get_d3_K4 = make_get_tag(TAG_IDS["dist_3"], desc="读 dist_3(K4 total)")
    get_d4_K4 = make_get_tag(TAG_IDS["dist_4"], desc="读 dist_4(K4 total)")
    calc_total_K4 = make_calc(
        [P(get_d1_K4, PT_FUNC_RET),
         P(OP_ADD), P(get_d2_K4, PT_FUNC_RET),
         P(OP_ADD), P(get_d3_K4, PT_FUNC_RET),
         P(OP_ADD), P(get_d4_K4, PT_FUNC_RET)],
        desc="K4: d1+d2+d3+d4",
    )
    set_total_K4 = make_modify_tag(TAG_IDS["total"], P(calc_total_K4, PT_FUNC_RET), desc="total(K4)")

    # K=5: total = d1+d2+d3+d4+d5
    get_d1_K5 = make_get_tag(TAG_IDS["dist_1"], desc="读 dist_1(K5 total)")
    get_d2_K5 = make_get_tag(TAG_IDS["dist_2"], desc="读 dist_2(K5 total)")
    get_d3_K5 = make_get_tag(TAG_IDS["dist_3"], desc="读 dist_3(K5 total)")
    get_d4_K5 = make_get_tag(TAG_IDS["dist_4"], desc="读 dist_4(K5 total)")
    get_d5_K5 = make_get_tag(TAG_IDS["dist_5"], desc="读 dist_5(K5 total)")
    calc_total_K5 = make_calc(
        [P(get_d1_K5, PT_FUNC_RET),
         P(OP_ADD), P(get_d2_K5, PT_FUNC_RET),
         P(OP_ADD), P(get_d3_K5, PT_FUNC_RET),
         P(OP_ADD), P(get_d4_K5, PT_FUNC_RET),
         P(OP_ADD), P(get_d5_K5, PT_FUNC_RET)],
        desc="K5: sum d1..d5",
    )
    set_total_K5 = make_modify_tag(TAG_IDS["total"], P(calc_total_K5, PT_FUNC_RET), desc="total(K5)")

    # 5 档分支: K==1/2/3/4/5
    get_K_a = make_get_tag(TAG_IDS["K"], desc="读 K(total a)")
    cmp_K_eq_1 = make_value_compare(P(get_K_a, PT_FUNC_RET), CMP_EQ, P(1), desc="K==1?")
    get_K_b = make_get_tag(TAG_IDS["K"], desc="读 K(total b)")
    cmp_K_eq_2 = make_value_compare(P(get_K_b, PT_FUNC_RET), CMP_EQ, P(2), desc="K==2?")
    get_K_c = make_get_tag(TAG_IDS["K"], desc="读 K(total c)")
    cmp_K_eq_3 = make_value_compare(P(get_K_c, PT_FUNC_RET), CMP_EQ, P(3), desc="K==3?")
    get_K_d = make_get_tag(TAG_IDS["K"], desc="读 K(total d)")
    cmp_K_eq_4 = make_value_compare(P(get_K_d, PT_FUNC_RET), CMP_EQ, P(4), desc="K==4?")

    cond_total_K4_or_5 = make_cond_exec(cmp_K_eq_4, set_total_K4, set_total_K5, desc="K=4 or K=5 total")
    cond_total_K3_or_higher = make_cond_exec(cmp_K_eq_3, set_total_K3, cond_total_K4_or_5, desc="K=3/4/5 total")
    cond_total_K2_or_higher = make_cond_exec(cmp_K_eq_2, set_total_K2, cond_total_K3_or_higher, desc="K=2/3/4/5")
    cond_total = make_cond_exec(cmp_K_eq_1, set_total_K1, cond_total_K2_or_higher, desc="算 total（5 档分支）")

    # ===== Step 4：算 fanAngles[1..5]（按 K 分支，5 档线性插值）=====
    # 公式：fan_r = fanMin + (fanMax-fanMin) × (r-1) / (K-1)
    # K=1 特例：fan_1 = fanMax
    # K=2: [fanMin, fanMax]
    # K=3: [fanMin, mid, fanMax]
    # K=4: [fanMin, fanMin+diff/3, fanMin+2*diff/3, fanMax]
    # K=5: [fanMin, fanMin+diff/4, fanMin+diff/2, fanMin+3*diff/4, fanMax]

    # K=1
    fans_K1 = make_order([
        make_modify_tag(TAG_IDS["fan_1"], P(EXT_FAN_MAX, PT_EXTRA_PARAM), desc="K1: fan_1=fanMax"),
        make_modify_tag(TAG_IDS["fan_2"], P(0), desc="K1: fan_2=0"),
        make_modify_tag(TAG_IDS["fan_3"], P(0), desc="K1: fan_3=0"),
        make_modify_tag(TAG_IDS["fan_4"], P(0), desc="K1: fan_4=0"),
        make_modify_tag(TAG_IDS["fan_5"], P(0), desc="K1: fan_5=0"),
    ], desc="K=1 fans")

    # K=2
    fans_K2 = make_order([
        make_modify_tag(TAG_IDS["fan_1"], P(EXT_FAN_MIN, PT_EXTRA_PARAM), desc="K2: fan_1=fanMin"),
        make_modify_tag(TAG_IDS["fan_2"], P(EXT_FAN_MAX, PT_EXTRA_PARAM), desc="K2: fan_2=fanMax"),
        make_modify_tag(TAG_IDS["fan_3"], P(0), desc="K2: fan_3=0"),
        make_modify_tag(TAG_IDS["fan_4"], P(0), desc="K2: fan_4=0"),
        make_modify_tag(TAG_IDS["fan_5"], P(0), desc="K2: fan_5=0"),
    ], desc="K=2 fans")

    # K=3：fan_2 = (fanMin + fanMax) / 2
    calc_fan_2_K3 = make_calc(
        [P(EXT_FAN_MIN, PT_EXTRA_PARAM), P(OP_ADD), P(EXT_FAN_MAX, PT_EXTRA_PARAM), P(OP_DIV), P(2)],
        desc="K3: (fanMin+fanMax)/2",
    )
    fans_K3 = make_order([
        make_modify_tag(TAG_IDS["fan_1"], P(EXT_FAN_MIN, PT_EXTRA_PARAM), desc="K3: fan_1=fanMin"),
        make_modify_tag(TAG_IDS["fan_2"], P(calc_fan_2_K3, PT_FUNC_RET), desc="K3: fan_2=mid"),
        make_modify_tag(TAG_IDS["fan_3"], P(EXT_FAN_MAX, PT_EXTRA_PARAM), desc="K3: fan_3=fanMax"),
        make_modify_tag(TAG_IDS["fan_4"], P(0), desc="K3: fan_4=0"),
        make_modify_tag(TAG_IDS["fan_5"], P(0), desc="K3: fan_5=0"),
    ], desc="K=3 fans")

    # K=4：fan_2 = fanMin + (fanMax-fanMin)/3, fan_3 = fanMin + 2*(fanMax-fanMin)/3
    # 公式简化：fan_2 = fanMin + (fanMax - fanMin) / 3 = (2*fanMin + fanMax) / 3
    # fan_3 = (fanMin + 2*fanMax) / 3
    calc_fan_2_K4 = make_calc(
        [P(EXT_FAN_MIN, PT_EXTRA_PARAM), P(OP_MULTI), P(2),
         P(OP_ADD), P(EXT_FAN_MAX, PT_EXTRA_PARAM), P(OP_DIV), P(3)],
        desc="K4: fan_2=(2*fanMin+fanMax)/3",
    )
    calc_fan_3_K4 = make_calc(
        [P(EXT_FAN_MAX, PT_EXTRA_PARAM), P(OP_MULTI), P(2),
         P(OP_ADD), P(EXT_FAN_MIN, PT_EXTRA_PARAM), P(OP_DIV), P(3)],
        desc="K4: fan_3=(fanMin+2*fanMax)/3",
    )
    fans_K4 = make_order([
        make_modify_tag(TAG_IDS["fan_1"], P(EXT_FAN_MIN, PT_EXTRA_PARAM), desc="K4: fan_1=fanMin"),
        make_modify_tag(TAG_IDS["fan_2"], P(calc_fan_2_K4, PT_FUNC_RET), desc="K4: fan_2"),
        make_modify_tag(TAG_IDS["fan_3"], P(calc_fan_3_K4, PT_FUNC_RET), desc="K4: fan_3"),
        make_modify_tag(TAG_IDS["fan_4"], P(EXT_FAN_MAX, PT_EXTRA_PARAM), desc="K4: fan_4=fanMax"),
        make_modify_tag(TAG_IDS["fan_5"], P(0), desc="K4: fan_5=0"),
    ], desc="K=4 fans")

    # K=5：fan_2 = fanMin + (fanMax-fanMin)/4 = (3*fanMin + fanMax)/4
    # fan_3 = (fanMin + fanMax)/2
    # fan_4 = (fanMin + 3*fanMax)/4
    calc_fan_2_K5 = make_calc(
        [P(EXT_FAN_MIN, PT_EXTRA_PARAM), P(OP_MULTI), P(3),
         P(OP_ADD), P(EXT_FAN_MAX, PT_EXTRA_PARAM), P(OP_DIV), P(4)],
        desc="K5: fan_2=(3*fanMin+fanMax)/4",
    )
    calc_fan_3_K5 = make_calc(
        [P(EXT_FAN_MIN, PT_EXTRA_PARAM), P(OP_ADD), P(EXT_FAN_MAX, PT_EXTRA_PARAM), P(OP_DIV), P(2)],
        desc="K5: fan_3=(fanMin+fanMax)/2",
    )
    calc_fan_4_K5 = make_calc(
        [P(EXT_FAN_MAX, PT_EXTRA_PARAM), P(OP_MULTI), P(3),
         P(OP_ADD), P(EXT_FAN_MIN, PT_EXTRA_PARAM), P(OP_DIV), P(4)],
        desc="K5: fan_4=(fanMin+3*fanMax)/4",
    )
    fans_K5 = make_order([
        make_modify_tag(TAG_IDS["fan_1"], P(EXT_FAN_MIN, PT_EXTRA_PARAM), desc="K5: fan_1=fanMin"),
        make_modify_tag(TAG_IDS["fan_2"], P(calc_fan_2_K5, PT_FUNC_RET), desc="K5: fan_2"),
        make_modify_tag(TAG_IDS["fan_3"], P(calc_fan_3_K5, PT_FUNC_RET), desc="K5: fan_3"),
        make_modify_tag(TAG_IDS["fan_4"], P(calc_fan_4_K5, PT_FUNC_RET), desc="K5: fan_4"),
        make_modify_tag(TAG_IDS["fan_5"], P(EXT_FAN_MAX, PT_EXTRA_PARAM), desc="K5: fan_5=fanMax"),
    ], desc="K=5 fans")

    # 5 档分支
    get_K_fa = make_get_tag(TAG_IDS["K"], desc="读 K(fan a)")
    cmp_Kf1 = make_value_compare(P(get_K_fa, PT_FUNC_RET), CMP_EQ, P(1), desc="K==1?(fan)")
    get_K_fb = make_get_tag(TAG_IDS["K"], desc="读 K(fan b)")
    cmp_Kf2 = make_value_compare(P(get_K_fb, PT_FUNC_RET), CMP_EQ, P(2), desc="K==2?(fan)")
    get_K_fc = make_get_tag(TAG_IDS["K"], desc="读 K(fan c)")
    cmp_Kf3 = make_value_compare(P(get_K_fc, PT_FUNC_RET), CMP_EQ, P(3), desc="K==3?(fan)")
    get_K_fd = make_get_tag(TAG_IDS["K"], desc="读 K(fan d)")
    cmp_Kf4 = make_value_compare(P(get_K_fd, PT_FUNC_RET), CMP_EQ, P(4), desc="K==4?(fan)")

    cond_fan_K4_or_5 = make_cond_exec(cmp_Kf4, fans_K4, fans_K5, desc="K=4 or K=5 fans")
    cond_fan_K3_or_higher = make_cond_exec(cmp_Kf3, fans_K3, cond_fan_K4_or_5, desc="K=3/4/5 fans")
    cond_fan_K2_or_higher = make_cond_exec(cmp_Kf2, fans_K2, cond_fan_K3_or_higher, desc="K=2/3/4/5 fans")
    cond_fan = make_cond_exec(cmp_Kf1, fans_K1, cond_fan_K2_or_higher, desc="算 fanAngles[1..5]")

    # ===== Step 5：算 counts[1..5]（按 K 分支 + floor 公式 + 最后一层补差）=====
    # 模式：count_r = floor(N*dist_r/total) for r<K, count_K = N - sum

    def make_count_floor(dist_tag: int, label: str) -> int:
        """生成 c_r = floor(N * dist_r / total)"""
        get_d = make_get_tag(dist_tag, desc=f"读 {label}.dist")
        get_t = make_get_tag(TAG_IDS["total"], desc=f"读 {label}.total")
        return make_calc(
            [P(EXT_N, PT_EXTRA_PARAM),
             P(OP_MULTI), P(get_d, PT_FUNC_RET),
             P(OP_DIV), P(get_t, PT_FUNC_RET)],
            desc=f"{label}: floor(N*d/t)",
        )

    # K=1: count_1=N, 其余=0
    counts_K1 = make_order([
        make_modify_tag(TAG_IDS["count_1"], P(EXT_N, PT_EXTRA_PARAM), desc="K1: c1=N"),
        make_modify_tag(TAG_IDS["count_2"], P(0)),
        make_modify_tag(TAG_IDS["count_3"], P(0)),
        make_modify_tag(TAG_IDS["count_4"], P(0)),
        make_modify_tag(TAG_IDS["count_5"], P(0)),
    ], desc="K=1 counts")

    # K=2
    calc_c1_K2 = make_count_floor(TAG_IDS["dist_1"], "K2 c1")
    set_c1_K2 = make_modify_tag(TAG_IDS["count_1"], P(calc_c1_K2, PT_FUNC_RET), desc="K2: c1")
    get_c1_for_c2_K2 = make_get_tag(TAG_IDS["count_1"], desc="K2 读 c1(c2)")
    calc_c2_K2 = make_calc(
        [P(EXT_N, PT_EXTRA_PARAM), P(OP_MINUS), P(get_c1_for_c2_K2, PT_FUNC_RET)],
        desc="K2: c2=N-c1",
    )
    counts_K2 = make_order([
        set_c1_K2,
        make_modify_tag(TAG_IDS["count_2"], P(calc_c2_K2, PT_FUNC_RET), desc="K2: c2"),
        make_modify_tag(TAG_IDS["count_3"], P(0)),
        make_modify_tag(TAG_IDS["count_4"], P(0)),
        make_modify_tag(TAG_IDS["count_5"], P(0)),
    ], desc="K=2 counts")

    # K=3
    calc_c1_K3 = make_count_floor(TAG_IDS["dist_1"], "K3 c1")
    set_c1_K3 = make_modify_tag(TAG_IDS["count_1"], P(calc_c1_K3, PT_FUNC_RET), desc="K3: c1")
    calc_c2_K3 = make_count_floor(TAG_IDS["dist_2"], "K3 c2")
    set_c2_K3 = make_modify_tag(TAG_IDS["count_2"], P(calc_c2_K3, PT_FUNC_RET), desc="K3: c2")
    get_c1_K3 = make_get_tag(TAG_IDS["count_1"], desc="K3 读 c1(c3)")
    get_c2_K3 = make_get_tag(TAG_IDS["count_2"], desc="K3 读 c2(c3)")
    calc_c3_K3 = make_calc(
        [P(EXT_N, PT_EXTRA_PARAM),
         P(OP_MINUS), P(get_c1_K3, PT_FUNC_RET),
         P(OP_MINUS), P(get_c2_K3, PT_FUNC_RET)],
        desc="K3: c3=N-c1-c2",
    )
    counts_K3 = make_order([
        set_c1_K3, set_c2_K3,
        make_modify_tag(TAG_IDS["count_3"], P(calc_c3_K3, PT_FUNC_RET), desc="K3: c3"),
        make_modify_tag(TAG_IDS["count_4"], P(0)),
        make_modify_tag(TAG_IDS["count_5"], P(0)),
    ], desc="K=3 counts")

    # K=4
    calc_c1_K4 = make_count_floor(TAG_IDS["dist_1"], "K4 c1")
    set_c1_K4 = make_modify_tag(TAG_IDS["count_1"], P(calc_c1_K4, PT_FUNC_RET), desc="K4: c1")
    calc_c2_K4 = make_count_floor(TAG_IDS["dist_2"], "K4 c2")
    set_c2_K4 = make_modify_tag(TAG_IDS["count_2"], P(calc_c2_K4, PT_FUNC_RET), desc="K4: c2")
    calc_c3_K4 = make_count_floor(TAG_IDS["dist_3"], "K4 c3")
    set_c3_K4 = make_modify_tag(TAG_IDS["count_3"], P(calc_c3_K4, PT_FUNC_RET), desc="K4: c3")
    g_c1_K4 = make_get_tag(TAG_IDS["count_1"], desc="K4 读 c1(c4)")
    g_c2_K4 = make_get_tag(TAG_IDS["count_2"], desc="K4 读 c2(c4)")
    g_c3_K4 = make_get_tag(TAG_IDS["count_3"], desc="K4 读 c3(c4)")
    calc_c4_K4 = make_calc(
        [P(EXT_N, PT_EXTRA_PARAM),
         P(OP_MINUS), P(g_c1_K4, PT_FUNC_RET),
         P(OP_MINUS), P(g_c2_K4, PT_FUNC_RET),
         P(OP_MINUS), P(g_c3_K4, PT_FUNC_RET)],
        desc="K4: c4=N-c1-c2-c3",
    )
    counts_K4 = make_order([
        set_c1_K4, set_c2_K4, set_c3_K4,
        make_modify_tag(TAG_IDS["count_4"], P(calc_c4_K4, PT_FUNC_RET), desc="K4: c4"),
        make_modify_tag(TAG_IDS["count_5"], P(0)),
    ], desc="K=4 counts")

    # K=5
    calc_c1_K5 = make_count_floor(TAG_IDS["dist_1"], "K5 c1")
    set_c1_K5 = make_modify_tag(TAG_IDS["count_1"], P(calc_c1_K5, PT_FUNC_RET), desc="K5: c1")
    calc_c2_K5 = make_count_floor(TAG_IDS["dist_2"], "K5 c2")
    set_c2_K5 = make_modify_tag(TAG_IDS["count_2"], P(calc_c2_K5, PT_FUNC_RET), desc="K5: c2")
    calc_c3_K5 = make_count_floor(TAG_IDS["dist_3"], "K5 c3")
    set_c3_K5 = make_modify_tag(TAG_IDS["count_3"], P(calc_c3_K5, PT_FUNC_RET), desc="K5: c3")
    calc_c4_K5 = make_count_floor(TAG_IDS["dist_4"], "K5 c4")
    set_c4_K5 = make_modify_tag(TAG_IDS["count_4"], P(calc_c4_K5, PT_FUNC_RET), desc="K5: c4")
    g_c1_K5 = make_get_tag(TAG_IDS["count_1"], desc="K5 读 c1(c5)")
    g_c2_K5 = make_get_tag(TAG_IDS["count_2"], desc="K5 读 c2(c5)")
    g_c3_K5 = make_get_tag(TAG_IDS["count_3"], desc="K5 读 c3(c5)")
    g_c4_K5 = make_get_tag(TAG_IDS["count_4"], desc="K5 读 c4(c5)")
    calc_c5_K5 = make_calc(
        [P(EXT_N, PT_EXTRA_PARAM),
         P(OP_MINUS), P(g_c1_K5, PT_FUNC_RET),
         P(OP_MINUS), P(g_c2_K5, PT_FUNC_RET),
         P(OP_MINUS), P(g_c3_K5, PT_FUNC_RET),
         P(OP_MINUS), P(g_c4_K5, PT_FUNC_RET)],
        desc="K5: c5=N-c1..c4",
    )
    counts_K5 = make_order([
        set_c1_K5, set_c2_K5, set_c3_K5, set_c4_K5,
        make_modify_tag(TAG_IDS["count_5"], P(calc_c5_K5, PT_FUNC_RET), desc="K5: c5"),
    ], desc="K=5 counts")

    get_K_ca = make_get_tag(TAG_IDS["K"], desc="读 K(cnt a)")
    cmp_Kc1 = make_value_compare(P(get_K_ca, PT_FUNC_RET), CMP_EQ, P(1), desc="K==1?(cnt)")
    get_K_cb = make_get_tag(TAG_IDS["K"], desc="读 K(cnt b)")
    cmp_Kc2 = make_value_compare(P(get_K_cb, PT_FUNC_RET), CMP_EQ, P(2), desc="K==2?(cnt)")
    get_K_cc = make_get_tag(TAG_IDS["K"], desc="读 K(cnt c)")
    cmp_Kc3 = make_value_compare(P(get_K_cc, PT_FUNC_RET), CMP_EQ, P(3), desc="K==3?(cnt)")
    get_K_cd = make_get_tag(TAG_IDS["K"], desc="读 K(cnt d)")
    cmp_Kc4 = make_value_compare(P(get_K_cd, PT_FUNC_RET), CMP_EQ, P(4), desc="K==4?(cnt)")

    cond_cnt_K4_or_5 = make_cond_exec(cmp_Kc4, counts_K4, counts_K5, desc="K=4 or K=5 counts")
    cond_cnt_K3_or_higher = make_cond_exec(cmp_Kc3, counts_K3, cond_cnt_K4_or_5, desc="K=3/4/5 counts")
    cond_cnt_K2_or_higher = make_cond_exec(cmp_Kc2, counts_K2, cond_cnt_K3_or_higher, desc="K=2/3/4/5 counts")
    cond_counts = make_cond_exec(cmp_Kc1, counts_K1, cond_cnt_K2_or_higher, desc="算 counts[1..5]")

    # ===== Step 6：算 cumulative[1..5] =====
    # cum_1 = count_1
    get_c1_cum = make_get_tag(TAG_IDS["count_1"], desc="读 c1(cum1)")
    set_cum_1 = make_modify_tag(TAG_IDS["cum_1"], P(get_c1_cum, PT_FUNC_RET), desc="cum_1=c1")
    # cum_2 = cum_1 + c2
    g_cum_1_for_2 = make_get_tag(TAG_IDS["cum_1"], desc="读 cum_1(cum2)")
    g_c2_for_2 = make_get_tag(TAG_IDS["count_2"], desc="读 c2(cum2)")
    calc_cum_2 = make_calc(
        [P(g_cum_1_for_2, PT_FUNC_RET), P(OP_ADD), P(g_c2_for_2, PT_FUNC_RET)],
        desc="cum_2 = cum_1 + c2",
    )
    set_cum_2 = make_modify_tag(TAG_IDS["cum_2"], P(calc_cum_2, PT_FUNC_RET), desc="cum_2")
    # cum_3
    g_cum_2_for_3 = make_get_tag(TAG_IDS["cum_2"], desc="读 cum_2(cum3)")
    g_c3_for_3 = make_get_tag(TAG_IDS["count_3"], desc="读 c3(cum3)")
    calc_cum_3 = make_calc(
        [P(g_cum_2_for_3, PT_FUNC_RET), P(OP_ADD), P(g_c3_for_3, PT_FUNC_RET)],
        desc="cum_3",
    )
    set_cum_3 = make_modify_tag(TAG_IDS["cum_3"], P(calc_cum_3, PT_FUNC_RET), desc="cum_3")
    # cum_4
    g_cum_3_for_4 = make_get_tag(TAG_IDS["cum_3"], desc="读 cum_3(cum4)")
    g_c4_for_4 = make_get_tag(TAG_IDS["count_4"], desc="读 c4(cum4)")
    calc_cum_4 = make_calc(
        [P(g_cum_3_for_4, PT_FUNC_RET), P(OP_ADD), P(g_c4_for_4, PT_FUNC_RET)],
        desc="cum_4",
    )
    set_cum_4 = make_modify_tag(TAG_IDS["cum_4"], P(calc_cum_4, PT_FUNC_RET), desc="cum_4")
    # cum_5
    g_cum_4_for_5 = make_get_tag(TAG_IDS["cum_4"], desc="读 cum_4(cum5)")
    g_c5_for_5 = make_get_tag(TAG_IDS["count_5"], desc="读 c5(cum5)")
    calc_cum_5 = make_calc(
        [P(g_cum_4_for_5, PT_FUNC_RET), P(OP_ADD), P(g_c5_for_5, PT_FUNC_RET)],
        desc="cum_5",
    )
    set_cum_5 = make_modify_tag(TAG_IDS["cum_5"], P(calc_cum_5, PT_FUNC_RET), desc="cum_5")

    compute_cums = make_order([set_cum_1, set_cum_2, set_cum_3, set_cum_4, set_cum_5], desc="算 cumulative")

    # ===== Step A：i=0（初始化）=====
    init_i = make_modify_tag(TAG_IDS["i"], P(0), desc="初始化 i=0")

    # ===== 整个 init_order：依次执行所有预计算 =====
    init_order = make_order(
        [init_i, cond_K, compute_dists, cond_total, cond_fan, cond_counts, compute_cums],
        desc="预计算（K, dist, total, fan, count, cum）",
    )

    # ===== Step B：单发循环内 — i++ =====
    get_i_for_inc = make_get_tag(TAG_IDS["i"], desc="读 i(i++)")
    calc_inc_i = make_calc(
        [P(get_i_for_inc, PT_FUNC_RET), P(OP_ADD), P(1)],
        desc="i+1",
    )
    inc_i = make_modify_tag(TAG_IDS["i"], P(calc_inc_i, PT_FUNC_RET), desc="i = i+1")

    # ===== Step C：3 套层流程 ORDER =====
    # 每层 ORDER = 设置 curFan / curDist / curCnt / curJ / curStagger
    def make_layer_order(layer_r: int, fan_tag: int, dist_tag: int, count_tag: int,
                          cum_prev_tag: int | None) -> int:
        """
        生成第 r 层的 ORDER 节点。
        - curFan = fan_r
        - curDist = dist_r
        - curCnt = count_r
        - curJ = i - cum_{r-1} - 1（cum_0 = 0）
        - curStagger = 1 (奇数 r) / 2 (偶数 r)
        """
        get_fan_r = make_get_tag(fan_tag, desc=f"r={layer_r} 读 fan_{layer_r}")
        set_curFan = make_modify_tag(TAG_IDS["curFan"], P(get_fan_r, PT_FUNC_RET), desc=f"r={layer_r} curFan")
        get_dist_r = make_get_tag(dist_tag, desc=f"r={layer_r} 读 dist_{layer_r}")
        set_curDist = make_modify_tag(TAG_IDS["curDist"], P(get_dist_r, PT_FUNC_RET), desc=f"r={layer_r} curDist")
        get_cnt_r = make_get_tag(count_tag, desc=f"r={layer_r} 读 count_{layer_r}")
        set_curCnt = make_modify_tag(TAG_IDS["curCnt"], P(get_cnt_r, PT_FUNC_RET), desc=f"r={layer_r} curCnt")

        # curJ = i - cum_{r-1} - 1
        get_i_for_j = make_get_tag(TAG_IDS["i"], desc=f"r={layer_r} 读 i(j)")
        if cum_prev_tag is None:  # r=1：curJ = i - 1
            calc_j = make_calc([P(get_i_for_j, PT_FUNC_RET), P(OP_MINUS), P(1)],
                               desc=f"r=1 j=i-1")
        else:
            get_cum_prev = make_get_tag(cum_prev_tag, desc=f"r={layer_r} 读 cum_{layer_r-1}")
            calc_j = make_calc(
                [P(get_i_for_j, PT_FUNC_RET),
                 P(OP_MINUS), P(get_cum_prev, PT_FUNC_RET),
                 P(OP_MINUS), P(1)],
                desc=f"r={layer_r} j=i-cum_{layer_r-1}-1",
            )
        set_curJ = make_modify_tag(TAG_IDS["curJ"], P(calc_j, PT_FUNC_RET), desc=f"r={layer_r} curJ")

        stagger_value = 2 if layer_r % 2 == 0 else 1
        set_stagger = make_modify_tag(TAG_IDS["curStagger"], P(stagger_value),
                                       desc=f"r={layer_r} curStagger={stagger_value}")

        return make_order([set_curFan, set_curDist, set_curCnt, set_curJ, set_stagger],
                          desc=f"层 r={layer_r}")

    layer_1_order = make_layer_order(1, TAG_IDS["fan_1"], TAG_IDS["dist_1"], TAG_IDS["count_1"], None)
    layer_2_order = make_layer_order(2, TAG_IDS["fan_2"], TAG_IDS["dist_2"], TAG_IDS["count_2"], TAG_IDS["cum_1"])
    layer_3_order = make_layer_order(3, TAG_IDS["fan_3"], TAG_IDS["dist_3"], TAG_IDS["count_3"], TAG_IDS["cum_2"])
    layer_4_order = make_layer_order(4, TAG_IDS["fan_4"], TAG_IDS["dist_4"], TAG_IDS["count_4"], TAG_IDS["cum_3"])
    layer_5_order = make_layer_order(5, TAG_IDS["fan_5"], TAG_IDS["dist_5"], TAG_IDS["count_5"], TAG_IDS["cum_4"])

    # ===== Step D：反查 r 嵌套 condition（5 路）=====
    # if i ≤ cum_1 → r=1; elif i ≤ cum_2 → r=2; ... elif i ≤ cum_4 → r=4; else r=5
    g_cum_1_b = make_get_tag(TAG_IDS["cum_1"], desc="读 cum_1(分支)")
    g_i_a = make_get_tag(TAG_IDS["i"], desc="读 i(分支a)")
    cmp_i_le_cum_1 = make_value_compare(P(g_cum_1_b, PT_FUNC_RET), CMP_GE,
                                          P(g_i_a, PT_FUNC_RET), desc="cum_1 ≥ i ?")

    g_cum_2_b = make_get_tag(TAG_IDS["cum_2"], desc="读 cum_2(分支)")
    g_i_b = make_get_tag(TAG_IDS["i"], desc="读 i(分支b)")
    cmp_i_le_cum_2 = make_value_compare(P(g_cum_2_b, PT_FUNC_RET), CMP_GE,
                                          P(g_i_b, PT_FUNC_RET), desc="cum_2 ≥ i ?")

    g_cum_3_b = make_get_tag(TAG_IDS["cum_3"], desc="读 cum_3(分支)")
    g_i_c = make_get_tag(TAG_IDS["i"], desc="读 i(分支c)")
    cmp_i_le_cum_3 = make_value_compare(P(g_cum_3_b, PT_FUNC_RET), CMP_GE,
                                          P(g_i_c, PT_FUNC_RET), desc="cum_3 ≥ i ?")

    g_cum_4_b = make_get_tag(TAG_IDS["cum_4"], desc="读 cum_4(分支)")
    g_i_d = make_get_tag(TAG_IDS["i"], desc="读 i(分支d)")
    cmp_i_le_cum_4 = make_value_compare(P(g_cum_4_b, PT_FUNC_RET), CMP_GE,
                                          P(g_i_d, PT_FUNC_RET), desc="cum_4 ≥ i ?")

    # 嵌套：从最深的 r=5 开始向外
    cond_r4_or_r5 = make_cond_exec(cmp_i_le_cum_4, layer_4_order, layer_5_order,
                                    desc="if i≤cum_4 then 层4 else 层5")
    cond_r3_or_higher = make_cond_exec(cmp_i_le_cum_3, layer_3_order, cond_r4_or_r5,
                                        desc="if i≤cum_3 then 层3 else 分支 4/5")
    cond_r2_or_higher = make_cond_exec(cmp_i_le_cum_2, layer_2_order, cond_r3_or_higher,
                                        desc="if i≤cum_2 then 层2 else 分支 3/4/5")
    branch_r = make_cond_exec(cmp_i_le_cum_1, layer_1_order, cond_r2_or_higher,
                               desc="反查 r 并设置工作 Tag（5 路）")

    # ===== Step E：算 angle_offset = curFan*(2*curJ + curStagger - curCnt)/(2*curCnt) =====
    get_j_for_angle = make_get_tag(TAG_IDS["curJ"], desc="读 curJ(angle)")
    get_stagger_for_angle = make_get_tag(TAG_IDS["curStagger"], desc="读 curStagger(angle)")
    get_cnt_for_angle_a = make_get_tag(TAG_IDS["curCnt"], desc="读 curCnt(angle分子)")
    get_fan_for_angle = make_get_tag(TAG_IDS["curFan"], desc="读 curFan(angle)")
    get_cnt_for_angle_b = make_get_tag(TAG_IDS["curCnt"], desc="读 curCnt(angle分母)")

    angle_offset_eid = make_calc(
        [P(get_j_for_angle, PT_FUNC_RET),
         P(OP_MULTI), P(2),
         P(OP_ADD), P(get_stagger_for_angle, PT_FUNC_RET),
         P(OP_MINUS), P(get_cnt_for_angle_a, PT_FUNC_RET),
         P(OP_MULTI), P(get_fan_for_angle, PT_FUNC_RET),
         P(OP_DIV), P(get_cnt_for_angle_b, PT_FUNC_RET),
         P(OP_DIV), P(2)],
        desc="angle_offset",
    )

    # ===== Step F：abs_angle = caster.facing + angle_offset =====
    facing_eid = make_get_attr(91, desc="caster.facing")
    abs_angle_calc = make_calc(
        [P(facing_eid, PT_FUNC_RET), P(OP_ADD), P(angle_offset_eid, PT_FUNC_RET)],
        desc="abs_angle = facing + offset",
    )
    set_abs_angle = make_modify_tag(TAG_IDS["curAbsAngle"], P(abs_angle_calc, PT_FUNC_RET),
                                      desc="写入 curAbsAngle")

    # ===== Step G：cos / sin / spawn_X / spawn_Y =====
    get_abs_for_cos = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle(cos)")
    cos_eid = b.alloc_eid()
    cos_payload = {"ID": cos_eid, "SkillEffectType": ET["COS"],
                   "Params": [P(get_abs_for_cos, PT_FUNC_RET)]}
    b.add_node("TSET_MATH_COS", cos_eid, cos_payload, desc="cos", effect_type=ET["COS"])

    get_abs_for_sin = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle(sin)")
    sin_eid = b.alloc_eid()
    sin_payload = {"ID": sin_eid, "SkillEffectType": ET["SIN"],
                   "Params": [P(get_abs_for_sin, PT_FUNC_RET)]}
    b.add_node("TSET_MATH_SIN", sin_eid, sin_payload, desc="sin", effect_type=ET["SIN"])

    caster_x_eid = make_get_attr(59, desc="caster.X")
    caster_y_eid = make_get_attr(60, desc="caster.Y")
    get_dist_for_x = make_get_tag(TAG_IDS["curDist"], desc="读 curDist(x)")
    get_dist_for_y = make_get_tag(TAG_IDS["curDist"], desc="读 curDist(y)")

    spawn_x_eid = make_calc(
        [P(cos_eid, PT_FUNC_RET),
         P(OP_MULTI), P(get_dist_for_x, PT_FUNC_RET),
         P(OP_DIV), P(10000),
         P(OP_ADD), P(caster_x_eid, PT_FUNC_RET)],
        desc="spawn_X",
    )
    spawn_y_eid = make_calc(
        [P(sin_eid, PT_FUNC_RET),
         P(OP_MULTI), P(get_dist_for_y, PT_FUNC_RET),
         P(OP_DIV), P(10000),
         P(OP_ADD), P(caster_y_eid, PT_FUNC_RET)],
        desc="spawn_Y",
    )

    # ===== Step H：CREATE_BULLET =====
    get_abs_for_bullet = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle(子弹)")

    # 出手点高度（Z）：参考 30122002 节点 32003945 的 Z 配法 — 用施法者的胶囊中点假高度
    bullet_height_eid = b.alloc_eid()
    bullet_height_payload = {
        "ID": bullet_height_eid, "SkillEffectType": ET["GET_FIXTURE_CENTER_Z"],
        "Params": [P(75, PT_ATTR), P(1)],   # 75=施法者, 1=取胶囊中点
    }
    b.add_node("TSET_GET_FIXTURE_CENTER_Z", bullet_height_eid, bullet_height_payload,
               desc="获取出手点假高度 Z", effect_type=ET["GET_FIXTURE_CENTER_Z"])

    bullet_eid = b.alloc_eid()
    bullet_payload = {
        "ID": bullet_eid, "SkillEffectType": ET["BULLET"],
        "Params": [
            P(EXT_BULLET_ID, PT_EXTRA_PARAM),       # 0  子弹ID
            P(get_abs_for_bullet, PT_FUNC_RET),     # 1  朝向
            P(spawn_x_eid, PT_FUNC_RET),            # 2  X
            P(spawn_y_eid, PT_FUNC_RET),            # 3  Y
            P(1, PT_COMMON_PARAM),                  # 4  位置类型=自定义
            P(0), P(0),                             # 5,6  X/Y 偏移
            P(0), P(0), P(0),                       # 7,8,9
            P(41, PT_COMMON_PARAM),                 # 10 角度类型
            P(0),                                   # 11
            P(bullet_height_eid, PT_FUNC_RET),      # 12 Z = 出手点假高度（参考 32003945）
            P(0), P(1),                             # 13,14
        ],
    }
    b.add_node("TSET_CREATE_BULLET", bullet_eid, bullet_payload, desc="创建子弹",
               effect_type=ET["BULLET"])

    # ===== single_order =====
    single_order = make_order(
        [inc_i, branch_r, set_abs_angle, bullet_eid],
        desc="单发流程",
    )

    # ===== REPEAT_EXECUTE =====
    repeat_eid = b.alloc_eid()
    repeat_payload = {
        "ID": repeat_eid, "SkillEffectType": ET["REPEAT"],
        "Params": [
            P(0),                                  # 间隔帧 = 0（无间隔，同帧发射）
            P(EXT_N, PT_EXTRA_PARAM),              # 次数 = N
            P(1),                                  # 立即执行
            P(single_order),                       # 子效果
            P(0), P(0), P(0), P(0), P(0),
            P(1),                                  # 急速
        ],
    }
    b.add_node("TSET_REPEAT_EXECUTE", repeat_eid, repeat_payload,
               desc="重复 N 次", effect_type=ET["REPEAT"])

    # ===== 模板根 ORDER (IsTemplate=true) =====
    # 用固定 EID（ROOT_TEMPLATE_EID），避免每次重生成时 EID 漂移。
    # 编辑器 template2Nodes 字典按 ID 索引且重载时不清理，EID 漂移会导致老模板残留在工具栏列表中。
    root_eid = ROOT_TEMPLATE_EID
    root_payload = {
        "ID": root_eid, "SkillEffectType": ET["ORDER"],
        "Params": [P(init_order), P(repeat_eid)],
    }
    b.add_node(
        "TSET_ORDER_EXECUTE", root_eid, root_payload,
        is_template=True, template_params=TPARAMS,
        desc="扇形分层弹幕模板根 (K=1~3)",
        effect_type=ET["ORDER"],
    )

    return b


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    b = build()
    b.emit(OUTPUT)
    print(f"✓ 模板生成成功 → {OUTPUT}")
    print(f"  节点数: {len(b.refs)}")
    print(f"  边数:   {len(b.edges)}")


if __name__ == "__main__":
    main()
