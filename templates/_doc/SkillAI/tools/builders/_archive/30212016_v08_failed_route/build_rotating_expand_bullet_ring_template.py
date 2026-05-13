#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旋转扩张子弹圈 — SkillEditor 通用技能模板生成器（v0.4）

需求来源：用户算法需求文档 v1.0 (2026-05-09)
路径：F:\\DreamRivakes2\\ClientPublish\\DreamRivakes2_U3DProj\\doc\\SkillAI\\算法/旋转扩张子弹圈.md（用户原稿）

== v0.4 升级（2026-05-09，接力 a97e82cc61a41701f）==
用户 v0.3 实测反馈：
  1. 有些"线没连"——经红队拓扑分析证明 v0.3 实际 0 个完全孤立节点 + 0 个不可达节点
     + ConfigJson↔edges 完全一致（双根模板设计意图导致 OnTick 子图与 L1 主流程视觉
     不连，跟 #022 同款，并非 bug）。
  2. "改了参数无效"——根因定位：**TSCT_VALUE_COMPARE 操作符 op 编码错配**。v0.3
     沿用 empirical 推断的 op 表（CMP_GT=5/GE=6/LT=3/LE=4），而 C# 真值
     （common.nothotfix.cs L7929 TConditionOperator 枚举）：
        TCO_EQUAL=1 / NOT_EQUAL=2 / BIGGER(>)=3 / BIGGER_OR_EQUAL(>=)=4 /
        SMALLER(<)=5 / SMALLER_OR_EQUAL(<=)=6
     v0.4 修正所有 op 编码 → 跟 C# 枚举对齐。这条是**接力消息任务 B**的真根因。
  3. damagePerHit 删除——子弹的 BulletConfig.hit 链路自己管伤害，模板再单加一层
     EXT_PARAM 是冗余（且需要调用方接 SkillTag 32300714 才生效，更繁琐）。
  4. lifetime 删除——子弹的 BulletConfig.LastTime 自己管生命周期，模板算
     elapsedFrames 强行 DESTROY 是越权。整个 lifetime 销毁机制（OnTick 链
     elapsedFrames++ + ≥lifetime*30 → DESTROY）连同实体级 SkillTag 32300713 全删。

v0.4 净改动：
  - TPARAMS 12 项 → 10 项（删 [8] lifetime + [12] damagePerHit）
  - SkillTag 11 个 → 9 个（删 32300713 elapsedFrames + 32300714 damagePerHitPool）
  - OnTick 链：删 init_damagePool / init_elapsedFrames / add_elapsedFrames /
    get_elapsed_for_check / calc_lifetime_threshold / cond_lifetime / branch_lifetime
  - op 编码：TCO_BIGGER=3 / TCO_BIGGER_OR_EQUAL=4 / TCO_SMALLER=5 / TCO_SMALLER_OR_EQUAL=6
    （v0.3 把 GT/GE 错配成 5/6，把 LT/LE 错配成 3/4 — 全部反向了）
  - 节点数 89 → 70（-19），边数 115 → ~90 预期，10/10 真消费

== v0.3 历史（已废弃）==
v0.3 把 12 项 TemplateParam 中的 ω/vR 真正消费，aR/lifetime/maxRadius/minRadius/
followPlayer/damagePerHit 6 项升级到真消费。op 编码错配 + lifetime/damagePerHit
冗余设计，被 v0.4 修正。

  [6] aR (径向加速度，px/s²)：OnTick 每帧 currentRadialSpeed += aR/30，每帧
      R += currentRadialSpeed（替换 v0.2 的 R += vR 写死）。
      新增实体级 SkillTag currentRadialSpeed（init=vR）。

  [8] maxRadius (最大半径上限)：OnTick 每帧 R 计算后，条件 R > maxRadius → DESTROY。
      v0.3 op=5 (实际是 <) → v0.4 op=3 (>)。

  [9] minRadius (最小半径下限)：OnTick 每帧 R 计算后，条件 R < minRadius → DESTROY。
       默认 0 时永不触发（R 初始 100）。
       v0.3 op=3 (实际是 >) → v0.4 op=5 (<)。

  [10] followPlayer (是否每帧跟随主角，0/1)：OnTick 每帧用 CONDITION_EXECUTE 分两路
       - followPlayer != 0：每帧重读 caster.X/Y（用 PT=COMMON_PARAM 4 = 主体伤害归属
         单位指向 caster），刷新 X0/Y0 实体级 tag
       - followPlayer == 0：保持 v0.2 的"出生时记录 X0/Y0"行为不变
       v0.3 op=2 (!=) — 恰好对，v0.4 不变。

== v0.2 已实现（保留）==
v0.1 报告判定"OnTick 重算 R(t)/θ(t) 在 SkillEditor 不可低成本实现"——**经反编译 30212010
（叶散风行）证实判断错误**。项目内现成机制：
    REPEAT(interval=1, count=-1, interrupt=单位不存在) →
        每帧 ADD_TAG R+=vR、ADD_TAG θ+=ω →
        MATH_COS/SIN(θ) → CALC X = X0 + R·cos(θ)/10000 (项目用 *10000 整数定点) →
        MODIFY_ENTITY_ATTR (slot 59=X, 60=Y) → CHANGE_ENTITY_POSITION → 改面向 (slot 91)
v0.2 把这条 OnTick 链**内嵌**进模板，子弹生成后立即启动；ω/vR 两项 TemplateParam 真正消费。

== 核心算法 ==
以 caster 为圆心，N 颗子弹按 2π/N 均匀分布在初始半径 R0 圆周上。
每颗子弹生成时刻位置：
    θ_i_0 = 2π·i/N（i ∈ [0, N-1]）
    abs_angle_i = caster.facing + θ_i_0_degrees
    spawn_X_i = caster.X + R0 · cos(abs_angle_i)
    spawn_Y_i = caster.Y + R0 · sin(abs_angle_i)
    heading_i = abs_angle_i + 90 + φ
        - φ=0：长边沿切线（默认花瓣）
        - φ=90：长边沿径向（"刺向外"）

子弹存活期间每帧：
    θ_i(t+1) = θ_i(t) + ω_per_frame
    R(t+1)   = R(t) + vR_per_frame
    X = caster.X + R(t)·cos(θ_i(t))/10000
    Y = caster.Y + R(t)·sin(θ_i(t))/10000
    ChangeEntityPosition(子弹, X, Y)
    子弹面向 = atan2(子弹.Y - caster.Y, 子弹.X - caster.X) + 90

== SkillEditor 框架适配（v0.4 全部 10 项真消费）==
- 原算法 §3.3-3.5 OnTick 重算：✓ 实现（参考 30212010 rid 1108-1131）
- 整团绕主角旋转 ω：✓ 真正消费（每帧 ADD_TAG）
- 径向运动 vR：✓ 真正消费（v0.3 改为初始化 currentRadialSpeed = vR）
- 中断条件：单位不存在 / 子弹自然销毁（BulletConfig.LastTime）/ maxRadius / minRadius
  ⚠️ lifetime 销毁机制 v0.4 删除：交给 BulletConfig.LastTime 自己管，模板不越权。
- aR：✓ v0.3 实现（每帧 currentRadialSpeed += aR/30，再每帧 R += currentRadialSpeed）
- maxRadius/minRadius：✓ v0.3 实现（每帧条件分支 + DESTROY_ENTITY）— v0.4 修正 op 编码
- followPlayer：✓ v0.3 实现（每帧 CONDITION_EXECUTE 选择"重读 caster.X/Y"或"用初始 X0/Y0"）
- damagePerHit：v0.4 删除（伤害由 BulletConfig.AfterBornSkillEffectExecuteInfo 链路自己管）
- pierceCount：BulletConfig 内配置（不在模板域内，无变化）

== 实现策略 ==
1. 用 Effect 73/74「角度距离计算位置 X/Y」直接出 caster + R0·cos/sin(θ) 坐标
   - 比手动 SIN(50)/COS(51)+×10000 干净
   - 真实样本验证：SkillGraph_28004657_【模板】兽潮刷怪逻辑.json
2. 模板根 ORDER (IsTemplate=true) → init_order(i=0) + REPEAT(N) → single_order(i++ + spawn)

== TemplateParams 10 项（v0.4 全部真消费）==
[1]  bulletID         BulletConfig                            (调用方拉子弹)
[2]  bulletCount N    int     8       ✓ 主流程使用
[3]  initialRadius R0 int     100     ✓ 主流程 + OnTick init
[4]  tangentOffsetAngle φ(度)  0      ✓ 主流程 + OnTick init θ_0 反推
[5]  radialVelocity vR(每帧)   10     ✓ OnTick init currentRadialSpeed=vR
[6]  radialAcceleration aR(每秒) 0    ✓ OnTick currentRadialSpeed += aR/30
[7]  angularVelocity ω(°/帧)   15     ✓ OnTick θ += ω
[8]  maxRadius                 1500   ✓ R > maxRadius → DESTROY (v0.4 op=3 修正)
[9]  minRadius                 0      ✓ R < minRadius → DESTROY (v0.4 op=5 修正；默认 0 永不触发)
[10] followPlayer 0/1          0      ✓ 1=每帧重读 caster.X/Y / 0=固定 X0/Y0 (op=2 != 不变)
默认值用算法文档预设组"花瓣绽放"。

== ID 段位 ==
模板根 EID = 32300001（固定，PostMortem #010）
SkillEffectConfig 段：32300002 起
SkillTagsConfig 段：32300700 起（i 工作变量）
（已扫描全工程：32300000~32310000 段连续 1 万 ID 全空）

== 参考样本 ==
- 扇形分层弹幕模板：build_fan_layered_template.py（拓扑骨架来源）
- 兽潮刷怪逻辑模板（28004657）：Effect 73/74 用法参考
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJ = Path(r"<<PROJECT_ROOT_WIN>>")
OUTPUT = PROJ / "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】旋转扩张子弹圈.json"

# ===== ID 段位 =====
ROOT_TEMPLATE_EID = 32300001  # 模板根 EID（固定，避免编辑器 template2Nodes 缓存累积）
EFFECT_BASE = 32300002        # SkillEffectConfig 起始
COND_BASE   = 32300500        # SkillConditionConfig 起始（本模板暂未使用）
TAG_BASE    = 32300700        # SkillTagsConfig 起始

TAG_IDS = {
    # 技能级（caster 身上）— 主流程使用
    "i":            TAG_BASE + 0,   # 当前子弹索引 (1..N)
    "curTheta":     TAG_BASE + 1,   # 当前 θ_i (度) = i * 360 / N
    "curAbsAngle":  TAG_BASE + 2,   # 当前 abs_angle = facing + θ_i
    "curHeading":   TAG_BASE + 3,   # 子弹长边朝向 = abs_angle + 90 + φ
    "casterX":      TAG_BASE + 4,   # caster.X 初始（每帧子弹用作圆心）— 实体级容器在 OnTick 链中
    "casterY":      TAG_BASE + 5,   # caster.Y 初始
    # 实体级（子弹身上）— OnTick 轨迹链使用
    # （配置同样是 SkillTagsConfigNode 节点，PT=COMMON_PARAM 41 ORIGIN_SKILL_INST_ID
    #  使其挂在 effect 实例容器 = 子弹 上 — PostMortem #019 命中）
    "trajR":             TAG_BASE + 10,  # 当前半径 R(t) 实体级
    "trajTheta":         TAG_BASE + 11,  # 当前 θ(t) 实体级
    # v0.3 新增 1 项实体级 tag（aR 真消费需要）— v0.4 删 elapsedFrames + damagePerHitPool
    "currentRadialSpeed": TAG_BASE + 12, # 当前径向速度（每帧）— init=vR，每帧 += aR/30
    # v0.4 删除：
    #   "elapsedFrames":  TAG_BASE + 13 (lifetime 销毁机制)
    #   "damagePerHitPool": TAG_BASE + 14 (damagePerHit 中转池)
}

# ===== TableTash =====
TASH_SKILL_EFFECT    = "0CFA05568A66FEA1DF3BA6FE40DB7080"
TASH_SKILL_TAGS      = "6A8A6883BDFDA1411BB2461E65CB2D9B"
TASH_SKILL_CONDITION = "ED89F46EAB95F7ACF5C1911A5A375278"

# ===== TSkillEffectType =====
ET = {
    "ORDER":          1,
    "DELAY":          2,
    "REPEAT":         3,
    "BULLET":         8,
    "GET_FIXTURE_CENTER_Z": 367,
    "ANGLE_DIST_X":  73,    # 角度距离计算位置 X
    "ANGLE_DIST_Y":  74,    # 角度距离计算位置 Y
    "CALC":          31,
    "GET_ATTR":      32,
    "MODIFY_TAG":    46,
    "GET_TAG":       48,
    # v0.2 OnTick 轨迹链新增（参考 30212010 rid 1108-1131）
    "MODIFY_ATTR":   12,   # TSET_MODIFY_ENTITY_ATTR_VALUE
    "CHANGE_POS":    22,   # TSET_CHANGE_ENTITY_POSITION
    "MATH_SIN":      50,
    "MATH_COS":      51,
    "ANGLE_BETWEEN": 59,   # TSET_GET_ANGLE_BETWEEN_POINT
    "ADD_TAG":       97,   # TSET_ADD_SKILL_TAG_VALUE
    # v0.3 条件执行 + 销毁实体（参考 30212010 rid 1010/1019/1031/1035）
    "CONDITION_EXECUTE": 47,  # TSET_CONDITION_EXECUTE
    "DESTROY_ENTITY":    24,  # TSET_DESTROY_ENTITY
}

# ===== TSkillConditionType =====
CT = {
    "AND":           1,
    "VALUE_COMPARE": 7,   # TSCT_VALUE_COMPARE
}

# ===== VALUE_COMPARE 操作符 — 来自 C# 真值（v0.4 修正 PostMortem #022 后的二次复盘）==
# 权威来源：Assets/Scripts/TableDR_CS/NotHotfix/Gen/common.nothotfix.cs L7929
#   public enum TConditionOperator
#       TCO_NULL              = 0   "-"
#       TCO_EQUAL             = 1   "=="
#       TCO_NOT_EQUAL         = 2   "!="
#       TCO_BIGGER            = 3   ">"
#       TCO_BIGGER_OR_EQUAL   = 4   ">="
#       TCO_SMALLER           = 5   "<"
#       TCO_SMALLER_OR_EQUAL  = 6   "<="
#       TCO_OR/AND/NOT/CLOSED_INTERVAL/INCLUDE/HAS_FLAG = 7..12
#
# v0.3 错配（empirically 推断）：CMP_LT=3/LE=4/GT=5/GE=6 — 实际把 < 跟 > 搞反、
# <= 跟 >= 搞反。30212010 line 8106 用 op=2 NEQ 是对的；其他 GT/LT 推断都错了。
# v0.4 修正后跟 C# 完全对齐。
CMP_EQ, CMP_NEQ, CMP_GT, CMP_GE, CMP_LT, CMP_LE = 1, 2, 3, 4, 5, 6

# 数值运算符 TNumOperators
OP_ADD, OP_MINUS, OP_MULTI, OP_DIV = 3, 4, 5, 6

# ParamType
PT_NULL, PT_ATTR, PT_FUNC_RET, PT_SKILL_PARAM, PT_EXTRA_PARAM, PT_COMMON_PARAM = 0, 1, 2, 3, 4, 5


# ===== Builder =====
class TplBuilder:
    def __init__(self):
        self.refs = []
        self.edges = []
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

    def emit(self, output_path: Path, sticky_notes: list = None):
        # 自动建边（沿用扇形分层弹幕模板的逻辑）
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
                # PT=1(Attr)/4(ExtraParam)/5(CommonParam)/6(EventParam) 的 Value 不是 ConfigID，跳过
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


# 模板参数索引 (1-based, PT=4 EXTRA_PARAM) — v0.4 删 lifetime + damagePerHit 后剩 10 项
EXT_BULLET_ID    = 1
EXT_N            = 2
EXT_R0           = 3
EXT_PHI          = 4
EXT_VR           = 5
EXT_AR           = 6
EXT_OMEGA        = 7
EXT_MAX_R        = 8   # v0.3 是 9 → v0.4 上移 1
EXT_MIN_R        = 9   # v0.3 是 10 → v0.4 上移 1
EXT_FOLLOW       = 10  # v0.3 是 11 → v0.4 上移 1
# v0.4 已删除：
#   EXT_LIFETIME = 8 (v0.3) — 子弹生命由 BulletConfig.LastTime 自管
#   EXT_DAMAGE   = 12 (v0.3) — 伤害由 BulletConfig.AfterBornSkillEffectExecuteInfo 链路自管

# 默认值用算法文档第 9 章预设组"花瓣绽放"
TPARAMS = [
    # [1] 子弹ID（BulletConfig 引用，无默认 JSON — 由调用方在面板拉子弹）
    {"DefaultValueDesc": "", "Name": "子弹ID", "RefTypeName": "BulletConfig",
     "RefPortTypeNames": "", "DefalutParam": {}, "DefalutParamJson": "",
     "isConfigId": True, "isEnum": False,
     "RefTableFullName": "TableDR.BulletConfig",
     "RefTableManagerName": "TableDR.BulletConfigManager",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [2] 子弹数N
    {"DefaultValueDesc": "", "Name": "子弹数N", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":8,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [3] 初始半径R0
    {"DefaultValueDesc": "", "Name": "初始半径R0", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":100,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [4] 切线偏移角φ（度）
    {"DefaultValueDesc": "", "Name": "切线偏移角φ(度)", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [5] 径向速度vR（每帧）— v0.2/v0.3 已消费（init currentRadialSpeed = vR）
    {"DefaultValueDesc": "", "Name": "径向速度vR(每帧)", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":10,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [6] 径向加速度aR（每秒，px/s²）— v0.3 已消费（每帧 currentRadialSpeed += aR/30）
    {"DefaultValueDesc": "", "Name": "径向加速度aR(每秒)", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [7] 整团角速度ω（度每帧）— v0.2 已消费（同 30212010 默认值）
    {"DefaultValueDesc": "", "Name": "整团角速度ω(度每帧)", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":15,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [8] 最大半径maxRadius — v0.3 已消费（R > maxRadius → DESTROY）— v0.4 op=3 修正
    {"DefaultValueDesc": "", "Name": "maxRadius", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":1500,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [9] 最小半径minRadius — v0.3 已消费（R < minRadius → DESTROY）— v0.4 op=5 修正；默认 0 永不触发
    {"DefaultValueDesc": "", "Name": "minRadius", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # [10] followPlayer（0=圆心固定/1=每帧跟随）— v0.3 已消费（op=2 != 不变）
    {"DefaultValueDesc": "", "Name": "followPlayer(0或1)", "RefTypeName": "",
     "RefPortTypeNames": "", "DefalutParam": {},
     "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
     "isConfigId": False, "isEnum": False,
     "RefTableFullName": "", "RefTableManagerName": "",
     "RefPortTypeName": "", "RefPortTypeFullName": "", "IsFunctionReturn": False},
    # v0.4 已删除：
    #   [8 v0.3] lifetime — BulletConfig.LastTime 自管
    #   [12 v0.3] damagePerHit — BulletConfig 命中链路自管
]


def build():
    b = TplBuilder()

    # ----- SkillTagsConfigNode 集合 -----
    for name, tid in TAG_IDS.items():
        payload = {"ID": tid, "TagType": 0, "Desc": f"_旋转扩张_{name}",
                   "NameKey": 0, "DefaultValue": 0, "FinalValueEffectID": 0,
                   "RetainWhenDie": False}
        b.add_node("SkillTagsConfigNode", tid, payload,
                   desc=f"_旋转扩张_{name}",
                   table_tash=TASH_SKILL_TAGS,
                   table_name_for_config2id="SkillTagsConfig")

    # ===== 通用 helper =====
    def make_modify_tag(tag_id: int, value_param: dict, desc=""):
        """技能级 SkillTag 写入（caster 身上，TPT_COMMON_SKILL_PARAM=7）"""
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

    # ===== v0.2 实体级 SkillTag helpers（参考 30212010 rid 1114-1115）=====
    # 实体容器 = TCPT_ORIGIN_SKILL_INST_ID (41) — 让 tag 挂在子弹身上
    # 主体引用 = TCPT_MAIN_ENTITY (1) — "我=子弹自己"（在 OnTick 链里 caster 视角=子弹）
    def make_modify_entity_tag(tag_id: int, value_param: dict, desc=""):
        """实体级 SkillTag 写入（OnTick 子弹身上）"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["MODIFY_TAG"],
                   "Params": [
                       P(1, PT_COMMON_PARAM),    # 主体单位
                       P(41, PT_COMMON_PARAM),   # ORIGIN_SKILL_INST_ID = 实体级容器
                       P(tag_id), value_param, P(1),
                   ]}
        b.add_node("TSET_MODIFY_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["MODIFY_TAG"])
        return eid

    def make_get_entity_tag(tag_id: int, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_TAG"],
                   "Params": [
                       P(1, PT_COMMON_PARAM),
                       P(41, PT_COMMON_PARAM),
                       P(tag_id), P(1), P(0),
                   ]}
        b.add_node("TSET_GET_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_TAG"])
        return eid

    def make_add_entity_tag(tag_id: int, delta_param: dict, desc=""):
        """实体级 SkillTag 增量（参考 30212010 rid 1128/1129）"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["ADD_TAG"],
                   "Params": [
                       P(1, PT_COMMON_PARAM),
                       P(41, PT_COMMON_PARAM),
                       P(tag_id), delta_param, P(1),
                   ]}
        b.add_node("TSET_ADD_SKILL_TAG_VALUE", eid, payload,
                   desc=desc, effect_type=ET["ADD_TAG"])
        return eid

    def make_get_attr(attr_id: int, desc=""):
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_ATTR"],
                   "Params": [P(75, PT_ATTR), P(attr_id)]}
        b.add_node("TSET_GET_ENTITY_ATTR_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_ATTR"])
        return eid

    def make_get_self_attr(attr_id: int, desc=""):
        """读子弹自身实体属性（参考 30212010 rid 1112 改面向、1119/1120 改 X/Y）
        差异：30212010 用 P[0]=1, PT=5 (主体单位=子弹) — 在 OnTick 上下文里
        '主体' 视角是子弹自己。这里直接复用模式。"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["GET_ATTR"],
                   "Params": [P(1, PT_COMMON_PARAM), P(attr_id)]}
        b.add_node("TSET_GET_ENTITY_ATTR_VALUE", eid, payload,
                   desc=desc, effect_type=ET["GET_ATTR"])
        return eid

    def make_modify_entity_attr(attr_id: int, value_param: dict, desc=""):
        """改子弹实体属性（参考 30212010 rid 1119/1120/1112）
        Params=[主体, attr_id, value]"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["MODIFY_ATTR"],
                   "Params": [P(1, PT_COMMON_PARAM), P(attr_id), value_param]}
        b.add_node("TSET_MODIFY_ENTITY_ATTR_VALUE", eid, payload,
                   desc=desc, effect_type=ET["MODIFY_ATTR"])
        return eid

    def make_change_entity_position(x_param, y_param, z_param=None, desc=""):
        """ChangeEntityPosition 应用 X/Y 写入到引擎位置（参考 30212010 rid 1125）
        Params=[主体, X_eid, Y_eid, 位置类型=2(自定义?), Z]"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["CHANGE_POS"],
                   "Params": [P(1, PT_COMMON_PARAM), x_param, y_param,
                              P(2),  # 位置类型 = 2（用 30212010 同款）
                              z_param or P(0)]}
        b.add_node("TSET_CHANGE_ENTITY_POSITION", eid, payload,
                   desc=desc, effect_type=ET["CHANGE_POS"])
        return eid

    def make_math_cos(angle_param, desc=""):
        """COS(angle_degrees) — 项目内输出 *10000 整数定点"""
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

    def make_repeat_each_frame(child_id: int, desc=""):
        """每帧重复（interval=1, count=-1 无限）— 中断由子弹自然销毁实现
        参考 30212010 rid 1108：[interval=1, count=-1, immediateRun=0,
                                  childID=child_id, ?, interruptID=0(默认), ...]
        v0.2 简化：不用外部 SkillInterruptConfig，依赖子弹 BulletConfig.LastTime
        过期或被打死时引擎自动停 effect。"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["REPEAT"],
                   "Params": [
                       P(1),                # 0  间隔=1帧
                       P(-1),               # 1  无限次
                       P(0),                # 2  立即执行=0
                       P(child_id),         # 3  child
                       P(0), P(0), P(0),    # 4-6
                       P(0), P(0),          # 7-8
                       P(1),                # 9  急速?
                   ]}
        b.add_node("TSET_REPEAT_EXECUTE", eid, payload,
                   desc=desc, effect_type=ET["REPEAT"])
        return eid

    def make_angle_dist_x(center_x_param, center_y_param, angle_param, dist_param, desc=""):
        """Effect 73: 角度距离计算位置 X = center_x + dist · cos(angle_degrees)"""
        eid = b.alloc_eid()
        # 参考样本 28004657：Params=[center_x, center_y, angle, dist, height_z]
        payload = {"ID": eid, "SkillEffectType": ET["ANGLE_DIST_X"],
                   "Params": [center_x_param, center_y_param, angle_param, dist_param, P(0)]}
        b.add_node("TSET_GET_POS_X_BY_ANGLE_DISTANCE", eid, payload,
                   desc=desc, effect_type=ET["ANGLE_DIST_X"])
        return eid

    def make_angle_dist_y(center_x_param, center_y_param, angle_param, dist_param, desc=""):
        """Effect 74: 角度距离计算位置 Y = center_y + dist · sin(angle_degrees)"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["ANGLE_DIST_Y"],
                   "Params": [center_x_param, center_y_param, angle_param, dist_param, P(0)]}
        b.add_node("TSET_GET_POS_Y_BY_ANGLE_DISTANCE", eid, payload,
                   desc=desc, effect_type=ET["ANGLE_DIST_Y"])
        return eid

    # ===== v0.3 新增 helpers — 条件分支 / 销毁实体 =====
    def make_value_compare(left_param, op: int, right_param, desc=""):
        """TSCT_VALUE_COMPARE — left op right。
        op 取自 CMP_EQ/NEQ/LT/LE/GT/GE（empirically 推断，参考文件头注释）。
        参考真实样本 30212010 ID=320287 / 320296。
        ⚠️ TableTash 必须用 SkillConditionConfig，PostMortem #010。"""
        cid = b.alloc_cid()
        payload = {"ID": cid, "SkillConditionType": CT["VALUE_COMPARE"],
                   "Params": [left_param, P(op), right_param]}
        b.add_node("TSCT_VALUE_COMPARE", cid, payload,
                   desc=desc, condition_type=CT["VALUE_COMPARE"],
                   table_tash=TASH_SKILL_CONDITION,
                   table_name_for_config2id="SkillConditionConfig")
        return cid

    def make_condition_execute(cond_id: int, then_eid: int, desc=""):
        """TSET_CONDITION_EXECUTE — 条件成立则执行 then_eid。
        参考 30212010 rid 1010/1011 真实样本。"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["CONDITION_EXECUTE"],
                   "Params": [P(cond_id), P(then_eid), P(0)]}
        b.add_node("TSET_CONDITION_EXECUTE", eid, payload,
                   desc=desc, effect_type=ET["CONDITION_EXECUTE"])
        return eid

    def make_destroy_entity(desc=""):
        """TSET_DESTROY_ENTITY — 销毁主体单位（在 OnTick 链中即销毁子弹自身）。
        参考 30212010 rid 1031/1035 真实样本。"""
        eid = b.alloc_eid()
        payload = {"ID": eid, "SkillEffectType": ET["DESTROY_ENTITY"],
                   "Params": [P(75, PT_ATTR), P(1), P(0)]}
        b.add_node("TSET_DESTROY_ENTITY", eid, payload,
                   desc=desc, effect_type=ET["DESTROY_ENTITY"])
        return eid

    # ===== 初始化：i = 0 =====
    init_i = make_modify_tag(TAG_IDS["i"], P(0), desc="初始化 i=0")
    init_order = make_order([init_i], desc="预初始化 (i=0)")

    # ===== 单发循环内 — i = i + 1 =====
    get_i_for_inc = make_get_tag(TAG_IDS["i"], desc="读 i (准备 i++)")
    calc_inc_i = make_calc(
        [P(get_i_for_inc, PT_FUNC_RET), P(OP_ADD), P(1)],
        desc="i + 1",
    )
    inc_i = make_modify_tag(TAG_IDS["i"], P(calc_inc_i, PT_FUNC_RET), desc="i = i + 1")

    # ===== 算 θ_i = (i - 1) · 360 / N =====
    # 注：i 从 1 开始（先 +1），所以用 i-1 让第一颗在 0°
    get_i_for_theta = make_get_tag(TAG_IDS["i"], desc="读 i (算 θ)")
    calc_theta = make_calc(
        [P(get_i_for_theta, PT_FUNC_RET), P(OP_MINUS), P(1),
         P(OP_MULTI), P(360),
         P(OP_DIV), P(EXT_N, PT_EXTRA_PARAM)],
        desc="θ_i = (i-1) * 360 / N",
    )
    set_theta = make_modify_tag(TAG_IDS["curTheta"], P(calc_theta, PT_FUNC_RET),
                                  desc="curTheta = (i-1)·360/N")

    # ===== 算 abs_angle = caster.facing + θ_i =====
    facing_eid = make_get_attr(91, desc="caster.facing (角度，度)")
    get_theta_for_abs = make_get_tag(TAG_IDS["curTheta"], desc="读 curTheta")
    calc_abs_angle = make_calc(
        [P(facing_eid, PT_FUNC_RET), P(OP_ADD), P(get_theta_for_abs, PT_FUNC_RET)],
        desc="abs_angle = facing + θ_i",
    )
    set_abs_angle = make_modify_tag(TAG_IDS["curAbsAngle"], P(calc_abs_angle, PT_FUNC_RET),
                                      desc="curAbsAngle")

    # ===== 算 heading = abs_angle + 90 + φ（长边沿切线 + 偏移） =====
    get_abs_for_heading = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle (heading)")
    calc_heading = make_calc(
        [P(get_abs_for_heading, PT_FUNC_RET), P(OP_ADD), P(90),
         P(OP_ADD), P(EXT_PHI, PT_EXTRA_PARAM)],
        desc="heading = abs_angle + 90 + φ",
    )
    set_heading = make_modify_tag(TAG_IDS["curHeading"], P(calc_heading, PT_FUNC_RET),
                                    desc="curHeading = abs+90+φ")

    # ===== 算 spawn_X / spawn_Y（用 Effect 73/74）=====
    caster_x = make_get_attr(59, desc="caster.X")
    caster_y_for_x = make_get_attr(60, desc="caster.Y (备用-X计算)")
    get_abs_for_x = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle (spawn_X)")
    spawn_x_eid = make_angle_dist_x(
        P(caster_x, PT_FUNC_RET),
        P(caster_y_for_x, PT_FUNC_RET),
        P(get_abs_for_x, PT_FUNC_RET),
        P(EXT_R0, PT_EXTRA_PARAM),
        desc="spawn_X = caster.X + R0·cos(abs_angle)",
    )

    caster_x_for_y = make_get_attr(59, desc="caster.X (备用-Y计算)")
    caster_y = make_get_attr(60, desc="caster.Y")
    get_abs_for_y = make_get_tag(TAG_IDS["curAbsAngle"], desc="读 curAbsAngle (spawn_Y)")
    spawn_y_eid = make_angle_dist_y(
        P(caster_x_for_y, PT_FUNC_RET),
        P(caster_y, PT_FUNC_RET),
        P(get_abs_for_y, PT_FUNC_RET),
        P(EXT_R0, PT_EXTRA_PARAM),
        desc="spawn_Y = caster.Y + R0·sin(abs_angle)",
    )

    # ===== 出手点高度 Z（参考扇形分层弹幕模板）=====
    bullet_height_eid = b.alloc_eid()
    bullet_height_payload = {
        "ID": bullet_height_eid, "SkillEffectType": ET["GET_FIXTURE_CENTER_Z"],
        "Params": [P(75, PT_ATTR), P(1)],
    }
    b.add_node("TSET_GET_FIXTURE_CENTER_Z", bullet_height_eid, bullet_height_payload,
               desc="出手点假高度 Z (caster 胶囊中点)",
               effect_type=ET["GET_FIXTURE_CENTER_Z"])

    # ===== CREATE_BULLET =====
    get_heading_for_bullet = make_get_tag(TAG_IDS["curHeading"], desc="读 curHeading (子弹朝向)")

    bullet_eid = b.alloc_eid()
    bullet_payload = {
        "ID": bullet_eid, "SkillEffectType": ET["BULLET"],
        "Params": [
            P(EXT_BULLET_ID, PT_EXTRA_PARAM),       # 0  子弹ID
            P(get_heading_for_bullet, PT_FUNC_RET), # 1  朝向 (heading = 切线 + φ)
            P(spawn_x_eid, PT_FUNC_RET),            # 2  spawn_X
            P(spawn_y_eid, PT_FUNC_RET),            # 3  spawn_Y
            P(1, PT_COMMON_PARAM),                  # 4  位置类型 = 自定义
            P(0), P(0),                             # 5,6  X/Y 偏移
            P(0), P(0), P(0),                       # 7,8,9
            P(41, PT_COMMON_PARAM),                 # 10 角度类型
            P(0),                                   # 11
            P(bullet_height_eid, PT_FUNC_RET),      # 12 Z
            P(0), P(1),                             # 13,14
        ],
    }
    b.add_node("TSET_CREATE_BULLET", bullet_eid, bullet_payload,
               desc="创建第 i 颗子弹", effect_type=ET["BULLET"])

    # ===== single_order =====
    single_order = make_order(
        [inc_i, set_theta, set_abs_angle, set_heading, bullet_eid],
        desc="单发流程: i++ → θ → abs_angle → heading → spawn",
    )

    # ===== REPEAT_EXECUTE：重复 N 次 =====
    repeat_eid = b.alloc_eid()
    repeat_payload = {
        "ID": repeat_eid, "SkillEffectType": ET["REPEAT"],
        "Params": [
            P(0),                                  # 0  间隔帧 = 0（同帧发射）
            P(EXT_N, PT_EXTRA_PARAM),              # 1  次数 = N
            P(1),                                  # 2  立即执行
            P(single_order),                       # 3  子效果
            P(0), P(0), P(0), P(0), P(0),
            P(1),                                  # 9  急速
        ],
    }
    b.add_node("TSET_REPEAT_EXECUTE", repeat_eid, repeat_payload,
               desc="重复 N 次（每次发一颗）",
               effect_type=ET["REPEAT"])

    # ===== v0.3 OnTick 工具子图（模拟轨迹 + 6 项真消费）=====
    # 这是独立子图，根节点 ID = ONTICK_INIT_EID (32300101)，**不连入主流程 root**。
    # 调用方拷贝一份 BulletConfig，把 AfterBornSkillEffectExecuteInfo.SkillEffectConfigID
    # 改为 ONTICK_INIT_EID（在面板上手动操作）。模板提供完整轨迹 + 终止条件实现。
    #
    # v0.3 OnTick 链结构（参考 30212010 rid 1108-1131 + 1010/1011 条件分支）：
    #   ONTICK_INIT (root, ID=32300101) [ORDER]
    #     ├─ MODIFY_ENTITY_TAG trajR = R0
    #     ├─ MODIFY_ENTITY_TAG trajTheta = facing - 90 - φ
    #     ├─ MODIFY_ENTITY_TAG X0 = 子弹.X (初始)
    #     ├─ MODIFY_ENTITY_TAG Y0 = 子弹.Y (初始)
    #     ├─ MODIFY_ENTITY_TAG currentRadialSpeed = vR  ← v0.3
    #     ├─ MODIFY_ENTITY_TAG elapsedFrames = 0       ← v0.3
    #     ├─ MODIFY_ENTITY_TAG damagePerHitPool = damagePerHit  ← v0.3 (调用方读)
    #     └─ REPEAT (interval=1, count=-1) → ONTICK_FRAME [ORDER]
    #          ├─ ADD_ENTITY_TAG  trajTheta += ω/帧
    #          ├─ ADD_ENTITY_TAG  currentRadialSpeed += aR/30  ← v0.3
    #          ├─ ADD_ENTITY_TAG  trajR += currentRadialSpeed  ← v0.3 (替换 v0.2 R+=vR)
    #          ├─ ADD_ENTITY_TAG  elapsedFrames += 1            ← v0.3
    #          ├─ CONDITION_EXECUTE (followPlayer != 0) → 每帧重写 X0/Y0 = caster.X/Y  ← v0.3
    #          ├─ COS(trajTheta) / SIN(trajTheta) → calc newX, newY
    #          ├─ MODIFY_ENTITY_ATTR 子弹.X/Y + CHANGE_POSITION（v0.2 不变）
    #          ├─ CONDITION_EXECUTE (elapsedFrames >= lifetime*30) → DESTROY  ← v0.3
    #          ├─ CONDITION_EXECUTE (R > maxRadius)                → DESTROY  ← v0.3
    #          └─ CONDITION_EXECUTE (R < minRadius)                → DESTROY  ← v0.3
    #
    # 注：
    #  - ω/vR 单位是"每帧"。aR 单位是"每秒"（项目惯例，由用户调）；除以 30 即每帧增量。
    #  - 销毁条件三选一即触发；DESTROY_ENTITY 节点共享同一个 effect ID（节点复用）。
    #  - followPlayer 真值检查用 != 0，即任何非零都视为开启（用户填 1 是常见，但 5/100 也能开）。

    # ===== Init 阶段（主体=子弹）=====
    init_R = make_modify_entity_tag(
        TAG_IDS["trajR"], P(EXT_R0, PT_EXTRA_PARAM),
        desc="init: trajR = R0（实体级，挂子弹）"
    )
    self_facing_for_init = make_get_self_attr(91, desc="读子弹自身 facing (init)")
    calc_init_theta = make_calc(
        [P(self_facing_for_init, PT_FUNC_RET), P(OP_MINUS), P(90),
         P(OP_MINUS), P(EXT_PHI, PT_EXTRA_PARAM)],
        desc="init: θ_0 = facing - 90 - φ（反推 abs_angle）"
    )
    init_theta = make_modify_entity_tag(
        TAG_IDS["trajTheta"], P(calc_init_theta, PT_FUNC_RET),
        desc="init: trajTheta = θ_0"
    )
    self_x_init = make_get_self_attr(59, desc="读子弹自身 X (init)")
    self_y_init = make_get_self_attr(60, desc="读子弹自身 Y (init)")
    init_X0 = make_modify_entity_tag(
        TAG_IDS["casterX"], P(self_x_init, PT_FUNC_RET),
        desc="init: X0 = 子弹.X (实体级)"
    )
    init_Y0 = make_modify_entity_tag(
        TAG_IDS["casterY"], P(self_y_init, PT_FUNC_RET),
        desc="init: Y0 = 子弹.Y (实体级)"
    )
    # v0.3 新增 init 项 — v0.4 删 init_elapsedFrames + init_damagePool
    init_curRadSpd = make_modify_entity_tag(
        TAG_IDS["currentRadialSpeed"], P(EXT_VR, PT_EXTRA_PARAM),
        desc="init: currentRadialSpeed = vR (v0.3)"
    )
    # v0.4 删除：
    #   init_elapsedFrames — lifetime 销毁机制不再使用
    #   init_damagePool    — damagePerHit 不再走模板中转

    # ===== OnTick 单帧链（主体=子弹）=====
    # (1) θ += ω/帧（v0.2 不变）
    add_theta = make_add_entity_tag(
        TAG_IDS["trajTheta"], P(EXT_OMEGA, PT_EXTRA_PARAM),
        desc="frame: θ += ω/帧"
    )
    # (2) v0.3 — currentRadialSpeed += aR/30
    # 但 ADD_TAG 直接增量必须是单一 Param —— aR 是 EXT_PARAM，需要先 CALC = aR/30 再 ADD
    calc_aR_per_frame = make_calc(
        [P(EXT_AR, PT_EXTRA_PARAM), P(OP_DIV), P(30)],
        desc="frame: aR/30 (每帧加速度增量)"
    )
    add_curRadSpd = make_add_entity_tag(
        TAG_IDS["currentRadialSpeed"], P(calc_aR_per_frame, PT_FUNC_RET),
        desc="frame: currentRadialSpeed += aR/30 (v0.3)"
    )
    # (3) v0.3 — R += currentRadialSpeed (替换 v0.2 R += vR)
    get_curRadSpd_for_R = make_get_entity_tag(
        TAG_IDS["currentRadialSpeed"], desc="frame: 读 currentRadialSpeed"
    )
    add_R = make_add_entity_tag(
        TAG_IDS["trajR"], P(get_curRadSpd_for_R, PT_FUNC_RET),
        desc="frame: R += currentRadialSpeed (v0.3, 替换 v0.2 vR 写死)"
    )
    # (4) v0.4 删除：v0.3 的 elapsedFrames += 1（lifetime 销毁机制全删）

    # (5) v0.3 followPlayer 分支：每帧重写 X0/Y0 = caster.X/Y
    # 在 OnTick 链里"主体=子弹"，要读 caster 用 PT_COMMON_PARAM=4（主体单位-伤害归属单位 → caster）
    # 注意 GET_ATTR 已有 helper make_get_attr 用 PT=ATTR slot=75 对应"伤害归属单位的属性"
    # 这里 make_get_attr(59) 读的是 75 下挂载的实体（caster）的 attr 59。
    follow_get_caster_x = make_get_attr(59, desc="frame: caster.X (followPlayer=1 用)")
    follow_get_caster_y = make_get_attr(60, desc="frame: caster.Y (followPlayer=1 用)")
    follow_write_X0 = make_modify_entity_tag(
        TAG_IDS["casterX"], P(follow_get_caster_x, PT_FUNC_RET),
        desc="frame: X0 = caster.X (followPlayer 分支)"
    )
    follow_write_Y0 = make_modify_entity_tag(
        TAG_IDS["casterY"], P(follow_get_caster_y, PT_FUNC_RET),
        desc="frame: Y0 = caster.Y (followPlayer 分支)"
    )
    follow_then_order = make_order(
        [follow_write_X0, follow_write_Y0],
        desc="frame: followPlayer=1 时刷新 X0/Y0 (v0.3)"
    )
    follow_cond = make_value_compare(
        P(EXT_FOLLOW, PT_EXTRA_PARAM), CMP_NEQ, P(0),
        desc="frame: followPlayer != 0 ? (v0.3)"
    )
    follow_branch = make_condition_execute(
        follow_cond, follow_then_order,
        desc="frame: if followPlayer != 0 then refresh X0/Y0 (v0.3)"
    )

    # (6) 读 trajTheta / trajR (v0.2 不变 — 但 R 现在是新值)
    get_theta_tick = make_get_entity_tag(TAG_IDS["trajTheta"], desc="frame: 读 trajTheta")
    get_R_tick = make_get_entity_tag(TAG_IDS["trajR"], desc="frame: 读 trajR")
    cos_theta = make_math_cos(P(get_theta_tick, PT_FUNC_RET), desc="frame: cos(θ)*10000")
    sin_theta = make_math_sin(P(get_theta_tick, PT_FUNC_RET), desc="frame: sin(θ)*10000")

    # (7) 算 newX/newY = X0 + R·cos(θ)/10000  (v0.2 不变)
    get_X0 = make_get_entity_tag(TAG_IDS["casterX"], desc="frame: 读 X0")
    get_Y0 = make_get_entity_tag(TAG_IDS["casterY"], desc="frame: 读 Y0")
    calc_new_X = make_calc(
        [P(get_X0, PT_FUNC_RET),
         P(OP_ADD), P(get_R_tick, PT_FUNC_RET),
         P(OP_MULTI), P(cos_theta, PT_FUNC_RET),
         P(OP_DIV), P(10000)],
        desc="frame: newX = X0 + R·cos(θ)/10000"
    )
    calc_new_Y = make_calc(
        [P(get_Y0, PT_FUNC_RET),
         P(OP_ADD), P(get_R_tick, PT_FUNC_RET),
         P(OP_MULTI), P(sin_theta, PT_FUNC_RET),
         P(OP_DIV), P(10000)],
        desc="frame: newY = Y0 + R·sin(θ)/10000"
    )
    # (8) 写 X/Y 到子弹实体属性 + 应用位置 (v0.2 不变)
    write_X = make_modify_entity_attr(59, P(calc_new_X, PT_FUNC_RET), desc="frame: 子弹.X = newX")
    write_Y = make_modify_entity_attr(60, P(calc_new_Y, PT_FUNC_RET), desc="frame: 子弹.Y = newY")
    change_pos = make_change_entity_position(
        P(calc_new_X, PT_FUNC_RET),
        P(calc_new_Y, PT_FUNC_RET),
        desc="frame: 应用位置到引擎",
    )

    # (9) v0.4 销毁条件 — 仅保留 maxRadius / minRadius 两条
    # （删 v0.3 的 lifetime 销毁机制：BulletConfig.LastTime 自管子弹生命）
    destroy_eff = make_destroy_entity(desc="frame: 销毁子弹自身 (v0.4 两条件共享)")
    # 9.1 maxRadius 检查：R > maxRadius (v0.4 op=3 修正，v0.3 错用 op=5 实际是 <)
    get_R_for_max = make_get_entity_tag(
        TAG_IDS["trajR"], desc="frame: 读 trajR (maxRadius 检查)"
    )
    cond_max = make_value_compare(
        P(get_R_for_max, PT_FUNC_RET), CMP_GT,
        P(EXT_MAX_R, PT_EXTRA_PARAM),
        desc="frame: R > maxRadius ? (v0.4 op=3 TCO_BIGGER 修正)"
    )
    branch_max = make_condition_execute(
        cond_max, destroy_eff,
        desc="frame: if R>maxRadius then DESTROY (v0.4)"
    )
    # 9.2 minRadius 检查：R < minRadius (默认 0 永不触发)
    # v0.4 op=5 修正，v0.3 错用 op=3 实际是 >
    get_R_for_min = make_get_entity_tag(
        TAG_IDS["trajR"], desc="frame: 读 trajR (minRadius 检查)"
    )
    cond_min = make_value_compare(
        P(get_R_for_min, PT_FUNC_RET), CMP_LT,
        P(EXT_MIN_R, PT_EXTRA_PARAM),
        desc="frame: R < minRadius ? (v0.4 op=5 TCO_SMALLER 修正)"
    )
    branch_min = make_condition_execute(
        cond_min, destroy_eff,
        desc="frame: if R<minRadius then DESTROY (v0.4)"
    )

    # OnTick 单帧 ORDER（v0.4 链 — 删 add_elapsedFrames + branch_lifetime）
    ontick_frame = make_order(
        [add_theta, add_curRadSpd, add_R, follow_branch,
         write_X, write_Y, change_pos,
         branch_max, branch_min],
        desc="OnTick 单帧 v0.4：θ+=ω → curRadSpd+=aR/30 → R+=curRadSpd → "
             "followPlayer 分支 → 改 X/Y → 应用位置 → "
             "maxR/minR 双条件检查（lifetime 销毁机制 v0.4 删除，由 BulletConfig.LastTime 自管）"
    )

    # OnTick REPEAT
    ontick_repeat = make_repeat_each_frame(ontick_frame, desc="OnTick REPEAT (每帧)")

    # OnTick init 根（暴露给调用方）— v0.4 删 init_elapsedFrames + init_damagePool
    ONTICK_INIT_EID = 32300101  # 固定 ID，sticky 里告知调用方
    ontick_init_payload = {
        "ID": ONTICK_INIT_EID, "SkillEffectType": ET["ORDER"],
        "Params": [
            P(init_R), P(init_theta), P(init_X0), P(init_Y0),
            P(init_curRadSpd),
            P(ontick_repeat),
        ],
    }
    b.add_node(
        "TSET_ORDER_EXECUTE", ONTICK_INIT_EID, ontick_init_payload,
        desc="OnTick init v0.4: 记录 R0/θ_0/X0/Y0/curRadSpd + 启动每帧 REPEAT\n"
             "调用方挂 BulletConfig.AfterBornSkillEffectExecuteInfo",
        effect_type=ET["ORDER"],
    )
    # 注：next_eid 在以上 alloc_eid 调用中已自然滚动，ONTICK_INIT_EID 是手填固定常量
    # 不冲突（32300101 远高于已分配的 32300002+~80 区间）

    # ===== 模板根 ORDER (IsTemplate=true) =====
    root_eid = ROOT_TEMPLATE_EID
    root_payload = {
        "ID": root_eid, "SkillEffectType": ET["ORDER"],
        "Params": [P(init_order), P(repeat_eid)],
    }
    b.add_node(
        "TSET_ORDER_EXECUTE", root_eid, root_payload,
        is_template=True, template_params=TPARAMS,
        desc="旋转扩张子弹圈模板根 v0.4（10 项 TemplateParam 全真消费 + op 修正）",
        effect_type=ET["ORDER"],
    )

    return b


def make_sticky_notes() -> list:
    """生成画布大注释（团队 v3 模板：5 段纯逻辑骨架）"""
    overview = (
        "【旋转扩张子弹圈 通用模板 v0.4】\n\n"
        "【v0.4 净改动】\n"
        "1) 删 lifetime + damagePerHit 两项（共 -2 个 EXT 槽 / -2 个 SkillTag /\n"
        "   -1 init / -1 add / -4 销毁链节点）— BulletConfig 自管。\n"
        "2) 修正 TSCT_VALUE_COMPARE 操作符 op 编码（v0.3 错配，是用户报\n"
        "   '改了参数无效' 的根因）。来源 common.nothotfix.cs L7929 TConditionOperator：\n"
        "       1=`==` 2=`!=` 3=`>` 4=`>=` 5=`<` 6=`<=`\n"
        "   maxRadius 改 op=3（>），minRadius 改 op=5（<），followPlayer != 0 op=2 不变。\n"
        "3) 节点数 89 → ~70，10/10 真消费（v0.3 是 12/12 但 op 错配 → 实际只 7/12 生效）。\n\n"
        "【作用】\n"
        "通用旋转扩张子弹圈算法模板，被其他技能图通过\n"
        "TSET_RUN_SKILL_EFFECT_TEMPLATE 复用。两层结构：\n"
        "  L1 主流程：以 caster 为圆心瞬间生成 N 颗子弹按 2π/N\n"
        "      均匀分布在初始半径 R0 圆周上，可通过 φ 调长边朝向。\n"
        "  L2 OnTick 工具 effect (ID=32300101)：每帧让子弹按\n"
        "      运动学方程做螺旋扩张/收缩，并按 maxR/minR 两个销毁条件自检。\n"
        "      调用方需把这个 ID 手动配到 BulletConfig.AfterBornSkillEffectExecuteInfo\n"
        "      （或在自家技能图里 RUN 它）。\n\n"
        "【流程 — L1 圆周分布（不变）】\n"
        "1. 创建 N 颗子弹按 2π/N 均匀分布在初始半径 R0 圆周\n"
        "   → θ_i = (i-1)·360/N (度)\n"
        "   → abs_angle = caster.facing + θ_i\n"
        "   → spawn_X = caster.X + R0·cos(abs_angle)\n"
        "   → spawn_Y = caster.Y + R0·sin(abs_angle)\n"
        "     （用 Effect 73/74「角度距离计算位置 X/Y」一步出位置）\n"
        "2. 每颗子弹长边沿 heading = abs_angle + 90 + φ\n"
        "   φ=0  → 切线（默认花瓣绽放）\n"
        "   φ=90 → 径向（刺向外）\n\n"
        "【流程 — L2 OnTick 轨迹 v0.4（effect ID=32300101）】\n"
        "init 阶段（子弹生成时执行一次，主体=子弹）:\n"
        "  - trajR (实体级) = R0\n"
        "  - trajTheta (实体级) = facing - 90 - φ\n"
        "  - X0/Y0 (实体级) = 子弹.X / 子弹.Y\n"
        "  - currentRadialSpeed (实体级) = vR\n"
        "  - 启动 REPEAT(interval=1, count=-1)\n"
        "每帧执行（主体=子弹）v0.4 链:\n"
        "  - trajTheta += ω/帧\n"
        "  - currentRadialSpeed += aR/30\n"
        "  - trajR += currentRadialSpeed\n"
        "  - if followPlayer != 0 then\n"
        "      X0 = caster.X (CommonParam=4 主体伤害归属 = caster)\n"
        "      Y0 = caster.Y\n"
        "  - newX = X0 + trajR·cos(trajTheta)/10000\n"
        "  - newY = Y0 + trajR·sin(trajTheta)/10000\n"
        "  - 子弹.X = newX, 子弹.Y = newY → ChangeEntityPosition 应用\n"
        "  - if R > maxRadius then DESTROY (op=3 TCO_BIGGER)\n"
        "  - if R < minRadius then DESTROY (op=5 TCO_SMALLER, 默认 0 不触发)\n"
        "中断: maxR/minR 触发 / 子弹被打死 / BulletConfig.LastTime 到期\n\n"
        "【特殊条件 / 框架适配】\n"
        "- 单位约定：\n"
        "    ω 单位「度/帧」（不是°/秒！）。30212010 直接填每帧值，本模板沿用。\n"
        "      换算：°/秒 ÷ 30fps = °/帧。默认 ω=15°/帧 ≈ 450°/秒。\n"
        "    vR 单位「单位/帧」（项目内坐标系单位）。默认 vR=10/帧。\n"
        "    aR 单位「单位/秒²」（项目惯例）。模板内每帧 aR/30 即每帧增量。\n"
        "      默认 aR=0 → 匀速径向运动等同 v0.2。\n"
        "    maxRadius / minRadius 单位「项目坐标系单位」（同 R0）。\n"
        "    followPlayer：0=圆心固定（v0.2 行为），任何非零=每帧跟随 caster。\n"
        "- TSCT_VALUE_COMPARE 操作符（C# 真值，common.nothotfix.cs L7929）:\n"
        "    TCO_NULL=0 TCO_EQUAL=1 TCO_NOT_EQUAL=2\n"
        "    TCO_BIGGER=3 (>) TCO_BIGGER_OR_EQUAL=4 (>=)\n"
        "    TCO_SMALLER=5 (<) TCO_SMALLER_OR_EQUAL=6 (<=)\n"
        "- 子弹生命：由 BulletConfig.LastTime 自管。模板不再用\n"
        "    elapsedFrames>=lifetime*30 → DESTROY 越权销毁。\n"
        "- 子弹伤害：由 BulletConfig.AfterBornSkillEffectExecuteInfo 链路自管。\n"
        "    模板不再走 SkillTag 32300714 中转。如果调用方需要 EXT_DAMAGE 之类\n"
        "    动态调伤害，请在 BulletConfig 自家命中链上读 EXT_PARAM。\n"
        "- pierceCount: 仍由 BulletConfig 内自带配置，模板不接管。\n\n"
        "【调用方接入步骤】\n"
        "1. 把本模板拖入自家技能图，TemplateParam 填 10 项（见下）\n"
        "2. 在调用方使用的 BulletConfig 里：\n"
        "   AfterBornSkillEffectExecuteInfo.SkillEffectConfigID = 32300101\n"
        "3. 子弹会自动按 ω/vR/aR 螺旋扩张/收缩 + maxR/minR 自动销毁\n\n"
        "【参数（默认值参考 30212010 + 算法文档「花瓣绽放」预设）】\n"
        "[1]  bulletID (BulletConfig)         调用方拉子弹\n"
        "[2]  子弹数N                         8\n"
        "[3]  初始半径R0                      100\n"
        "[4]  切线偏移角φ(度)                  0\n"
        "[5]  径向速度vR(每帧)                10\n"
        "[6]  径向加速度aR(每秒)              0\n"
        "[7]  整团角速度ω(度每帧)             15\n"
        "[8]  maxRadius                       1500  (R > maxR → DESTROY)\n"
        "[9]  minRadius                       0     (R < minR → DESTROY，默认 0 不触发)\n"
        "[10] followPlayer(0或1)              0     (0=固定圆心 / 非零=每帧跟随 caster)\n\n"
        "【联动】\n"
        "调用方以 TSET_RUN_SKILL_EFFECT_TEMPLATE 调用本模板，\n"
        "在 SkillConfigNode 外壳里传入 10 项参数 + 在 BulletConfig\n"
        "上挂 OnTick effect 32300101。命中链路 / 伤害 / 生命周期由\n"
        "BulletConfig 自家 hit 链 + LastTime 完成。L1 主流程仍是「t=0\n"
        "瞬间分布」，L2 OnTick 实现「螺旋扩张/收缩 + maxR/minR 销毁」运动学。\n\n"
        "【参考真实样本】\n"
        "30212010（叶散风行）— L2 OnTick 链结构同款；\n"
        "rid 1010/1011 用 TSET_CONDITION_EXECUTE+TSCT_VALUE_COMPARE 做条件分支；\n"
        "rid 1031/1035 用 TSET_DESTROY_ENTITY (Params=[V=75/PT=1, V=1, V=0]) 销毁主体。\n"
    )
    return [{
        "GUID": str(uuid.uuid4()),
        "position": {
            "serializedVersion": "2",
            "x": -180.0, "y": 60.0,
            "width": 760.0, "height": 1800.0,
        },
        "title": "[概览] 旋转扩张子弹圈 通用模板 v0.4 — 10/10 全真消费 + op 修正",
        "content": overview,
    }]


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    b = build()
    notes = make_sticky_notes()
    b.emit(OUTPUT, sticky_notes=notes)
    print(f"✓ 模板生成成功 → {OUTPUT}")
    print(f"  节点数: {len(b.refs)}")
    print(f"  边数:   {len(b.edges)}")
    # 输出 ID 范围
    ids = [r["data"]["ID"] for r in b.refs]
    print(f"  ID 范围: {min(ids)} ~ {max(ids)}")
    print(f"  模板根 ID: {ROOT_TEMPLATE_EID}")


if __name__ == "__main__":
    main()
