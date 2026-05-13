#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rewrite_30212009_v2.py — 第二次尝试（精确手术版）

目标：
  1. ORDER 32003421 由 [重置1002 + 三排发射] 改为 [ADD 32003430 + CONDITION 32003431]
  2. CONDITION 32003431 的 Then/Else 由 旧 CREATE_BULLET 改为 新 RUN_TEMPLATE
  3. 新增 2 个 RUN_SKILL_EFFECT_TEMPLATE 调用 扇形分层弹幕模板
     - Then = 32100001 强化飞叶 (320160), N=30
     - Else = 32100002 普通飞叶 (320159), N=30
  4. SkillConfig.SkillTagsList 删 6 项 (320129/130/137/144/145/146)
  5. 删除所有不可达节点 (reachability cleanup)
  6. 重写 stickyNotes
  7. 重新 derive edges

设计原则：
  - 入口 ORDER 32001684 完全不动
  - DELAY 32002513 不动 (仍指向 32003421)
  - 通过修改 32003421 内部 Params 实现"原地手术"
  - 用 reachability 自动清理孤儿
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC = PROJECT_ROOT / "<<SKILLGRAPH_JSONS_ROOT>>宗门技能/SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json"

TPL_FAN_LAYERED = "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】扇形分层弹幕.json"
ROOT_EFFECT_FAN = 32100001  # 扇形分层弹幕模板根 effect_id（与模板内部一致）

# 新分配的 effect_id（避开现有 32003xxx 区段）
NEW_RUN_STRONG_EID = 32200001  # RUN 强化飞叶 (BulletConfig 320160) - Then
NEW_RUN_NORMAL_EID = 32200002  # RUN 普通飞叶 (BulletConfig 320159) - Else

# 删除的旧 SkillTagsConfigNode (旧"3排分层"系统专用，不再被任何节点用)
DELETE_TAG_IDS = {320129, 320130, 320137, 320144, 320145, 320146}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_template_params(template_path: str) -> list[dict]:
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


def make_run_template_node(eid: int, bullet_id: int, n: int, desc: str) -> dict:
    """生成 TSET_RUN_SKILL_EFFECT_TEMPLATE 调用扇形分层弹幕模板。

    Params 按调用约定:
      [0] 主体  (1/PT=5)
      [1] 目标  (2/PT=5)
      [2] 模板根 effect_id (32100001)
      [3] 子弹ID  (BulletConfig)
      [4] 总子弹数 N
      [5] 内层扇角 fanMin
      [6] 外层扇角 fanMax
      [7] 基础距离 baseDist
      [8] 层距步进 layerStep
    """
    cj = {
        "ID": eid,
        "SkillEffectType": 118,  # TSET_RUN_SKILL_EFFECT_TEMPLATE = 118 (注意：113 是 TSET_SHOW_SECONDARY_DIALOGUE，曾踩过这个坑)
        "Params": [
            make_param(1, pt=5),  # 主体
            make_param(2, pt=5),  # 目标
            make_param(ROOT_EFFECT_FAN),
            make_param(bullet_id),
            make_param(n),
            make_param(0),    # fanMin = 0
            make_param(90),   # fanMax = 90
            make_param(200),  # baseDist = 200 (= 现位移距离一致)
            make_param(100),  # layerStep = 100
        ],
    }
    return {
        "rid": 0,  # 后面会重排
        "type": {"class": "TSET_RUN_SKILL_EFFECT_TEMPLATE",
                 "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2",
                         "x": 5000.0 + (eid % 5) * 350,
                         "y": 1500.0, "width": 380.0, "height": 250.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": eid, "Desc": desc,
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps(cj, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillEffectConfig_{eid}",
            "SkillEffectType": 118,
            "TemplateData": {
                "TemplateParams": get_template_params(TPL_FAN_LAYERED),
                "TemplatePath": TPL_FAN_LAYERED,
            },
        },
    }


def collect_referenced_ids(cj: dict, cls: str) -> set:
    """从节点 ConfigJson 中提取所有"被引用的"节点 ID。

    覆盖：
      - SkillConfigNode 的 SkillEffectExecuteInfo + SkillIndicatorParamTagConfigIds + SkillTagsList
      - BulletConfigNode 的 BeforeBorn / AfterBorn / DieSkillEffectExecuteInfo
      - TSET_*/TSCT_* 的 Params 中 PT=0/2 的 Value（指向其他 effect）
    """
    refs = set()

    if cls == "SkillConfigNode":
        ee = cj.get("SkillEffectExecuteInfo", {}) or {}
        if ee.get("SkillEffectConfigID"):
            refs.add(ee["SkillEffectConfigID"])
        ee2 = cj.get("SkillEffectPassiveExecuteInfo", {}) or {}
        if ee2.get("SkillEffectConfigID"):
            refs.add(ee2["SkillEffectConfigID"])
        for tid in cj.get("SkillIndicatorParamTagConfigIds", []) or []:
            refs.add(tid)
        for tid in cj.get("SkillIndicatorResParamTagConfigIds", []) or []:
            refs.add(tid)
        for entry in cj.get("SkillTagsList", []) or []:
            tid = entry.get("SkillTagConfigID")
            if tid:
                refs.add(tid)
        return refs

    if cls == "BulletConfigNode":
        for hook in ("BeforeBornSkillEffectExecuteInfo",
                     "AfterBornSkillEffectExecuteInfo",
                     "DieSkillEffectExecuteInfo"):
            hk = cj.get(hook, {}) or {}
            if hk.get("SkillEffectConfigID"):
                refs.add(hk["SkillEffectConfigID"])
        # BulletConfig 还会引用 ModelConfig 等
        for k in ("Model", "DieEffectModel", "HitEffectModel"):
            v = cj.get(k)
            if isinstance(v, int) and v > 1000:
                refs.add(v)
        return refs

    if cls == "ModelConfigNode":
        # ModelConfig 一般不会引用其他节点
        return refs

    if cls == "SkillTagsConfigNode":
        # SkillTag 节点不引用其他节点
        return refs

    if cls == "RefConfigBaseNode":
        return refs

    # TSET_*/TSCT_*：扫 Params
    for p in cj.get("Params", []) or []:
        if not isinstance(p, dict):
            continue
        v = p.get("Value", 0)
        pt = p.get("ParamType", 0)
        # PT=0 (常量 / config_id) / PT=2 (effect_return) / PT=3 (skill_param tag) 都可能是节点引用
        if pt in (0, 2) and v > 1000:
            refs.add(v)
        # PT=3 引用 SkillTag id，但只有 tag_id < 1000000 才认为是 tag 引用
        # Pattern C 临时 tag (1001~1005) 不需要节点声明，跳过
        if pt == 3 and v > 1000:
            refs.add(v)
    return refs


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    g = load_json(SRC)
    refs = g["references"]["RefIds"]

    # ========== Step 1: 索引 ==========
    eid_to_ref: dict[int, dict] = {}
    for r in refs:
        cj_str = r["data"].get("ConfigJson", "")
        if not cj_str:
            continue
        try:
            cj = json.loads(cj_str)
        except Exception:
            continue
        nid = cj.get("ID")
        if nid is not None:
            eid_to_ref[nid] = r
    # RefConfigBaseNode 用 ManualID
    for r in refs:
        if r.get("type", {}).get("class", "").split(".")[-1] == "RefConfigBaseNode":
            mid = r["data"].get("ManualID")
            if mid:
                eid_to_ref.setdefault(mid, r)

    # ========== Step 2: 修改 SkillConfigNode（删 SkillTagsList 6 项）==========
    skill_config_ref = next(
        r for r in refs
        if r.get("type", {}).get("class", "").split(".")[-1] == "SkillConfigNode"
    )
    cj = json.loads(skill_config_ref["data"]["ConfigJson"])
    new_tags_list = [t for t in cj.get("SkillTagsList", [])
                     if t.get("SkillTagConfigID") not in DELETE_TAG_IDS]
    cj["SkillTagsList"] = new_tags_list
    skill_config_ref["data"]["ConfigJson"] = json.dumps(
        cj, ensure_ascii=False, separators=(",", ":"))
    print(f"SkillConfig.SkillTagsList: {len(new_tags_list)} 项（删 6 个废 tag）")

    # ========== Step 3: 修改 ORDER 32003421 的 Params ==========
    order_3421 = eid_to_ref[32003421]
    cj = json.loads(order_3421["data"]["ConfigJson"])
    cj["Params"] = [
        make_param(32003430),  # ADD 320100 += 1
        make_param(32003431),  # CONDITION 32003431
    ]
    order_3421["data"]["ConfigJson"] = json.dumps(
        cj, ensure_ascii=False, separators=(",", ":"))
    order_3421["data"]["Desc"] = "v2.0 重构：ADD 三重碧叶计数 + 条件分支选模板"
    print(f"ORDER 32003421 Params 改为 [ADD 32003430, CONDITION 32003431]")

    # ========== Step 4: 修改 CONDITION 32003431 ==========
    cond_3431 = eid_to_ref[32003431]
    cj = json.loads(cond_3431["data"]["ConfigJson"])
    # Params[0]=condition (320413, 不动), [1]=Then, [2]=Else
    cj["Params"][1] = make_param(NEW_RUN_STRONG_EID)  # Then = 强化 (与原一致)
    cj["Params"][2] = make_param(NEW_RUN_NORMAL_EID)  # Else = 普通 (与原一致)
    cond_3431["data"]["ConfigJson"] = json.dumps(
        cj, ensure_ascii=False, separators=(",", ":"))
    cond_3431["data"]["Desc"] = "True(buff+%3==1)→强化飞叶模板; False→普通飞叶模板"
    print(f"CONDITION 32003431: Then={NEW_RUN_STRONG_EID} Else={NEW_RUN_NORMAL_EID}")

    # ========== Step 5: 新增 2 个 RUN_TEMPLATE 节点 ==========
    new_run_strong = make_run_template_node(
        NEW_RUN_STRONG_EID, bullet_id=320160, n=30,
        desc="扇形分层弹幕 强化飞叶 (Then)"
    )
    new_run_normal = make_run_template_node(
        NEW_RUN_NORMAL_EID, bullet_id=320159, n=30,
        desc="扇形分层弹幕 普通飞叶 (Else)"
    )
    refs.append(new_run_strong)
    refs.append(new_run_normal)
    eid_to_ref[NEW_RUN_STRONG_EID] = new_run_strong
    eid_to_ref[NEW_RUN_NORMAL_EID] = new_run_normal

    # ========== Step 6: Reachability ==========
    # 从 SkillConfigNode 出发 BFS，所有可达的节点保留
    reachable: set[int] = set()
    queue: list[int] = []

    # 起点：SkillConfigNode 的 ID
    sc_cj = json.loads(skill_config_ref["data"]["ConfigJson"])
    skill_config_id = sc_cj.get("ID")
    reachable.add(skill_config_id)

    # 从 SkillConfig 引用的节点开始
    for ref_id in collect_referenced_ids(sc_cj, "SkillConfigNode"):
        if ref_id not in reachable:
            reachable.add(ref_id)
            queue.append(ref_id)

    # BFS
    while queue:
        eid = queue.pop(0)
        node = eid_to_ref.get(eid)
        if not node:
            continue
        cls = node.get("type", {}).get("class", "").split(".")[-1]
        try:
            cj_inner = json.loads(node["data"].get("ConfigJson", "{}"))
        except Exception:
            cj_inner = {}
        for child_id in collect_referenced_ids(cj_inner, cls):
            if child_id not in reachable:
                reachable.add(child_id)
                queue.append(child_id)

    # 添加 SkillConfig 本身（虽然没人"引用"它，但它是根）
    reachable.add(skill_config_id)

    # ========== Step 7: 保留可达的，删除其他 ==========
    kept_refs = []
    deleted_count = 0
    for r in refs:
        cj_str = r["data"].get("ConfigJson", "")
        cls = r.get("type", {}).get("class", "").split(".")[-1]

        # SkillConfigNode 总保留
        if cls == "SkillConfigNode":
            kept_refs.append(r)
            continue

        nid = None
        if cj_str:
            try:
                nid = json.loads(cj_str).get("ID")
            except Exception:
                pass
        if nid is None and cls == "RefConfigBaseNode":
            nid = r["data"].get("ManualID")

        # 删除规则：不在 reachable 中
        if nid not in reachable:
            deleted_count += 1
            continue

        kept_refs.append(r)

    print(f"原节点 {len(refs)} → 保留 {len(kept_refs)} (删除 {deleted_count} 个孤立节点)")

    # ========== Step 8: 重新分配 rid + computeOrder ==========
    for i, r in enumerate(kept_refs):
        r["rid"] = 1000 + i
        r["data"]["computeOrder"] = i

    g["references"]["RefIds"] = kept_refs
    g["nodes"] = [{"rid": 1000 + i} for i in range(len(kept_refs))]

    # ========== Step 9: 重新 derive edges ==========
    g["edges"] = derive_edges(kept_refs)
    print(f"新边数: {len(g['edges'])}")

    # ========== Step 10: 重写 stickyNotes ==========
    g["stickyNotes"] = build_sticky_notes(skill_config_id, len(kept_refs))

    # ========== Step 11: 写盘 ==========
    g["path"] = str(SRC).replace("\\", "/")
    SRC.write_text(json.dumps(g, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"\n✓ 写入 {SRC.relative_to(PROJECT_ROOT)}")
    print(f"  最终节点数: {len(kept_refs)} 边: {len(g['edges'])}")


def derive_edges(refs: list[dict]) -> list[dict]:
    """重新推导 edges — 修复 v1 的 4 个 bug：
       (1) SkillConfigNode/BulletConfigNode 的 outputFieldName 应该是 'PackedMembersOutput'
       (2) BulletConfigNode.Model 字段没生成边
       (3) TSCT_AND/OR 不在 DYNAMIC_PORT_NODES，导致 outputPortIdentifier 错（应该是 '0'）
       (4) RefConfigBaseNode 没纳入 find_target 搜索范围
    """
    DYNAMIC_PORT_NODES = {
        "TSET_ORDER_EXECUTE", "TSET_NUM_MAX", "TSET_NUM_MIN",
        "TSCT_AND", "TSCT_OR",
    }

    # ID → list of (cls, GUID)（同 ID 跨表可能多个节点）
    id_to_cands: dict[int, list[tuple[str, str]]] = {}
    for r in refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except Exception:
            cj = {}
        nid = cj.get("ID")
        if nid is None and cls == "RefConfigBaseNode":
            nid = r["data"].get("ManualID")
        if nid is None:
            continue
        id_to_cands.setdefault(nid, []).append((cls, r["data"]["GUID"]))

    def best_target(value):
        cands = id_to_cands.get(value, [])
        if not cands:
            return None
        # 优先非 RefConfigBaseNode（同 skill_compiler 实现）
        for cls, g in cands:
            if cls != "RefConfigBaseNode":
                return g
        return cands[0][1]

    edges = []

    for r in refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except Exception:
            cj = {}
        my_guid = r["data"]["GUID"]

        # ===== SkillConfigNode =====
        if cls == "SkillConfigNode":
            sei = cj.get("SkillEffectExecuteInfo", {}) or {}
            for field_name, key in [
                ("SkillEffectExecuteInfo.SkillEffectConfigID", sei.get("SkillEffectConfigID", 0)),
                ("SkillEffectExecuteInfo.SelectConfigID",      sei.get("SelectConfigID", 0)),
            ]:
                if key:
                    tg = best_target(key)
                    if tg:
                        edges.append({
                            "GUID": str(uuid.uuid4()),
                            "inputNodeGUID": tg,
                            "outputNodeGUID": my_guid,
                            "inputFieldName": "ID",
                            "outputFieldName": "PackedMembersOutput",  # ★ FIX
                            "inputPortIdentifier": "0",
                            "outputPortIdentifier": field_name,
                            "isVisible": True,
                        })
            continue

        # ===== BulletConfigNode =====
        if cls == "BulletConfigNode":
            for hook_field in ("BeforeBornSkillEffectExecuteInfo",
                               "AfterBornSkillEffectExecuteInfo",
                               "DieSkillEffectExecuteInfo"):
                hook = cj.get(hook_field, {}) or {}
                hook_id = hook.get("SkillEffectConfigID", 0)
                if hook_id:
                    tg = best_target(hook_id)
                    if tg:
                        edges.append({
                            "GUID": str(uuid.uuid4()),
                            "inputNodeGUID": tg,
                            "outputNodeGUID": my_guid,
                            "inputFieldName": "ID",
                            "outputFieldName": "PackedMembersOutput",  # ★ FIX
                            "inputPortIdentifier": "0",
                            "outputPortIdentifier": f"{hook_field}.SkillEffectConfigID",
                            "isVisible": True,
                        })
            # ★ NEW: Model 字段生成边
            model_id = cj.get("Model")
            if isinstance(model_id, int) and model_id > 0:
                tg = best_target(model_id)
                if tg:
                    edges.append({
                        "GUID": str(uuid.uuid4()),
                        "inputNodeGUID": tg,
                        "outputNodeGUID": my_guid,
                        "inputFieldName": "ID",
                        "outputFieldName": "PackedMembersOutput",
                        "inputPortIdentifier": "0",
                        "outputPortIdentifier": "Model",
                        "isVisible": True,
                    })
            continue

        # ===== ModelConfigNode / SkillTagsConfigNode / RefConfigBaseNode 不出边 =====
        if cls in {"RefConfigBaseNode", "ModelConfigNode", "SkillTagsConfigNode"}:
            continue

        # ===== TSET_*/TSCT_*/TSKILLSELECT_*：扫 Params =====
        is_dynamic = cls in DYNAMIC_PORT_NODES
        params = cj.get("Params", []) or []
        for i, p in enumerate(params):
            if not isinstance(p, dict):
                continue
            v = p.get("Value", 0)
            pt = p.get("ParamType", 0)
            if pt in (1, 5, 6) or v == 0:
                continue
            tg = best_target(v)
            if tg is None or tg == my_guid:
                continue
            out_port = "0" if is_dynamic else str(i)
            edges.append({
                "GUID": str(uuid.uuid4()),
                "inputNodeGUID": tg,
                "outputNodeGUID": my_guid,
                "inputFieldName": "ID",
                "outputFieldName": "PackedParamsOutput",
                "inputPortIdentifier": "0",
                "outputPortIdentifier": out_port,
                "isVisible": True,
            })
    return edges


def build_sticky_notes(skill_id: int, node_count: int) -> list[dict]:
    """v2.0 重构后 stickyNotes：2 条简洁版"""
    return [
        {
            "position": {"serializedVersion": "2", "x": 400.0, "y": 470.0,
                         "width": 400.0, "height": 380.0},
            "GUID": str(uuid.uuid4()),
            "title": "[概览] 千叶散华 v2.0",
            "content": (
                f"千叶散华 ({skill_id}) - v2.0 重构\n"
                f"\n"
                f"-- 改动总结 --\n"
                f"旧: 3 排手撸子弹 ({86 if False else '原'} 节点 / 3 排 ORDER + 共享 REPEAT)\n"
                f"新: 扇形分层弹幕模板 + 三重碧叶条件分支\n"
                f"\n"
                f"-- 核心流程 --\n"
                f"DELAY 20 帧 -> ORDER 32003421\n"
                f"  1. ADD tag 320100+1 (跨技能写三重碧叶计数)\n"
                f"  2. CONDITION 32003431 (条件 320413)\n"
                f"     Then(buff AND %3==1): RUN扇形(320160 强化, N=30)\n"
                f"     Else                : RUN扇形(320159 普通, N=30)\n"
                f"\n"
                f"模板参数: fanMin=0 / fanMax=90 / baseDist=200 / layerStep=100\n"
                f"\n"
                f"节点数: {node_count}"
            ),
        },
        {
            "position": {"serializedVersion": "2", "x": 850.0, "y": 470.0,
                         "width": 380.0, "height": 280.0},
            "GUID": str(uuid.uuid4()),
            "title": "[Tag] 删除清单",
            "content": (
                "删除的废 SkillTag (旧 3 排参数):\n"
                "  320129 第一排子弹数量\n"
                "  320130 第一排子弹间隔角度\n"
                "  320137 第二排子弹数量\n"
                "  320144 第二排子弹间隔角度\n"
                "  320145 第三排子弹数量\n"
                "  320146 第三排子弹间隔角度\n"
                "\n"
                "保留:\n"
                "  320147 (指示器角度, SkillIndicatorParamTagConfigIds)\n"
                "\n"
                "临时 tag 1001~1005 也随旧逻辑一起删除 (Pattern C)\n"
                "320100 跨技能写三重碧叶仍保留 (32003430)"
            ),
        },
    ]


if __name__ == "__main__":
    main()
