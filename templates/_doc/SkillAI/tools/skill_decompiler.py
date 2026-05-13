#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SkillGraph JSON → IR YAML 反编译器 (v0.1)

用途：
    把已有的 SkillGraph_xxx.json 还原为 IR YAML 形式，配合 skill_compiler.py
    实现"修改已有 JSON"工作流：
        JSON ─decompile─→ IR  ──编辑──→  IR'  ─compile─→ JSON'

设计目标：
    1. 对 skill_compiler.py 编译产物做到**语义可逆**（重编译后节点/参数等价，ID/GUID 可不同）
    2. 对手写 JSON / 历史 JSON 尽力还原；不认识的节点降级为 `raw_node` 表达
    3. 警告但不报错：未知 SkillEffectType / Params 长度异常等只输出 WARN 行

用法：
    python skill_decompiler.py input.json [-o output.skill.yaml] [-v]

依赖: pyyaml + skill_editor_enums.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

import yaml

TOOL_DIR = Path(__file__).parent
ENUMS_PATH = TOOL_DIR / "skill_editor_enums.json"

# ============================================================
# 枚举字典加载（用于 int → 中文反查）
# ============================================================
_ENUMS: dict = {}
if ENUMS_PATH.exists():
    _enum_data = json.loads(ENUMS_PATH.read_text(encoding="utf-8"))
    _ENUMS = _enum_data.get("enums", {})
else:
    print(f"WARNING: 找不到 {ENUMS_PATH}，反查中文名将失效。", file=sys.stderr)


def int_to_cn(enum_name: str, value: int) -> Optional[str]:
    e = _ENUMS.get(enum_name, {})
    for it in e.get("entries", []):
        if it.get("value") == value:
            cn = it.get("cn")
            return cn if cn and cn != "-" else None
    return None


def int_to_enum(enum_name: str, value: int) -> Optional[str]:
    e = _ENUMS.get(enum_name, {})
    for it in e.get("entries", []):
        if it.get("value") == value:
            return it.get("enum")
    return None


# entity 别名反查（与 compiler.resolve_ref 的 aliases 字典对应）
_ENTITY_ALIAS_REVERSE = {
    "主体单位实例ID": "主体",
    "目标单位实例ID": "目标",
    "施法者实例ID": "施法者",
    "主体单位-伤害属性归属单位": "主体伤害归属",
    "目标单位-伤害属性归属单位": "目标伤害归属",
    "施法者-伤害属性归属单位": "施法者伤害归属",
    "施法者-根创建者实例ID": "施法者根",
}


def param_to_ref(value: int, param_type: int) -> Any:
    """把 (Value, ParamType) 还原为 IR 的引用字符串或字面量。

    规则（与 compiler.resolve_ref 对称）：
      PT=0 (NULL)         → 字面量 int
      PT=1 (ATTR)         → "attr:<TBattleNatureEnum 中文名>"
      PT=2 (FUNC_RET)     → "effect_return:<id>"
      PT=3 (SKILL_PARAM)  → "tag:<id>"
      PT=4 (EXTRA_PARAM)  → "extra:<idx>"
      PT=5 (COMMON_PARAM) → "entity:<别名>" (优先) 或 "entity:<TCommonParamType 中文名>"
      PT=6 (EVENT_PARAM)  → "event:<id>"（沉淀格式，compiler 当前未实现）
    """
    if param_type == 0:
        return int(value)
    if param_type == 1:
        cn = int_to_cn("TBattleNatureEnum", value)
        return f"attr:{cn}" if cn else f"attr:{value}"
    if param_type == 2:
        return f"effect_return:{value}"
    if param_type == 3:
        return f"tag:{value}"
    if param_type == 4:
        return f"extra:{value}"
    if param_type == 5:
        cn = int_to_cn("TCommonParamType", value)
        if cn:
            short = _ENTITY_ALIAS_REVERSE.get(cn, cn)
            return f"entity:{short}"
        return f"entity:{value}"
    if param_type == 6:
        return f"event:{value}"
    # 未知 ParamType → 用 dict 保留原始三元组
    return {"value": int(value), "param_type": int(param_type)}


# ============================================================
# JSON 加载 + 节点索引
# ============================================================
class GraphIndex:
    """SkillGraph JSON 解析结果，按各种维度索引方便查找。"""

    def __init__(self, data: dict):
        self.raw = data
        self.refs: list[dict] = data.get("references", {}).get("RefIds", [])
        self.edges: list[dict] = data.get("edges", [])

        # 按 GUID / ConfigID 索引
        self.by_guid: dict[str, dict] = {}
        self.by_config_id: dict[int, dict] = {}
        # 同一 ConfigID 可能不同 cls（在不同表里碰巧 ID 重合）→ 用 (cls, id)
        self.by_cls_id: dict[tuple[str, int], dict] = {}

        for r in self.refs:
            d = r.get("data", {})
            g = d.get("GUID")
            cid = d.get("ID")
            cls = r.get("type", {}).get("class", "")
            if g:
                self.by_guid[g] = r
            if cid is not None:
                self.by_config_id[cid] = r  # 后写覆盖前写（一般 ID 唯一）
                self.by_cls_id[(cls, cid)] = r

    def parse_config(self, ref: dict) -> dict:
        """安全解析 node.data.ConfigJson 字符串。"""
        d = ref.get("data", {})
        s = d.get("ConfigJson", "")
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}

    def cls_of(self, ref: dict) -> str:
        return ref.get("type", {}).get("class", "")

    def find_root_effect_id(self) -> Optional[int]:
        """找 SkillEffectExecuteInfo.SkillEffectConfigID 边的目标节点 → 即技能主流程根。"""
        for e in self.edges:
            if e.get("outputPortIdentifier") == "SkillEffectExecuteInfo.SkillEffectConfigID":
                in_guid = e.get("inputNodeGUID")
                target = self.by_guid.get(in_guid)
                if target:
                    return target.get("data", {}).get("ID")
        return None

    def find_skill_config_node(self) -> Optional[dict]:
        for r in self.refs:
            if self.cls_of(r) == "SkillConfigNode":
                return r
        return None


# ============================================================
# Skill 元信息提取
# ============================================================
# SkillConfigNode 的 ConfigJson 字段较多，下面只取常用的（与 IR 的 skill: section 对齐）
# 字段名与 compiler.make_skill_config_node 写出的字段名严格一致（坑：别用 SkillEditor 内部别名）
_SKILL_FIELD_MAP = [
    # (cfg_key,                ir_key,            enum_name_for_int_to_cn)
    ("ID",                     None,              None),  # → meta.skill_id
    ("ElementType",            "element",         "TElementsType"),
    ("SkillMainType",          "main_type",       "TBattleSkillMainType"),
    ("SkillSubType",           "sub_type",        "TBattleSkillSubType"),
    ("DamageType",             "damage_type",     None),  # 用 _DMG_TYPE_REV
    ("CdType",                 "cd_type",         "TSkillColdType"),
    ("CdTime",                 "cd_frames",       None),
    ("SkillRange",             "range",           None),
    ("AISkillRange",           "ai_range",        None),
    ("SkillCastFrame",         "cast_frame",      None),
    ("SkillBufferStartFrame",  "buffer_start_frame", None),
    ("SkillBufferFrame",       "buffer_frame",    None),
    ("SkillBaseDuration",      "base_duration",   None),
    ("MPCost",                 "mp_cost",         None),
    ("HunLiValue",             "hunli_value",     None),
    ("SectXinfaEnergyValue",   "xinfa_energy",    None),
    ("SkillQuality",           "quality",         None),
    ("Icon",                   "icon",            None),
    ("SkillNameEditor",        "skill_name_text", None),
    ("SkillDescEditor",        "skill_desc_text", None),
]

# DamageType 的反查（与 compiler dmg_map 对应：1=直接伤害/物理 → 选 直接伤害 优先）
_DMG_TYPE_REV = {0: "无", 1: "直接伤害", 2: "法术", 3: "真实"}


def extract_skill_meta(idx: GraphIndex) -> tuple[OrderedDict, OrderedDict]:
    """提取 meta（id/name/desc/author）+ skill 段。返回 (meta, skill)。"""
    meta = OrderedDict([("ir_version", "1.0")])
    skill = OrderedDict()

    sc = idx.find_skill_config_node()
    if not sc:
        meta["skill_id"] = 0
        meta["skill_name"] = "(未知)"
        return meta, skill

    cfg = idx.parse_config(sc)
    skill_id = cfg.get("ID", 0)
    skill_name = (cfg.get("Name")
                  or cfg.get("SkillNameEditor")
                  or cfg.get("SkillNameText")
                  or f"Skill_{skill_id}")

    meta["skill_id"] = int(skill_id)
    meta["skill_name"] = str(skill_name)
    if cfg.get("SkillDescText"):
        meta["description"] = str(cfg["SkillDescText"])
    meta["author"] = "decompiled"

    # skill 段
    for cfg_key, ir_key, enum_name in _SKILL_FIELD_MAP:
        if ir_key is None:
            continue
        v = cfg.get(cfg_key)
        if v is None or v == 0 or v == "":
            continue
        # 通过枚举字典反查中文
        if enum_name:
            cn = int_to_cn(enum_name, v)
            skill[ir_key] = cn if cn else v
        elif cfg_key == "DamageType":
            skill[ir_key] = _DMG_TYPE_REV.get(v, v)
        else:
            skill[ir_key] = v

    # IR Schema 必填项兜底
    if "main_type" not in skill:
        skill["main_type"] = "功法技"
    if "sub_type" not in skill:
        skill["sub_type"] = "招式"
    if "cd_type" not in skill:
        skill["cd_type"] = "普通"
    if "element" not in skill:
        skill["element"] = "无"
    if "damage_type" not in skill:
        skill["damage_type"] = "直接伤害"

    return meta, skill


# ============================================================
# Step recognizers — 把单个 SkillEffect 节点还原为 IR step dict
# ============================================================
def _params(idx: GraphIndex, ref: dict) -> list[dict]:
    cfg = idx.parse_config(ref)
    return cfg.get("Params", [])


def _pv(p: dict) -> tuple[int, int]:
    """提取 (Value, ParamType) 二元组。"""
    return int(p.get("Value", 0)), int(p.get("ParamType", 0))


def _drop_zero_tail(d: dict, optional_keys: list[str]) -> dict:
    """从 dict 中删掉值为 0/None/空字符串的可选 key（让输出更紧凑）。"""
    for k in optional_keys:
        if k in d and (d[k] in (0, None, "", False)):
            del d[k]
    return d


def recognize_cast_anim(idx: GraphIndex, ref: dict) -> dict:
    """TSET_PLAY_ROLE_ANIM — params: [entity, anim_id, upper_body, blend_ms, speed_pct, ...]"""
    p = _params(idx, ref)
    out = OrderedDict()
    if len(p) >= 2:
        out["anim_id"] = _pv(p[1])[0]
    if len(p) >= 3 and _pv(p[2])[0] == 1:
        out["upper_body"] = True
    if len(p) >= 4:
        out["blend_ms"] = _pv(p[3])[0]
    if len(p) >= 5:
        out["speed_pct"] = _pv(p[4])[0]
    if len(p) >= 6 and _pv(p[5])[0] == 0:
        out["movable_break"] = False
    if len(p) >= 7 and _pv(p[6])[0] == 1:
        out["rapid_affect"] = True
    desc = ref["data"].get("Desc")
    if desc:
        out["desc"] = desc
    return {"cast_anim": out}


def recognize_cast_effect(idx: GraphIndex, ref: dict) -> dict:
    """TSET_CREATE_EFFECT — params[0]=model_id, [4]=duration, [6]=scale_pct, [9]=speed, [12]=z_height ..."""
    p = _params(idx, ref)
    out = OrderedDict()
    if p:
        out["model_id"] = _pv(p[0])[0]
    if len(p) >= 5:
        out["duration_frames"] = _pv(p[4])[0]
    if len(p) >= 6:
        v, pt = _pv(p[5])
        if pt == 5:
            out["follow"] = param_to_ref(v, pt)
    if len(p) >= 7:
        out["scale_pct"] = _pv(p[6])[0]
    if len(p) >= 8 and _pv(p[7])[0] != 1000:
        out["destroy_delay_ms"] = _pv(p[7])[0]
    if len(p) >= 10 and _pv(p[9])[0] != 100:
        out["speed_pct"] = _pv(p[9])[0]
    if len(p) >= 13 and _pv(p[12])[0] != 0:
        out["z_height"] = _pv(p[12])[0]
    desc = ref["data"].get("Desc")
    if desc:
        out["desc"] = desc
    _drop_zero_tail(out, ["scale_pct"])  # scale_pct=100 是默认
    if out.get("scale_pct") == 100:
        del out["scale_pct"]
    return {"cast_effect": out}


def recognize_play_sound(idx: GraphIndex, ref: dict) -> dict:
    p = _params(idx, ref)
    out = OrderedDict()
    if len(p) >= 1:
        v, pt = _pv(p[0])
        out["voice_id"] = param_to_ref(v, pt)
    if len(p) >= 2:
        out["sound_type"] = _pv(p[1])[0]
    if len(p) >= 3:
        out["config"] = _pv(p[2])[0]
    return {"play_sound": out}


def recognize_camera_shake(idx: GraphIndex, ref: dict) -> dict:
    p = _params(idx, ref)
    out = OrderedDict()
    if len(p) >= 1:
        v, pt = _pv(p[0])
        out["executor"] = param_to_ref(v, pt)
    if len(p) >= 2:
        out["target"] = _pv(p[1])[0]
    if len(p) >= 3:
        out["radius"] = _pv(p[2])[0]
    if len(p) >= 6:
        out["shake_id"] = _pv(p[5])[0]
    if len(p) >= 7 and _pv(p[6])[0] != 1:
        out["priority"] = _pv(p[6])[0]
    return {"camera_shake": out}


def recognize_apply_buff(idx: GraphIndex, ref: dict) -> dict:
    p = _params(idx, ref)
    out = OrderedDict()
    if len(p) >= 1:
        out["buff_id"] = _pv(p[0])[0]
    if len(p) >= 2:
        v, pt = _pv(p[1])
        out["target"] = param_to_ref(v, pt)
    if len(p) >= 3:
        v, pt = _pv(p[2])
        out["caster"] = param_to_ref(v, pt)
    if len(p) >= 4:
        out["stack"] = _pv(p[3])[0]
    return {"apply_buff": out}


def recognize_remove_buff(idx: GraphIndex, ref: dict) -> dict:
    p = _params(idx, ref)
    out = OrderedDict()
    if len(p) >= 1:
        out["buff_id"] = _pv(p[0])[0]
    if len(p) >= 2:
        v, pt = _pv(p[1])
        out["target"] = param_to_ref(v, pt)
    return {"remove_buff": out}


def recognize_modify_tag(idx: GraphIndex, ref: dict) -> dict:
    """TSET_MODIFY_SKILL_TAG_VALUE — params[0]=ATTR(108), [2]=tag_id, [3]=value, [4]=op_type"""
    p = _params(idx, ref)
    out = OrderedDict()
    if len(p) >= 3:
        out["tag_id"] = _pv(p[2])[0]
    if len(p) >= 4:
        v, pt = _pv(p[3])
        out["value"] = param_to_ref(v, pt)
    if len(p) >= 5:
        out["op_type"] = _pv(p[4])[0]
    return {"modify_tag": out}


def recognize_delay(idx: GraphIndex, ref: dict, walker: "EffectWalker") -> dict:
    """TSET_DELAY_EXECUTE — params[0]=frames, [1]=inner_effect_id"""
    p = _params(idx, ref)
    out = OrderedDict()
    if p:
        v, pt = _pv(p[0])
        out["frames"] = param_to_ref(v, pt) if pt != 0 else v

    # 内部效果（递归 walk）
    inner_id = _pv(p[1])[0] if len(p) >= 2 else 0
    if inner_id:
        inner_steps = walker.walk_effect(inner_id)
        out["then"] = inner_steps

    if len(p) >= 3 and _pv(p[2])[0] == 1:
        out["die_continue"] = True
    if len(p) >= 7 and _pv(p[6])[0] != 1:
        out["rapid_affect"] = False

    desc = ref["data"].get("Desc")
    if desc:
        out["desc"] = desc

    return {"delay": out}


def recognize_bullet(idx: GraphIndex, ref: dict, walker: "EffectWalker") -> dict:
    """TSET_CREATE_BULLET — 识别为子弹模式（v1.2 加入 pattern 自动判断）。

    pattern 判定逻辑（v1.2 新增）：
      - 检查子弹引用的 BulletConfigNode 的 FlyType + DieSkillEffectExecuteInfo
      - 若 FlyType=5 + 有 Die 链路 → pattern: 回旋飞回（双 Bullet 接力）
      - 否则 → pattern: 直线子弹（默认）
    """
    p = _params(idx, ref)
    out = OrderedDict()

    # v1.2: 识别 BulletConfig 看是不是回旋飞回 pattern
    bullet_id = _pv(p[0])[0] if p else 0
    bullet_node = idx.by_cls_id.get(("BulletConfigNode", bullet_id)) if bullet_id else None
    is_boomerang = False
    if bullet_node:
        bcfg = idx.parse_config(bullet_node)
        fly_type = bcfg.get("FlyType", 0)
        die_info = bcfg.get("DieSkillEffectExecuteInfo") or {}
        die_eid = die_info.get("SkillEffectConfigID", 0)
        # 启发式：FlyType=5 + 有 Die 链路 → 回旋飞回
        if fly_type == 5 and die_eid:
            is_boomerang = True

    out["pattern"] = "回旋飞回" if is_boomerang else "直线子弹"

    if p:
        out["bullet_id"] = _pv(p[0])[0]
    if len(p) >= 6 and _pv(p[5])[0]:
        out["offset_right"] = _pv(p[5])[0]
    if len(p) >= 7 and _pv(p[6])[0]:
        out["offset_forward"] = _pv(p[6])[0]
    if len(p) >= 10:
        out["is_projectile"] = bool(_pv(p[9])[0])
    if len(p) >= 13 and _pv(p[12])[0]:
        out["z_height"] = _pv(p[12])[0]
    if len(p) >= 15 and _pv(p[14])[0]:
        out["rapid_affect"] = True

    # v1.2: 回旋飞回还原 boomerang 字段块
    if is_boomerang and bullet_node:
        bcfg = idx.parse_config(bullet_node)
        last_time = bcfg.get("LastTime", 0)
        max_dist = bcfg.get("MaxDistance", 0)
        # TracePathParams 反查飞行帧 / 悬停帧（编译器存的是 [flight_frames, max_distance, ...]）
        tpp = bcfg.get("TracePathParams") or []
        flight_f = tpp[0]["Value"] if len(tpp) >= 1 else last_time
        # 找 return_bullet 的 Speed
        return_speed = 2000
        for r2 in idx.refs:
            if idx.cls_of(r2) == "BulletConfigNode":
                cj2 = idx.parse_config(r2)
                if cj2.get("ID") != bullet_id and cj2.get("FlyType") == 6:
                    return_speed = cj2.get("Speed", 2000)
                    out["return_bullet_id"] = cj2.get("ID")
                    break
        boomerang = OrderedDict()
        boomerang["flight_frames"] = flight_f
        if last_time > flight_f:
            boomerang["hover_frames"] = last_time - flight_f
        if max_dist:
            boomerang["max_distance"] = max_dist
        boomerang["return_speed"] = return_speed
        out["boomerang"] = boomerang

    desc = ref["data"].get("Desc")
    if desc:
        out["desc"] = desc

    # 命中链路：通过 BulletConfigNode.AfterBornSkillEffectExecuteInfo 找到碰撞模板
    bullet_id = out.get("bullet_id", 0)
    if bullet_id:
        bullet_node = idx.by_cls_id.get(("BulletConfigNode", bullet_id))
        if bullet_node:
            bcfg = idx.parse_config(bullet_node)
            after_born = (bcfg.get("AfterBornSkillEffectExecuteInfo") or {}).get("SkillEffectConfigID", 0)
            if after_born:
                hit = recognize_bullet_hit(idx, after_born)
                if hit:
                    out["hit"] = hit

    return {"bullet": out}


def recognize_bullet_hit(idx: GraphIndex, collision_effect_id: int) -> Optional[dict]:
    """从碰撞模板节点 → 命中 ORDER → 伤害模板 + 表现模板 还原 hit 块。"""
    coll = idx.by_config_id.get(collision_effect_id)
    if not coll:
        return None
    coll_cfg = idx.parse_config(coll)

    # 验证是否真的是"子弹通用逻辑-碰撞"模板
    if coll.get("type", {}).get("class") != "TSET_RUN_SKILL_EFFECT_TEMPLATE":
        return None
    coll_params = coll_cfg.get("Params", [])
    # 模板根 ID 在 [2]，子弹通用碰撞模板 = 190016404
    if len(coll_params) < 3 or _pv(coll_params[2])[0] != 190016404:
        return None

    hit = OrderedDict()
    # extra_params 从 coll_params[3] 开始（前 3 个是模板调用元信息: TCommonParam, TCommonParam, TemplatePathID）
    # 顺序参考 expand_bullet_straight: [命中后功能, shape_type, radius, height, _, off_right, off_fwd, ...]
    if len(coll_params) >= 6:
        hit["collision_radius"] = _pv(coll_params[5])[0]
    if len(coll_params) >= 7:
        hit["collision_height"] = _pv(coll_params[6])[0]
    if len(coll_params) >= 14:
        hit["detect_interval"] = _pv(coll_params[13])[0]

    # 命中后 ORDER
    hit_order_id = _pv(coll_params[3])[0] if len(coll_params) >= 4 else 0
    if hit_order_id:
        hit_order = idx.by_config_id.get(hit_order_id)
        if hit_order:
            order_params = idx.parse_config(hit_order).get("Params", [])
            for op in order_params:
                child_id = _pv(op)[0]
                child = idx.by_config_id.get(child_id)
                if not child:
                    continue
                ccfg = idx.parse_config(child)
                cps = ccfg.get("Params", [])
                template_id = _pv(cps[2])[0] if len(cps) >= 3 else 0
                if template_id == 190016485:  # 伤害模板
                    hit["damage"] = _extract_damage(cps)
                    # destroy_on_hit 在伤害模板的 extra_params[10] = cps[13]
                    if len(cps) >= 14 and _pv(cps[13])[0]:
                        hit["destroy_on_hit"] = True
                elif template_id == 190016523:  # 表现模板
                    # hit_effect_model 在表现模板的 extra_params[2] = cps[5]
                    if len(cps) >= 6 and _pv(cps[5])[0]:
                        hit["hit_effect_model"] = _pv(cps[5])[0]

    return hit if hit else None


def _extract_damage(cps: list[dict]) -> dict:
    """子弹通用-伤害模板 extra_params 还原为 damage 块。"""
    # [0] 子弹序号 [1] 伤害来源 [2] 伤害类型 [3] 五行 [4] flags [5] coef [6] extra ...
    out = OrderedDict()
    elem_map = {0: "随技能", 1: "金", 2: "木", 3: "水", 4: "火", 5: "土"}
    type_map = {0: "随技能", 1: "物理", 2: "法术", 3: "真实"}
    if len(cps) >= 6:
        out["element"] = elem_map.get(_pv(cps[6])[0], _pv(cps[6])[0])
    if len(cps) >= 6:
        out["type"] = type_map.get(_pv(cps[5])[0], _pv(cps[5])[0])
    if len(cps) >= 8:
        out["coef"] = _pv(cps[8])[0]
    if len(cps) >= 7:
        out["subtype_flags"] = _pv(cps[7])[0]
    if len(cps) >= 9:
        out["extra"] = _pv(cps[9])[0]
    return out


# ============================================================
# 效果树游走器
# ============================================================
class EffectWalker:
    """递归遍历 SkillEffect 树并产生 IR steps 列表。"""

    def __init__(self, idx: GraphIndex, verbose: bool = False):
        self.idx = idx
        self.verbose = verbose
        # 已访问节点防止循环引用
        self._visited: set[int] = set()
        # 子弹的 hit 链路引用的节点（碰撞/伤害/表现模板等）— 不应在主流程展开
        self._consumed_by_bullet: set[int] = set()
        self.warnings: list[str] = []

    def warn(self, msg: str):
        self.warnings.append(msg)
        if self.verbose:
            print(f"[WARN] {msg}", file=sys.stderr)

    def _mark_bullet_chain(self, bullet_id: int):
        """把子弹 hit 链路用到的节点标记为 consumed，避免在父 ORDER 里重复展开。"""
        bullet_node = self.idx.by_cls_id.get(("BulletConfigNode", bullet_id))
        if not bullet_node:
            return
        bcfg = self.idx.parse_config(bullet_node)
        coll_id = (bcfg.get("AfterBornSkillEffectExecuteInfo") or {}).get("SkillEffectConfigID", 0)
        if not coll_id:
            return
        self._consumed_by_bullet.add(coll_id)

        coll = self.idx.by_config_id.get(coll_id)
        if not coll:
            return
        coll_params = self.idx.parse_config(coll).get("Params", [])
        hit_order_id = _pv(coll_params[3])[0] if len(coll_params) >= 4 else 0
        if hit_order_id:
            self._consumed_by_bullet.add(hit_order_id)
            order_params = self.idx.parse_config(self.idx.by_config_id[hit_order_id]).get("Params", [])
            for op in order_params:
                self._consumed_by_bullet.add(_pv(op)[0])

    def walk_effect(self, eid: int) -> list[dict]:
        """走访一个效果节点，返回 IR steps 列表（一般是 1 个 step；ORDER 会展开成多个）。"""
        if eid in self._visited:
            self.warn(f"循环引用检测到 effect_id={eid}，跳过")
            return []
        self._visited.add(eid)

        ref = self.idx.by_config_id.get(eid)
        if not ref:
            self.warn(f"找不到 effect_id={eid} 对应节点")
            return [{"raw_node": {"missing_ref": eid}}]

        cls = self.idx.cls_of(ref)

        if cls == "TSET_ORDER_EXECUTE":
            # 展开为多个 step
            results: list[dict] = []
            for p in _params(self.idx, ref):
                child_id = _pv(p)[0]
                if child_id and child_id not in self._consumed_by_bullet:
                    results.extend(self.walk_effect(child_id))
            return results

        # 单一节点 → 识别
        step = self._recognize_single(ref)
        return [step]

    def _recognize_single(self, ref: dict) -> dict:
        cls = self.idx.cls_of(ref)
        try:
            if cls == "TSET_PLAY_ROLE_ANIM":
                return recognize_cast_anim(self.idx, ref)
            if cls == "TSET_CREATE_EFFECT":
                return recognize_cast_effect(self.idx, ref)
            if cls == "TSET_DELAY_EXECUTE":
                return recognize_delay(self.idx, ref, self)
            if cls == "TSET_CREATE_BULLET":
                step = recognize_bullet(self.idx, ref, self)
                bullet_id = (step.get("bullet") or {}).get("bullet_id", 0)
                if bullet_id:
                    self._mark_bullet_chain(bullet_id)
                return step
            if cls == "TSET_PLAY_SOUND":
                return recognize_play_sound(self.idx, ref)
            if cls == "TSET_CAMERA_SHAKE":
                return recognize_camera_shake(self.idx, ref)
            if cls == "TSET_ADD_BUFF":
                return recognize_apply_buff(self.idx, ref)
            if cls == "TSET_REMOVE_BUFF":
                return recognize_remove_buff(self.idx, ref)
            if cls == "TSET_MODIFY_SKILL_TAG_VALUE":
                return recognize_modify_tag(self.idx, ref)
        except Exception as ex:
            self.warn(f"识别 {cls} (id={ref['data'].get('ID')}) 时异常: {ex}")

        # 兜底：raw_node
        self.warn(f"未识别的节点类型 {cls} (id={ref['data'].get('ID')})，降级为 raw_node")
        return self._fallback_raw_node(ref)

    def _fallback_raw_node(self, ref: dict) -> dict:
        cls = self.idx.cls_of(ref)
        cfg = self.idx.parse_config(ref)
        out = OrderedDict()
        out["cls"] = cls
        params_raw = []
        for p in cfg.get("Params", []):
            v, pt = _pv(p)
            params_raw.append(param_to_ref(v, pt))
        out["params"] = params_raw
        desc = ref["data"].get("Desc")
        if desc:
            out["desc"] = desc
        return {"raw_node": out}


# ============================================================
# YAML 输出（保留顺序 + 中文友好）
# ============================================================
def _ordered_dict_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


yaml.add_representer(OrderedDict, _ordered_dict_representer)


def to_yaml(meta: dict, skill: dict, flow: list, tags: list = None) -> str:
    """组装 IR YAML 文档字符串。"""
    doc = OrderedDict()
    doc["meta"] = meta
    if skill:
        doc["skill"] = skill
    doc["flow"] = flow
    if tags:
        doc["tags"] = tags
    return yaml.dump(doc, allow_unicode=True, sort_keys=False, default_flow_style=False, indent=2)


# ============================================================
# 主流程
# ============================================================
def decompile(json_path: Path, verbose: bool = False) -> str:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    idx = GraphIndex(data)

    meta, skill = extract_skill_meta(idx)

    root_id = idx.find_root_effect_id()
    if root_id is None:
        if verbose:
            print("[WARN] 找不到 SkillEffectExecuteInfo.SkillEffectConfigID 边，flow 留空", file=sys.stderr)
        flow = []
    else:
        walker = EffectWalker(idx, verbose=verbose)
        flow = walker.walk_effect(root_id)
        if verbose and walker.warnings:
            print(f"[INFO] 反编译完成，{len(walker.warnings)} 条警告", file=sys.stderr)

    # tags（如有 SkillTagsConfigNode）
    tags = []
    for r in idx.refs:
        if idx.cls_of(r) == "SkillTagsConfigNode":
            cfg = idx.parse_config(r)
            tag = OrderedDict()
            tag["id"] = cfg.get("ID")
            if cfg.get("Desc"):
                tag["desc"] = cfg["Desc"]
            if cfg.get("DefaultValue"):
                tag["default_value"] = cfg["DefaultValue"]
            tags.append(tag)

    return to_yaml(meta, skill, flow, tags)


def main():
    ap = argparse.ArgumentParser(description="SkillGraph JSON → IR YAML 反编译器")
    ap.add_argument("input", help="输入 SkillGraph JSON 文件路径")
    ap.add_argument("-o", "--out", help="输出 YAML 路径（默认：input 同目录 + .skill.yaml）")
    ap.add_argument("-v", "--verbose", action="store_true", help="打印警告")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: 输入文件不存在: {in_path}", file=sys.stderr)
        sys.exit(1)

    out_text = decompile(in_path, verbose=args.verbose)

    if args.out:
        out_path = Path(args.out)
    else:
        # 默认：同目录，去掉 .json 加 .skill.yaml；去掉前缀 "SkillGraph_"
        stem = in_path.stem
        if stem.startswith("SkillGraph_"):
            stem = stem[len("SkillGraph_"):]
        out_path = in_path.parent / f"{stem}.skill.yaml"

    out_path.write_text(out_text, encoding="utf-8")
    print(f"✓ 反编译完成 → {out_path}")
    print(f"  flow steps: {out_text.count(chr(10) + '- ')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    main()
