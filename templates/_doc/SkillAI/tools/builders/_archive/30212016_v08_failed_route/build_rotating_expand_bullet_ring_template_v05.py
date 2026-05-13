#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旋转扩张子弹圈 — SkillEditor 通用技能模板生成器（v0.5）

== v0.5 净改动（2026-05-09，接力 acb652403da465fec）==
用户拍板走 1860216 风格"内置 BulletConfig + 字段端口连接 OnTick"。
v0.4 是双根模板（L1 主流程根 32300001 + L2 OnTick 工具根 32300101，
调用方手动接 BulletConfig.AfterBornSkillEffectExecuteInfo）— 反模式。
v0.5 在模板内部新增 BulletConfigNode + ModelConfigNode + 字段端口边，
让模板自包含子弹定义，调用方无需任何手动接线。

GATE-0.5 关键洞察（2026-05-09 红队研究 1860216）：
  1. SkillEffectType=118 = TSET_RUN_SKILL_EFFECT_TEMPLATE 是「调用方使用模板」入口；
     模板内 ParamType=4 (TPT_EXTRA_PARAM) 可索引到 TemplateParam[i]，但**只能影响
     SkillEffect.Params 数组**，不能直接改 BulletConfig 字段值。
  2. 1860216 链子弹模板"暴露 model TemplateParam"实际是**有名无实**——模板内
     BulletConfig.Model=30008 死值，model EXT_PARAM 没真消费（只作 UI 占位）。
  3. **真正能影响 BulletConfig 字段的机制 = 字段端口连接**：
     edge.outputFieldName="PackedMembersOutput" + outputPortIdentifier="字段路径"
     例如 AfterBornSkillEffectExecuteInfo.SkillEffectConfigID 或 Model。
     连入端必须是另一个节点（ModelConfigNode 给 Model；SkillEffectConfigNode 给
     AfterBornSkillEffectExecuteInfo.SkillEffectConfigID）。运行时 BulletConfig 加载
     时该字段值=连入节点的 ID。
  4. 因此 v0.5 实现策略：
     - 模板内置 BulletConfigNode（IsTemplate=false，新分配 32300150）
     - 模板内置 ModelConfigNode（默认 320149 普通飞叶模型）
     - 字段端口边 BulletConfig.Model ← ModelConfigNode
     - 字段端口边 BulletConfig.AfterBornSkillEffectExecuteInfo.SkillEffectConfigID ← OnTick init (32300101)
     - 主流程 TSET_CREATE_BULLET 不再读 EXT_PARAM bulletID，直接 Params[0]=32300150（死值引用）
     - bulletID EXT_PARAM 移除；新暴露：model（直接改 ModelConfigNode）由用户在面板手动调
     - 子弹时长/速度等 BulletConfig 字段由用户直接编辑 BulletConfigNode 的 ConfigJson

== TemplateParams 9 项（v0.5，全部算法系真消费）==
[1]  bulletCount N        int     8       ✓ 主流程 + REPEAT 次数
[2]  initialRadius R0     int     200     ✓ 主流程 spawn + OnTick init R(0)（米→单位 *100）
[3]  tangentOffsetAngle φ int     0       ✓ 主流程 heading + OnTick init θ_0 反推
[4]  radialVelocity vR    int     10      ✓ OnTick init currentRadialSpeed=vR (单位/帧)
[5]  radialAcceleration aR int    0       ✓ OnTick currentRadialSpeed += aR/30 (单位/秒²→帧²)
[6]  angularVelocity ω    int     3       ✓ OnTick θ += ω (度/帧)
[7]  maxRadius            int     1500    ✓ R > maxRadius → DESTROY (op=3)
[8]  minRadius            int     0       ✓ R < minRadius → DESTROY (op=5)
[9]  followPlayer 0/1     int     1       ✓ 1=每帧重读 caster.X/Y / 0=固定 X0/Y0 (op=2)

注：v0.4 的 [1] bulletID 删除（v0.5 BulletConfig 内置）。
注：model/scale/lifetime/effects 不暴露为 EXT_PARAM——用户在 SkillEditor 面板上直接
    修改 ModelConfigNode 的 ID 或 BulletConfigNode 的 ConfigJson 字段（这是 1860216
    严格风格的代价：模板对 BulletConfig 全权负责，调用方只能改"算法系"参数）。

== 单位约定（用户暴露层 vs 模板内部）==
**因项目无"运行时乘法 effect 节点"可以让 EXT_PARAM 在编译期保留为变量、运行时做 ÷100/×30 转换**，
v0.5 退化到「暴露层 = 单位制（与项目原生 30212010 同款）」+ Desc 写明换算关系。
  - 1 米 = 100 单位
  - 1 秒 = 30 帧
  - R0/maxR/minR 单位「项目坐标系单位」（默认 200 ≈ 2 米）
  - vR 单位「单位/帧」（默认 10/帧 ≈ 300 单位/秒 ≈ 3 米/秒）
  - ω 单位「度/帧」（默认 3°/帧 ≈ 90°/秒）
  - aR 单位「单位/秒²」（模板内每帧 aR/30 即增量；默认 0）
  - 子弹时长由 BulletConfig.LastTime（帧单位）配置；默认 150 帧 = 5 秒

== ID 段位 ==
模板根 EID = 32300001（固定，PostMortem #010）
SkillEffectConfig 段：32300002 起
SkillTagsConfig 段：32300700 起
BulletConfig 段：32300150 起（v0.5 新增）
ModelConfig 引用：320149（默认普通飞叶子弹模型，已在表内）

== 拓扑 diff（v0.4 → v0.5）==
节点：v0.4 ~70 节点 → v0.5 +2（BulletConfig + ModelConfig）= ~72
边：  v0.4 ~90 边 → v0.5 +2（Model 字段端口 + AfterBorn 字段端口）= ~92
TemplateParams：v0.4 10 项 → v0.5 9 项（删 bulletID）

== 参考真实样本 ==
- 1860216【模板】链子弹：内置 BulletConfig + PackedMembersOutput.AfterBorn 字段端口
- 30212009 千叶散华：BulletConfig + PackedMembersOutput.Model 字段端口
- 30212010 叶散风行：OnTick 链结构原型
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
BULLET_CONFIG_ID  = 32300150  # v0.5 新增：模板内置 BulletConfig
DEFAULT_MODEL_ID  = 320149    # 默认子弹模型（普通飞叶）— 已在 ModelConfig 表内
ONTICK_INIT_EID   = 32300101  # OnTick 工具子图根（沿用 v0.4）

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
        self.field_port_edges = []  # v0.5：字段端口边（手动构造，不走自动派生）
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
        """v0.5：在两个节点间添加字段端口边。
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
        # 自动建边（沿用 v0.4 的 PackedParamsOutput 自动派生逻辑）
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

        # v0.5 新增：合并字段端口边到 edges 列表
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


# 模板参数索引 (1-based, PT=4 EXTRA_PARAM) — v0.5 删 bulletID 后剩 9 项
EXT_N         = 1
EXT_R0        = 2
EXT_PHI       = 3
EXT_VR        = 4
EXT_AR        = 5
EXT_OMEGA     = 6
EXT_MAX_R     = 7
EXT_MIN_R     = 8
EXT_FOLLOW    = 9


# v0.5 默认值（参考"花瓣绽放"预设 + 用户接力消息默认值清单 + 单位制对齐）
# 用户层提示：1 米 = 100 单位 / 1 秒 = 30 帧
TPARAMS = [
    # [1] bulletCount N
    {"DefaultValueDesc": "", "Name": "[阵型] 子弹数N", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":8,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [2] initialRadius R0
    {"DefaultValueDesc": "起始半径(单位)。子弹生成时距主角的距离。默认 200 单位 = 2 米。1 米 = 100 单位。",
     "Name": "[阵型] 初始半径R0",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":200,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [3] tangentOffsetAngle φ
    {"DefaultValueDesc": "切线偏移角(度)。0=花瓣绽放(长边沿切线)，90=刺向外(长边沿径向)。",
     "Name": "[阵型] 切线偏移角φ(度)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [4] radialVelocity vR
    {"DefaultValueDesc": "径向速度(单位/帧)。正值=向外飞，负值=向内收。默认 10/帧 ≈ 300单位/秒 ≈ 3米/秒(比主角 4.5米/秒慢)。",
     "Name": "[运动] 径向速度vR(单位/帧)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":10,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [5] radialAcceleration aR
    {"DefaultValueDesc": "径向加速度(单位/秒²)。aR<0配合vR>0=先扩后缩。模板内每帧加 aR/30。默认 0 = 匀速。",
     "Name": "[运动] 径向加速度aR(单位/秒²)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [6] angularVelocity ω
    {"DefaultValueDesc": "旋转速度(度/帧)。正值=逆时针，负值=顺时针。默认 3°/帧 = 90°/秒(一秒1/4圈)。",
     "Name": "[运动] 整团角速度ω(度/帧)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":3,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [7] maxRadius
    {"DefaultValueDesc": "最大半径上限(单位)。R 超过则销毁。默认 1500 单位 = 15 米。",
     "Name": "[终止] maxRadius(最大半径)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":1500,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [8] minRadius
    {"DefaultValueDesc": "最小半径下限(单位)。R 小于则销毁。默认 0 永不触发；配合 aR<0 做收缩玩法时调高。",
     "Name": "[终止] minRadius(最小半径)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [9] followPlayer
    {"DefaultValueDesc": "0=圆心固定在 cast 位置(古早风格)；1=每帧跟随 caster(现代 MOBA 标配)。默认 1。",
     "Name": "[运动] followPlayer(是否跟随主角)",
     "RefTypeName": "", "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":1,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
]


def make_default_bullet_config_payload() -> dict:
    """v0.5 内置 BulletConfig 默认配置（参考 30212009 普通飞叶子弹 320159 + 1860216 链子弹默认）。
    所有字段写死，用户在 SkillEditor 面板上需要时可直接编辑（特别是 LastTime 决定子弹生命周期）。
    Model 字段会被 ModelConfigNode 字段端口边覆盖（运行时取节点 ID = 320149 默认）。
    AfterBornSkillEffectExecuteInfo.SkillEffectConfigID 会被 OnTick init effect 字段端口边覆盖。"""
    return {
        "ID": BULLET_CONFIG_ID,
        "FlyType": 1,                              # 1 = 直线飞行（占位，OnTick 会覆盖位置）
        "ChaseTargetEnemy_AttachPos": 0,
        "ChaseTargetEnemy_FaceToTarget": True,
        "ChaseTargetEnemy_PitchFaceToTarget": True,
        "IsAiEscape": False,
        "AngleAdjustType": 0,
        "Speed": 0,                                # 0 = 不靠 BulletConfig 自带速度（OnTick 全权管位置）
        "AcceSpeed": 0,
        "MaxSpeed": 0,
        "TurnSpeed": 0,
        "TurnAcceSpeed": 0,
        "MaxTurnSpeed": 0,
        "IsCloseTurnAutoHit": False,
        "PitchTurnSpeed": 0,
        "PitchTurnAcceSpeed": 0,
        "PitchMaxTurnSpeed": 0,
        "IsOpenPhysicalReflect": False,
        "PhysicalReflectCount": 0,
        "PhysicalReflectEndActionType": 0,
        "TracePathType": 0,
        "TracePathParams": [],
        "LastTime": 150,                           # 150 帧 = 5 秒（兜底；maxR/minR 通常先触发）
        "delayDestroyTime": 0,
        "DestroyWhenCreatorDie": True,
        "Hp": 100,
        "ATK": 0,
        "BeforeBornSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "AfterBornSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": ONTICK_INIT_EID},
        "DieSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "Model": DEFAULT_MODEL_ID,                # 320149 默认普通飞叶（字段端口边可覆盖）
        "ModelBaseScalePercent": 0,
        "ChainModel": 0,
        "ChainModelScalePercent": 0,
        "ChainTilingFactor": 100,
        "DisappearEffect": 0,
        "LifeFlag": 1,
        "MaxDistance": 0,
        "TrackEntityNoTargetSkillEffectConfigID": 0,
        "IsDieKeepMove": False,
    }


def make_default_model_config_payload(model_id: int) -> dict:
    """ModelConfigNode 是 ModelConfig 表的整行数据缓存——节点 ID 即 Model 表 ID。
    模板内置 320149 普通飞叶模型作为默认。
    用户在面板上修改 ModelConfigNode 即可换子弹模型。
    （Config 数据由编辑器在加载时从表回读，这里只需占位 ID + 节点声明即可。）"""
    return {
        "SheetRowIndex": 0,
        "ID": model_id,
        # 其余字段编辑器会在加载时按 TableTash 校验后从表自动 hydrate；
        # 这里写默认占位值即可（不影响运行时表读取）。
        "ModelTopUIHeight": 0, "InteractionRange": 0, "ModelInitAngle": 0,
        "ModelPath": "", "IsLoadModelSync": False,
        "DeathEffectId": 0, "DeathTime": 0, "ModelAmplify": 100,
        "ReadyScale": 0, "BodyType": 2, "BodyLevelType": 0,
        "BodyForceMoveFactor": 100, "FixtureConfigId": [], "InEyeModelId": 0,
        "ModelBornAudio": 0, "ModelBornAudioSoundType": 1,
        "ModelBornAudioStopOnDisable": False, "ModelBornAudioFadeOutFrame": 6,
        "ModelLoopAudio": 0, "ModelLoopAudioSoundType": 1,
        "ModelLoopAudioStopOnDisable": True, "ModelLoopAudioFadeOutFrame": 6,
        "ModelDeathAudio": 0, "ModelDeathAudioSoundType": 1,
        "ModelDeathAudioStopOnDisable": False, "ModelDeathAudioFadeOutFrame": 6,
        "AttachPos": 0, "Flags": 0, "HitEffectAmplify": 100,
        "BattleStateBaseSpeed": 0, "NormalStateBaseSpeed": 0,
        "LockCircleRadius": 0, "IsFollowScale": False, "IsFollowAnim": False,
        "MapAnimType": 0, "MapAnimSubType": 0, "SelectLevel": 0,
        "IsNotBias": 0, "IsDeadDelete": False, "ViewEventTargetType": 0,
        "DisappearType": 2, "BaseScale": 0, "MapCollider": [],
        "MapStartSoundID": 0, "MapDestroySoundID": 0, "MapTriggerSoundID": 0,
        "TransformType": 2, "MonsterSect": 0,
    }


def build():
    b = TplBuilder()

    # ----- SkillTagsConfigNode 集合（沿用 v0.4 9 项）-----
    for name, tid in TAG_IDS.items():
        payload = {"ID": tid, "TagType": 0, "Desc": f"_旋转扩张_{name}",
                   "NameKey": 0, "DefaultValue": 0, "FinalValueEffectID": 0,
                   "RetainWhenDie": False}
        b.add_node("SkillTagsConfigNode", tid, payload,
                   desc=f"_旋转扩张_{name}",
                   table_tash=TASH_SKILL_TAGS,
                   table_name_for_config2id="SkillTagsConfig")

    # ===== Helper（沿用 v0.4，省略重复 docstring）=====
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

    # ===== v0.5 关键改造：CREATE_BULLET 引用内置 BulletConfig 死值 ID（不再 EXT_PARAM）=====
    bullet_eid = b.alloc_eid()
    bullet_payload = {
        "ID": bullet_eid, "SkillEffectType": ET["BULLET"],
        "Params": [
            P(BULLET_CONFIG_ID),                    # 0  v0.5：直接死值引用模板内置 BulletConfig
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
               desc="创建第 i 颗子弹（引用模板内置 BulletConfig=32300150）",
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

    # ===== OnTick 工具子图（基本沿用 v0.4，作为 32300101 effect 暴露给 BulletConfig）=====
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
    self_x_init = make_get_self_attr(59, desc="读子弹自身 X (init)")
    self_y_init = make_get_self_attr(60, desc="读子弹自身 Y (init)")
    init_X0 = make_modify_entity_tag(
        TAG_IDS["casterX"], P(self_x_init, PT_FUNC_RET),
        desc="init: X0 = 子弹.X")
    init_Y0 = make_modify_entity_tag(
        TAG_IDS["casterY"], P(self_y_init, PT_FUNC_RET),
        desc="init: Y0 = 子弹.Y")
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
        desc="OnTick 单帧 v0.5：θ+=ω → curRadSpd+=aR/30 → R+=curRadSpd → "
             "followPlayer 分支 → 改 X/Y → 应用位置 → maxR/minR 双条件检查")

    ontick_repeat = make_repeat_each_frame(ontick_frame, desc="OnTick REPEAT (每帧)")

    # OnTick init 根（v0.5：仍为 32300101，但通过字段端口边自动连入 BulletConfig.AfterBornSkillEffectExecuteInfo）
    ontick_init_payload = {
        "ID": ONTICK_INIT_EID, "SkillEffectType": ET["ORDER"],
        "Params": [P(init_R), P(init_theta), P(init_X0), P(init_Y0),
                   P(init_curRadSpd), P(ontick_repeat)]}
    b.add_node(
        "TSET_ORDER_EXECUTE", ONTICK_INIT_EID, ontick_init_payload,
        desc="OnTick init v0.5: 初始化 R0/θ_0/X0/Y0/curRadSpd + 启动每帧 REPEAT\n"
             "通过字段端口边自动接入 BulletConfig.AfterBornSkillEffectExecuteInfo",
        effect_type=ET["ORDER"])

    # ===== 模板根 ORDER (IsTemplate=true) =====
    root_eid = ROOT_TEMPLATE_EID
    root_payload = {
        "ID": root_eid, "SkillEffectType": ET["ORDER"],
        "Params": [P(init_order), P(repeat_eid)]}
    b.add_node(
        "TSET_ORDER_EXECUTE", root_eid, root_payload,
        is_template=True, template_params=TPARAMS,
        desc="旋转扩张子弹圈模板根 v0.5（9 项算法 EXT_PARAM + 内置 BulletConfig）",
        effect_type=ET["ORDER"])

    # ===== v0.5 新增：内置 ModelConfigNode（默认 320149）=====
    model_payload = make_default_model_config_payload(DEFAULT_MODEL_ID)
    b.add_node(
        "ModelConfigNode", DEFAULT_MODEL_ID, model_payload,
        desc="默认子弹模型 320149（普通飞叶）。用户可在面板上修改本节点 ID 换其他子弹模型。\n"
             "通过字段端口边自动连入内置 BulletConfig.Model。",
        table_tash=TASH_MODEL_CONFIG,
        table_name_for_config2id="ModelConfig")

    # ===== v0.5 新增：内置 BulletConfigNode =====
    bullet_cfg_payload = make_default_bullet_config_payload()
    b.add_node(
        "BulletConfigNode", BULLET_CONFIG_ID, bullet_cfg_payload,
        desc="模板内置 BulletConfig 32300150。Model/AfterBorn 由字段端口边接入。\n"
             "用户可在面板上调 LastTime（子弹时长，帧）/ Speed / DieSkillEffectExecuteInfo 等。\n"
             "默认 LastTime=150 帧 = 5 秒（兜底，maxR/minR 通常先触发）。",
        table_tash=TASH_BULLET_CONFIG,
        table_name_for_config2id="BulletConfig")

    # ===== v0.5 新增：字段端口边 =====
    # 1) BulletConfig.Model ← ModelConfigNode (320149)
    b.add_field_port_edge(DEFAULT_MODEL_ID, BULLET_CONFIG_ID, "Model")
    # 2) BulletConfig.AfterBornSkillEffectExecuteInfo.SkillEffectConfigID ← OnTick init (32300101)
    b.add_field_port_edge(ONTICK_INIT_EID, BULLET_CONFIG_ID,
                          "AfterBornSkillEffectExecuteInfo.SkillEffectConfigID")

    return b


def make_sticky_notes() -> list:
    """v0.5 sticky note — 5 段纯逻辑骨架（按 doc/SkillAI/docs/StickyNote_模板.md v3）"""
    overview = (
        "[作用]\n"
        "通用旋转扩张子弹圈算法模板 v0.5（1860216 风格自包含模式）。\n"
        "调用方拖入即用：内置 BulletConfig 已自动接入 OnTick 与 Model，\n"
        "调用方只需在 SkillEditor 面板上调 9 项算法 EXT_PARAM（[阵型]/[运动]/[终止]\n"
        "三组）。子弹 Model/LastTime 等可视字段在面板上直接修改对应内置子节点。\n\n"
        "[流程]\n"
        "1. 主流程 (L1)：拖入模板后，根 ORDER (32300001) 串联：\n"
        "     init_i (i=0) → REPEAT(N 次) → single_order：\n"
        "       i++ → θ_i = (i-1)·360/N → abs_angle = facing + θ_i →\n"
        "       heading = abs_angle + 90 + φ →\n"
        "       spawn_X/Y = caster.X/Y + R0·cos/sin(abs_angle) (Effect 73/74) →\n"
        "       CREATE_BULLET (引用模板内置 BulletConfig=32300150)\n"
        "2. 子弹生成时刻 (L2 init)：内置 BulletConfig 的 AfterBornSkillEffectExecuteInfo\n"
        "     字段端口边自动指向 OnTick init effect (32300101)，子弹一出生立即执行：\n"
        "       trajR=R0, trajTheta=facing-90-φ, X0/Y0=子弹.X/Y, currentRadialSpeed=vR\n"
        "       启动 REPEAT(interval=1, count=-1) 每帧执行 frame 链\n"
        "3. 每帧 (L2 frame)：θ += ω/帧 → curRadSpd += aR/30 → R += curRadSpd →\n"
        "     followPlayer != 0 时刷新 X0/Y0 = caster.X/Y →\n"
        "     newX/Y = X0/Y0 + R·cos/sin(θ)/10000 → 应用到引擎位置 →\n"
        "     R > maxRadius 则 DESTROY；R < minRadius 则 DESTROY\n"
        "4. 子弹长边沿切线（φ=0）或偏移 φ 角朝向；\n"
        "   销毁条件三选一即触发：maxR / minR / BulletConfig.LastTime 到期\n\n"
        "[特殊条件]\n"
        "- followPlayer=1 时圆心每帧跟主角；=0 时固定在 cast 位置\n"
        "- aR<0 配合 vR>0 → 先扩后缩玩法\n"
        "- φ=90° 时子弹长边指向圆心外（刺向外）\n"
        "- 单位约定：1 米 = 100 单位，1 秒 = 30 帧\n"
        "    R0/maxR/minR 单位/项目坐标系\n"
        "    vR 单位/帧（正=外飞，负=内收）\n"
        "    ω 度/帧（正=逆时针，负=顺时针）\n"
        "    aR 单位/秒²（每帧加 aR/30）\n"
        "- TSCT_VALUE_COMPARE 操作符（C# 真值 common.nothotfix.cs L7929）：\n"
        "    1=`==` 2=`!=` 3=`>` 4=`>=` 5=`<` 6=`<=`\n\n"
        "[参数] 9 项算法 EXT_PARAM（按面板分组前缀）\n"
        "[阵型] 子弹数N             默认 8\n"
        "[阵型] 初始半径R0          默认 200 单位 (≈2 米)\n"
        "[阵型] 切线偏移角φ(度)     默认 0 (花瓣绽放)\n"
        "[运动] 径向速度vR(单位/帧) 默认 10/帧 (≈3 米/秒)\n"
        "[运动] 径向加速度aR(单位/秒²) 默认 0 (匀速)\n"
        "[运动] 整团角速度ω(度/帧)  默认 3°/帧 (≈90°/秒, 一秒1/4圈)\n"
        "[运动] followPlayer        默认 1 (跟随主角)\n"
        "[终止] maxRadius           默认 1500 单位 (≈15 米)\n"
        "[终止] minRadius           默认 0 (永不触发)\n\n"
        "子弹外观/生命/特效字段在 SkillEditor 面板上直接调（不走 EXT_PARAM）：\n"
        "  Model：改内置 ModelConfigNode (默认 320149 普通飞叶)\n"
        "  LastTime / Speed / DieSkillEffectExecuteInfo：直接编辑内置 BulletConfigNode\n"
        "  ModelBaseScalePercent / Hp 等：同上\n\n"
        "[联动]\n"
        "- 此模板由内置 BulletConfig + 字段端口边完成所有自动接入，\n"
        "  调用方无需手动接 OnTick effect ID（v0.4 双根反模式已修复）\n"
        "- 调用方在自己的 SkillConfig.SkillDamageTagsList 加伤害 tag\n"
        "  即可给子弹挂伤害（标准做法）\n"
        "- 调用方使用 TSET_RUN_SKILL_EFFECT_TEMPLATE (SET=118) 引用本模板根 32300001\n\n"
        "[v0.5 净改动]\n"
        "1) 移除双根反模式：模板内新增 BulletConfigNode (32300150) + ModelConfigNode (320149)\n"
        "   + 2 条字段端口边（Model 和 AfterBornSkillEffectExecuteInfo.SkillEffectConfigID），\n"
        "   实现 1860216 风格自包含。\n"
        "2) TemplateParams 10 项 → 9 项（删 bulletID — 由内置 BulletConfig 替代）。\n"
        "3) 默认值贴近【花瓣绽放】预设：N=8 / R0=200 / φ=0 / vR=10/帧 / aR=0 / ω=3°/帧\n"
        "   / maxR=1500 / minR=0 / followPlayer=1。\n"
        "4) Desc 按面板分组前缀 [阵型]/[运动]/[终止]（项目里 emoji 没真用过，退化为文字）。\n"
        "5) Desc 中文化 + 单位换算说明。\n\n"
        "[参考真实样本]\n"
        "1860216 链子弹模板：内置 BulletConfig + PackedMembersOutput 字段端口边\n"
        "30212009 千叶散华：BulletConfig.Model 字段端口边 + ModelConfigNode 用法\n"
        "30212010 叶散风行：OnTick 链 rid 1108-1131 结构原型"
    )
    return [{
        "GUID": str(uuid.uuid4()),
        "position": {
            "serializedVersion": "2",
            "x": -180.0, "y": 60.0,
            "width": 800.0, "height": 2400.0,
        },
        "title": "[概览] 旋转扩张子弹圈 通用模板 v0.5 — 1860216 风格自包含",
        "content": overview,
    }]


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    b = build()
    notes = make_sticky_notes()
    b.emit(OUTPUT, sticky_notes=notes)
    print(f"✓ v0.5 模板生成成功 → {OUTPUT}")
    print(f"  节点数: {len(b.refs)}")
    print(f"  自动派生 PackedParamsOutput 边数: {len(b.edges)}")
    print(f"  字段端口边数: {len(b.field_port_edges)}")
    print(f"  总边数: {len(b.edges) + len(b.field_port_edges)}")
    ids = [r["data"]["ID"] for r in b.refs]
    print(f"  ID 范围: {min(ids)} ~ {max(ids)}")
    print(f"  模板根 ID: {ROOT_TEMPLATE_EID}")
    print(f"  内置 BulletConfig ID: {BULLET_CONFIG_ID}")
    print(f"  内置 ModelConfig ID: {DEFAULT_MODEL_ID}")
    print(f"  OnTick init effect ID: {ONTICK_INIT_EID}")


if __name__ == "__main__":
    main()
