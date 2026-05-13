#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rewrite_30212009.py — 一次性脚本

把 30212009 千叶散华的"3 段分层手动发射"逻辑替换为扇形分层弹幕模板调用。

修改清单（详见 GATE-1 拓扑审核）：
  1. 删除旧子弹发射逻辑（CREATE_BULLET × 2 / MODIFY_TAG × 13 / NUM_CALCULATE × 5 / etc）
  2. 删除旧 SkillTagsConfigNode 6 个（320129/130/137/144/145/146 服务"3段分层"已废弃）
  3. 删除 BulletConfigNode 320147（无用数据载体）
  4. 新增 SkillTagsConfigNode 320148（总子弹数 N，default=21）+ 320149（位移距离，default=200）
  5. 新增 RUN_TEMPLATE 调用扇形分层弹幕（CONDITION_EXECUTE 包两版：普通 / 强化）
  6. 位移模板 Param[4] 改为动态读 GET_TAG 320149
  7. 重写 stickyNotes（删旧 + 新增 3 条）
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC = PROJECT_ROOT / "<<SKILLGRAPH_JSONS_ROOT>>宗门技能/SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json"

# 模板路径常量
TPL_FAN_LAYERED = "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】扇形分层弹幕.json"
TPL_DISPLACEMENT = "<<SKILLGRAPH_JSONS_ROOT>>技能模板/技能/SkillGraph_175_0023【模板】位移_按速度距离.json"

# 模板根 effect_id（需手动确定 — 扇形模板根 ID=32100001，位移模板根=38000228）
ROOT_EFFECT_FAN = 32100001
ROOT_EFFECT_DISPLACE = 38000228

# 新分配的 effect_id（避开现有 32003xxx 区段，用 32100xxx）
NEW_GET_TAG_N_EID = 32101001       # GET_TAG 320148
NEW_GET_TAG_DIST_EID = 32101002    # GET_TAG 320149
NEW_RUN_FAN_NORMAL_EID = 32101003  # RUN 普通飞叶
NEW_RUN_FAN_STRONG_EID = 32101004  # RUN 强化飞叶
NEW_CONDITION_EID = 32101005       # CONDITION_EXECUTE 包两个分支

# 新建的 SkillTag IDs
NEW_TAG_N = 320148            # 总子弹数 N
NEW_TAG_DISPLACE_DIST = 320149  # 位移距离
NEW_TAG_DEFAULTS = {
    NEW_TAG_N: ("总子弹数N", 21),
    NEW_TAG_DISPLACE_DIST: ("位移距离", 200),
}

# 删除的 SkillTagsConfigNode IDs（旧"3段分层"全废弃）
TAGS_TO_DELETE = {320129, 320130, 320137, 320144, 320145, 320146}

# 要保留的节点 — 通过 rid 锁定（基于审核时的真实 rid）
# 备注：SkillConfigNode + 入口 ORDER + 前摇/位移/特效/音效 + 320413 条件 + BulletConfig 普通/强化 + ModelConfig
# 不在此清单的全删
KEEP_RIDS = {
    1000,  # SkillConfigNode 主
    1001,  # 入口 ORDER (主流程入口) -- 但 Params 要重写
    # 前摇 / DELAY / 位移 / 特效 / 音效（保留）
    # 这些 rid 必须和真实 JSON 一致 — 让脚本动态识别更稳妥
}

# 通过 cls 类型 + Desc 关键字保留的辅助节点（更鲁棒）
KEEP_CLASSES_PRESERVE = {
    "SkillConfigNode",
    "ModelConfigNode",
    "RefConfigBaseNode",
    "TSCT_AND",
    "TSCT_HAS_BUFF",
    "TSCT_VALUE_COMPARE",
}

# 通过 Desc/ID 保留的特殊节点
KEEP_BULLET_IDS = {320159, 320160}  # 普通飞叶 + 强化飞叶（保留 BulletConfigNode）
KEEP_TAG_IDS = {320147}  # 指示器角度 tag — SkillIndicatorParamTagConfigIds 引用


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_node_by_id_and_cls(refs: list, target_id: int, target_cls: str) -> dict | None:
    for r in refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        if cls != target_cls:
            continue
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except Exception:
            continue
        if cj.get("ID") == target_id:
            return r
    return None


def get_template_params(template_path: str) -> list[dict]:
    """从模板 JSON 读 TemplateParams 定义（复制到调用方节点）"""
    full = PROJECT_ROOT / template_path.replace("/", "\\")
    if not full.exists():
        return []
    g = json.loads(full.read_text(encoding="utf-8"))
    for r in g.get("references", {}).get("RefIds", []):
        d = r.get("data", {})
        if d.get("IsTemplate") or d.get("TemplateFlags"):
            return d.get("TemplateParams", []) or []
    return []


def make_param(value, pt=0, factor=0):
    return {"Value": value, "ParamType": pt, "Factor": factor}


def make_skill_tag_node(tag_id: int, name: str, default: int, rid: int) -> dict:
    """生成 SkillTagsConfigNode"""
    cj = {
        "ID": tag_id,
        "TagType": 0,
        "Desc": name,
        "NameKey": 0,
        "DefaultValue": default,
        "FinalValueEffectID": 0,
        "RetainWhenDie": False,
    }
    return {
        "rid": rid,
        "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": 1500.0 + (rid % 5) * 350,
                         "y": -1800.0, "width": 300.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": tag_id, "Desc": name, "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",  # SkillTagsConfig
            "ConfigJson": json.dumps(cj, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillTagsConfig_{tag_id}",
        },
    }


def make_get_tag_node(tag_id: int, eid: int, rid: int, desc: str) -> dict:
    """生成 TSET_GET_SKILL_TAG_VALUE 节点（实体级 Pattern B 风格）"""
    cj = {
        "ID": eid,
        "SkillEffectType": 48,
        "Params": [
            make_param(3, pt=5),       # entity = caster
            make_param(0, pt=0),       # skill scope = "-" 实体级
            make_param(tag_id),        # tag id
            make_param(1),             # 取最终值
            make_param(0),
        ],
    }
    return {
        "rid": rid,
        "type": {"class": "TSET_GET_SKILL_TAG_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": 0.0 + (rid % 5) * 350,
                         "y": -1500.0, "width": 300.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": eid, "Desc": desc, "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",  # SkillEffectConfig
            "ConfigJson": json.dumps(cj, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillEffectConfig_{eid}",
            "SkillEffectType": 48,
        },
    }


def make_run_template_node(template_path: str, root_eid: int, extra_params: list,
                           eid: int, rid: int, desc: str) -> dict:
    """生成 TSET_RUN_SKILL_EFFECT_TEMPLATE 节点。

    extra_params: 模板的 6 个 TemplateParam 对应值（按顺序）
    """
    params = [
        make_param(1, pt=5),  # 主体
        make_param(2, pt=5),  # 目标
        make_param(root_eid, pt=0),  # root_effect_id
    ] + extra_params
    cj = {
        "ID": eid,
        "SkillEffectType": 113,  # TSET_RUN_SKILL_EFFECT_TEMPLATE
        "Params": params,
    }
    template_params_def = get_template_params(template_path)
    return {
        "rid": rid,
        "type": {"class": "TSET_RUN_SKILL_EFFECT_TEMPLATE", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": -1000.0 + (rid % 5) * 350,
                         "y": -800.0, "width": 380.0, "height": 250.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": eid, "Desc": desc, "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps(cj, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillEffectConfig_{eid}",
            "SkillEffectType": 113,
            "TemplateData": {
                "TemplateParams": template_params_def,
                "TemplatePath": template_path,
            },
        },
    }


def make_condition_execute_node(condition_eid: int, then_eid: int, else_eid: int,
                                 eid: int, rid: int, desc: str) -> dict:
    """生成 TSET_CONDITION_EXECUTE 节点。

    Params:
      [0] 条件 ID (effect_return PT=2)
      [1] 满足时执行 (PT=2)
      [2] 不满足时执行 (PT=2)
    """
    cj = {
        "ID": eid,
        "SkillEffectType": 8,  # TSET_CONDITION_EXECUTE
        "Params": [
            make_param(condition_eid, pt=2),
            make_param(then_eid, pt=2),
            make_param(else_eid, pt=2),
        ],
    }
    return {
        "rid": rid,
        "type": {"class": "TSET_CONDITION_EXECUTE", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": -500.0 + (rid % 5) * 350,
                         "y": -500.0, "width": 300.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": eid, "Desc": desc, "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps(cj, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillEffectConfig_{eid}",
            "SkillEffectType": 8,
        },
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    g = load_json(SRC)
    refs = g["references"]["RefIds"]

    # 1. 分类现有节点
    keep_refs: list[dict] = []
    skill_config_ref = None
    entry_order_ref = None
    displace_template_ref = None  # 175_0023 调用
    cond_320413_ref = None  # TSCT_AND 320413

    # 先找 SkillConfig，从中拿到真入口 ID
    real_entry_id = 0
    for r in refs:
        if r.get("type", {}).get("class", "").split(".")[-1] == "SkillConfigNode":
            cj = json.loads(r["data"]["ConfigJson"])
            real_entry_id = cj.get("SkillEffectExecuteInfo", {}).get("SkillEffectConfigID", 0)
            break
    print(f"识别真入口 ORDER ID={real_entry_id}")

    # 保留：SkillConfigNode / ModelConfigNode / TSCT 三件套 / 飞叶 BulletConfig / 320147 SkillTag
    # 也保留：动作 / DELAY / 位移模板调用 / CAMERA_SHAKE / PLAY_SOUND / PLAY_ROLE_ANIM / RefConfigBaseNode
    DELETE_CLASSES = {
        "TSET_CREATE_BULLET",       # 旧 CREATE_BULLET（替换为模板）
        "TSET_MODIFY_SKILL_TAG_VALUE",  # 旧循环计数
        "TSET_GET_SKILL_TAG_VALUE",  # 旧 GET（含 320100 跨技能）— 后面会重新加新的
        "TSET_ADD_SKILL_TAG_VALUE",  # 旧累加
        "TSET_NUM_CALCULATE",       # 旧角度计算
        "TSET_GET_FIXTURE_CENTER_Z",  # 子弹位置 Z（与子弹一起删）
        "TSET_REPEAT_EXECUTE",      # 旧分批发射循环
    }
    # 旧子弹模板调用 + 旧条件 — 都属于 CREATE_BULLET 的下游，孤立后必须删
    DELETE_EFFECT_IDS = {
        32003471, 32003472,  # 旧 子弹通用逻辑-碰撞 模板调用 × 2
        32003469,             # 旧 子弹通用逻辑-伤害
        32003468,             # 旧 子弹通用逻辑-表现
        32003431,             # 旧 CONDITION_EXECUTE "根据是否第三发飞叶决定是否强化"
        32002513, 32002520, 32002560,  # 旧 DELAY（位于旧 CREATE_BULLET 链路上的）
    }

    # 旧 SkillTagsConfigNode 选择性删除
    DELETE_TAG_IDS = TAGS_TO_DELETE

    # 子弹 320147 (无用数据载体) 删
    DELETE_BULLET_IDS = {320147}

    for r in refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except Exception:
            cj = {}
        node_id = cj.get("ID", 0)

        # 删除规则
        if cls in DELETE_CLASSES:
            continue
        if cls == "SkillTagsConfigNode" and node_id in DELETE_TAG_IDS:
            continue
        if cls == "BulletConfigNode" and node_id in DELETE_BULLET_IDS:
            continue
        # 显式删除的 effect IDs（旧 CREATE_BULLET 下游残留）
        if (cls.startswith("TSET_") or cls.startswith("TSCT_")) and node_id in DELETE_EFFECT_IDS:
            continue
        # RefConfigBaseNode：ID 指向已删 effect 的也删（孤儿引用）
        if cls == "RefConfigBaseNode":
            ref_id = r["data"].get("ManualID") or cj.get("ID")
            # 如果 ref 指向的 ID 是已删除的旧 effect、旧 CREATE_BULLET 内部 ID（32003427/35 等）
            STALE_REF_IDS = DELETE_EFFECT_IDS | {32003427, 32003433, 32003435, 32003436, 32003437,
                                                  32003434, 32003440, 32002761}
            if ref_id in STALE_REF_IDS:
                continue
        # 只保留真入口 ORDER（其 ID == SkillConfig.SkillEffectExecuteInfo.SkillEffectConfigID）
        if cls == "TSET_ORDER_EXECUTE":
            if node_id != real_entry_id:
                continue

        # 保留
        keep_refs.append(r)

        # 记录关键节点引用
        if cls == "SkillConfigNode":
            skill_config_ref = r
        elif cls == "TSET_RUN_SKILL_EFFECT_TEMPLATE":
            td = r["data"].get("TemplateData", {}) or {}
            if "175_0023" in td.get("TemplatePath", ""):
                displace_template_ref = r
        elif cls == "TSCT_AND" and node_id == 320413:
            cond_320413_ref = r

    print(f"原节点 {len(refs)} → 保留 {len(keep_refs)}")
    assert skill_config_ref is not None, "找不到 SkillConfigNode"
    # 真入口 ORDER = ID 等于 real_entry_id 的 ORDER
    entry_order_ref = next(
        (r for r in keep_refs
         if r.get("type", {}).get("class", "").split(".")[-1] == "TSET_ORDER_EXECUTE"
         and json.loads(r["data"]["ConfigJson"]).get("ID") == real_entry_id),
        None,
    )
    assert entry_order_ref is not None, f"找不到真入口 ORDER ID={real_entry_id}"
    assert displace_template_ref is not None, "找不到位移模板调用"
    assert cond_320413_ref is not None, "找不到 320413 条件"

    # 2. 修改位移模板调用 Param[4]（距离）= GET_TAG 320149
    cj = json.loads(displace_template_ref["data"]["ConfigJson"])
    cj["Params"][4] = make_param(NEW_GET_TAG_DIST_EID, pt=2)  # PT=2 effect_return
    displace_template_ref["data"]["ConfigJson"] = json.dumps(cj, ensure_ascii=False, separators=(",", ":"))
    print(f"位移模板调用 Param[4] 改为 GET_TAG_DIST({NEW_GET_TAG_DIST_EID})")

    # 3. 修改 SkillConfigNode：清理 SkillTagsList + 加新 tag entry
    cj = json.loads(skill_config_ref["data"]["ConfigJson"])
    new_tags_list = []
    for entry in cj.get("SkillTagsList", []):
        tid = entry.get("SkillTagConfigID")
        if tid in DELETE_TAG_IDS:
            continue
        new_tags_list.append(entry)
    # 加新的两个
    new_tags_list.append({"SkillTagConfigID": NEW_TAG_N, "Value": 21, "DescKey": 0})
    new_tags_list.append({"SkillTagConfigID": NEW_TAG_DISPLACE_DIST, "Value": 200, "DescKey": 0})
    cj["SkillTagsList"] = new_tags_list

    # 重写入口 ORDER 的 Params — 新的子流程
    # 找现有 ENTRY_ORDER 的子节点（保留的 effect_id）
    # 简化：从 entry_order 现有 Params 中，过滤出"还存在于 keep_refs 中"的 ID
    keep_eids: set[int] = set()
    for r in keep_refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        # 只考虑 effect 节点（SkillEffectConfig 表）
        if cls.startswith("TSET_") or cls.startswith("TSCT_"):
            try:
                ej = json.loads(r["data"].get("ConfigJson", "{}"))
                if ej.get("ID"):
                    keep_eids.add(ej["ID"])
            except Exception:
                pass

    entry_cj = json.loads(entry_order_ref["data"]["ConfigJson"])
    old_params = entry_cj.get("Params", [])
    # v2.0 扁平化：直接重建合理的执行顺序（按时序）
    # 顺序：动作 → 法阵特效 → 发射特效 → 音效 → 前摇 DELAY → 位移 → 镜头抖 → 扇形分支
    NEW_ENTRY_FLOW = [
        32002914,  # PLAY_ROLE_ANIM 角色双脚轻微离地动作
        32002001,  # CREATE_EFFECT 胸口法阵
        32002559,  # CREATE_EFFECT 发射爆发
        32002356,  # PLAY_SOUND
        32002002,  # DELAY 前摇
        32001832,  # 位移模板（已改 Param[4]=动态距离）
        32002563,  # CAMERA_SHAKE
        NEW_CONDITION_EID,  # 扇形分支 CONDITION（包两个 RUN_TEMPLATE）
    ]
    new_entry_params = [make_param(eid, pt=0) for eid in NEW_ENTRY_FLOW]
    entry_cj["Params"] = new_entry_params
    entry_order_ref["data"]["ConfigJson"] = json.dumps(entry_cj, ensure_ascii=False, separators=(",", ":"))
    skill_config_ref["data"]["ConfigJson"] = json.dumps(cj, ensure_ascii=False, separators=(",", ":"))

    print(f"入口 ORDER Params: {len(old_params)} → {len(new_entry_params)}（重建）")

    # 4. 新建节点
    new_nodes: list[dict] = []
    next_rid = max(r["rid"] for r in refs) + 1

    # SkillTagsConfigNode 320148 / 320149
    for tid, (name, default) in NEW_TAG_DEFAULTS.items():
        new_nodes.append(make_skill_tag_node(tid, name, default, next_rid))
        next_rid += 1

    # GET_TAG 320148 (N)
    new_nodes.append(make_get_tag_node(NEW_TAG_N, NEW_GET_TAG_N_EID, next_rid, "读总子弹数 N"))
    next_rid += 1

    # GET_TAG 320149 (位移距离)
    new_nodes.append(make_get_tag_node(NEW_TAG_DISPLACE_DIST, NEW_GET_TAG_DIST_EID, next_rid, "读位移距离"))
    next_rid += 1

    # RUN_TEMPLATE 普通飞叶（条件 True 走 — 反转后 = 条件成立 = 普通）
    fan_normal = make_run_template_node(
        TPL_FAN_LAYERED, ROOT_EFFECT_FAN,
        extra_params=[
            make_param(320159, pt=0),                        # [3] 子弹ID = 普通飞叶
            make_param(NEW_GET_TAG_N_EID, pt=2),             # [4] N (effect_return)
            make_param(0, pt=0),                              # [5] 内扇 fanMin
            make_param(90, pt=0),                             # [6] 外扇 fanMax
            make_param(800, pt=0),                            # [7] 基础距离 baseDist
            make_param(60, pt=0),                             # [8] 层距步进 layerStep
        ],
        eid=NEW_RUN_FAN_NORMAL_EID, rid=next_rid,
        desc="扇形分层弹幕 普通飞叶（条件成立）",
    )
    new_nodes.append(fan_normal)
    next_rid += 1

    # RUN_TEMPLATE 强化飞叶（条件 False 走）
    fan_strong = make_run_template_node(
        TPL_FAN_LAYERED, ROOT_EFFECT_FAN,
        extra_params=[
            make_param(320160, pt=0),                        # [3] 子弹ID = 强化飞叶
            make_param(NEW_GET_TAG_N_EID, pt=2),
            make_param(0, pt=0),
            make_param(90, pt=0),
            make_param(800, pt=0),
            make_param(60, pt=0),
        ],
        eid=NEW_RUN_FAN_STRONG_EID, rid=next_rid,
        desc="扇形分层弹幕 强化飞叶（条件不成立）",
    )
    new_nodes.append(fan_strong)
    next_rid += 1

    # CONDITION_EXECUTE 包两个分支
    cond_node = make_condition_execute_node(
        condition_eid=320413,
        then_eid=NEW_RUN_FAN_NORMAL_EID,
        else_eid=NEW_RUN_FAN_STRONG_EID,
        eid=NEW_CONDITION_EID, rid=next_rid,
        desc="按 320413 反转：True→普通 / False→强化",
    )
    new_nodes.append(cond_node)
    next_rid += 1

    # 5. 拼接 + 重排 rid（连续 1000+）
    all_refs = keep_refs + new_nodes
    for i, r in enumerate(all_refs):
        r["rid"] = 1000 + i
        r["data"]["computeOrder"] = i

    # 6. 重新生成 nodes 列表（外层 nodes 数组）
    g["nodes"] = [{"rid": 1000 + i} for i in range(len(all_refs))]
    g["references"]["RefIds"] = all_refs

    # 7. 重新生成 edges — 借用 skill_compiler.py 的 derive_edges
    # 简化：复用已有的边推导逻辑，但需要 Node 对象。最直接的方式：直接调 derive_edges 不现实
    # （因为节点不是 Node 对象）。所以这里手动重新推导：
    g["edges"] = derive_edges_from_refs(all_refs)
    print(f"新边数: {len(g['edges'])}")

    # 8. 重写 stickyNotes
    skill_id = json.loads(skill_config_ref["data"]["ConfigJson"]).get("ID", 30212009)
    sticky_notes = build_sticky_notes(skill_id, len(all_refs))
    g["stickyNotes"] = sticky_notes

    # 9. 输出
    g["path"] = str(SRC).replace("\\", "/")
    SRC.write_text(json.dumps(g, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"\n✓ 写入 {SRC.relative_to(PROJECT_ROOT)}")
    print(f"  最终节点数: {len(all_refs)}")


def derive_edges_from_refs(refs: list[dict]) -> list[dict]:
    """简化版 derive_edges — 扫所有节点的 ConfigJson Params 找出引用关系。"""
    # ID → GUID 映射
    id_to_guid: dict[tuple[str, int], str] = {}
    for r in refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except Exception:
            continue
        nid = cj.get("ID")
        if nid is None:
            continue
        # 简化：用 cls family 作 namespace
        if cls.startswith("TSET_") or cls.startswith("TSCT_") or cls.startswith("TSKILLSELECT_"):
            family = "effect"
        elif cls == "BulletConfigNode":
            family = "bullet"
        elif cls == "ModelConfigNode":
            family = "model"
        elif cls == "SkillTagsConfigNode":
            family = "tag"
        elif cls == "SkillConfigNode":
            family = "skill"
        else:
            family = cls
        id_to_guid[(family, nid)] = r["data"]["GUID"]

    DYNAMIC_PORT_NODES = {"TSET_ORDER_EXECUTE", "TSET_NUM_MAX", "TSET_NUM_MIN"}
    edges: list[dict] = []

    def find_target(value: int) -> str | None:
        # 优先 effect → bullet → model → tag
        for family in ("effect", "bullet", "model", "tag", "skill"):
            g = id_to_guid.get((family, value))
            if g:
                return g
        return None

    for r in refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except Exception:
            continue

        # SkillConfigNode 特殊：SkillEffectExecuteInfo 引用入口
        if cls == "SkillConfigNode":
            ee = cj.get("SkillEffectExecuteInfo", {}) or {}
            eid = ee.get("SkillEffectConfigID", 0)
            if eid:
                tg = find_target(eid)
                if tg:
                    edges.append({
                        "GUID": str(uuid.uuid4()),
                        "inputNodeGUID": tg,
                        "outputNodeGUID": r["data"]["GUID"],
                        "inputFieldName": "ID",
                        "outputFieldName": "PackedParamsOutput",
                        "inputPortIdentifier": "0",
                        "outputPortIdentifier": "SkillEffectExecuteInfo.SkillEffectConfigID",
                        "isVisible": True,
                    })
            # SkillIndicatorParamTagConfigIds → tag 引用
            for tid in cj.get("SkillIndicatorParamTagConfigIds", []) or []:
                tg = id_to_guid.get(("tag", tid))
                if tg:
                    edges.append({
                        "GUID": str(uuid.uuid4()),
                        "inputNodeGUID": tg,
                        "outputNodeGUID": r["data"]["GUID"],
                        "inputFieldName": "ID",
                        "outputFieldName": "PackedParamsOutput",
                        "inputPortIdentifier": "0",
                        "outputPortIdentifier": "SkillIndicatorParamTagConfigIds.Array.data[0]",
                        "isVisible": True,
                    })
            continue

        # BulletConfigNode AfterBornSkillEffectExecuteInfo
        if cls == "BulletConfigNode":
            for hook_field in ["BeforeBornSkillEffectExecuteInfo",
                               "AfterBornSkillEffectExecuteInfo",
                               "DieSkillEffectExecuteInfo"]:
                hk = cj.get(hook_field, {}) or {}
                eid = hk.get("SkillEffectConfigID", 0)
                if eid:
                    tg = find_target(eid)
                    if tg:
                        edges.append({
                            "GUID": str(uuid.uuid4()),
                            "inputNodeGUID": tg,
                            "outputNodeGUID": r["data"]["GUID"],
                            "inputFieldName": "ID",
                            "outputFieldName": "PackedParamsOutput",
                            "inputPortIdentifier": "0",
                            "outputPortIdentifier": f"{hook_field}.SkillEffectConfigID",
                            "isVisible": True,
                        })
            continue

        if cls in {"RefConfigBaseNode", "ModelConfigNode", "SkillTagsConfigNode"}:
            continue

        # TSET_*/TSCT_*/TSKILLSELECT_*：扫 Params
        is_dynamic = cls in DYNAMIC_PORT_NODES
        params = cj.get("Params", []) or []
        for i, p in enumerate(params):
            if not isinstance(p, dict):
                continue
            v = p.get("Value", 0)
            pt = p.get("ParamType", 0)
            if pt in (1, 5, 6) or v == 0:
                continue
            tg = find_target(v)
            if tg is None or tg == r["data"]["GUID"]:
                continue
            out_port = "0" if is_dynamic else str(i)
            edges.append({
                "GUID": str(uuid.uuid4()),
                "inputNodeGUID": tg,
                "outputNodeGUID": r["data"]["GUID"],
                "inputFieldName": "ID",
                "outputFieldName": "PackedParamsOutput",
                "inputPortIdentifier": "0",
                "outputPortIdentifier": out_port,
                "isVisible": True,
            })
    return edges


def build_sticky_notes(skill_id: int, node_count: int) -> list[dict]:
    """重写后的 stickyNotes：3 条"""
    notes = []

    # 1. 概览
    overview = (
        f"千叶散华 ({skill_id})\n"
        f"\n"
        f"-- v2.0 重构后 --\n"
        f"AI 重构于 2026-05-08\n"
        f"\n"
        f"核心改动：\n"
        f"1. 旧『3 段分层手动发射』改为扇形分层弹幕模板调用\n"
        f"2. 总子弹数 N 由 SkillTag 320148 动态读取（default=21）\n"
        f"3. 主角位移距离由 SkillTag 320149 动态读取（default=200）\n"
        f"4. 删除旧 6 个分层 SkillTag（已被模板内置参数替代）\n"
        f"\n"
        f"节点数: {node_count}"
    )
    notes.append({
        "position": {"serializedVersion": "2", "x": 400.0, "y": 470.0,
                     "width": 380.0, "height": 380.0},
        "GUID": str(uuid.uuid4()),
        "title": "[概览] 千叶散华 v2.0",
        "content": overview,
    })

    # 2. 条件分支说明
    cond_text = (
        "扇形发射条件分支：\n"
        "\n"
        "条件: 320413 = 处于三重碧叶 buff (320037)\n"
        "         AND 第3发\n"
        "\n"
        "分支:\n"
        "  True  -> 320159 普通飞叶（v2.0 反转）\n"
        "  False -> 320160 强化飞叶（v2.0 反转）\n"
        "\n"
        "（v1.0 时 True->强化，v2.0 反转）"
    )
    notes.append({
        "position": {"serializedVersion": "2", "x": 400.0, "y": 870.0,
                     "width": 360.0, "height": 280.0},
        "GUID": str(uuid.uuid4()),
        "title": "[关联] 条件分支",
        "content": cond_text,
    })

    # 3. SkillTag 声明
    tag_text = (
        "新增 SkillTag (Pattern A 私有持久):\n"
        "  320148 - 总子弹数N (default=21)\n"
        "  320149 - 位移距离  (default=200)\n"
        "\n"
        "保留 SkillTag:\n"
        "  320147 - 指示器角度 (default=90)\n"
        "           被 SkillIndicatorParamTagConfigIds 引用\n"
        "\n"
        "删除 SkillTag (旧3段分层已废):\n"
        "  320129/320130/320137/320144/320145/320146"
    )
    notes.append({
        "position": {"serializedVersion": "2", "x": 800.0, "y": 470.0,
                     "width": 360.0, "height": 320.0},
        "GUID": str(uuid.uuid4()),
        "title": "[Tag] 声明变更",
        "content": tag_text,
    })

    return notes


if __name__ == "__main__":
    main()
