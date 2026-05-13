#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
patch_30212009_displace_tag.py

新增 tag 320130 千叶散华后撤距离 (default=200)，把位移模板 32001832 Param[4]
由常量 200 改为 effect_return → GET_TAG 32200004。
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC = PROJECT_ROOT / "<<SKILLGRAPH_JSONS_ROOT>>宗门技能/SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json"

NEW_TAG_ID = 320130
NEW_TAG_DESC = "千叶散华后撤距离"
NEW_TAG_DEFAULT = 200
NEW_GET_TAG_EID = 32200004
DISPLACE_NODE_ID = 32001832  # 175_0023 位移模板调用
SET_GET_SKILL_TAG_VALUE = 48


def make_param(value, pt=0, factor=0):
    return {"Value": value, "ParamType": pt, "Factor": factor}


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    d = json.loads(SRC.read_text(encoding="utf-8"))
    refs = d["references"]["RefIds"]

    # ========== 1. SkillConfig.SkillTagsList 加 320130 ==========
    sc_ref = next(
        r for r in refs
        if r.get("type", {}).get("class", "").split(".")[-1] == "SkillConfigNode"
    )
    cj = json.loads(sc_ref["data"]["ConfigJson"])
    if not any(t.get("SkillTagConfigID") == NEW_TAG_ID for t in cj.get("SkillTagsList", [])):
        cj["SkillTagsList"].append({
            "SkillTagConfigID": NEW_TAG_ID,
            "Value": NEW_TAG_DEFAULT,
            "DescKey": 0,
        })
        sc_ref["data"]["ConfigJson"] = json.dumps(cj, ensure_ascii=False, separators=(",", ":"))
        print(f"SkillTagsList 加 {{320130, Value={NEW_TAG_DEFAULT}}}")

    # ========== 2. 新增 SkillTagsConfigNode 320130 ==========
    new_tag_node = {
        "rid": 0,
        "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": 4500.0, "y": 2200.0,
                         "width": 300.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": NEW_TAG_ID,
            "Desc": NEW_TAG_DESC,
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
            "ConfigJson": json.dumps({
                "ID": NEW_TAG_ID,
                "TagType": 0,
                "Desc": NEW_TAG_DESC,
                "NameKey": 0,
                "DefaultValue": NEW_TAG_DEFAULT,
                "FinalValueEffectID": 0,
                "RetainWhenDie": False,
            }, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillTagsConfig_{NEW_TAG_ID}",
        },
    }
    refs.append(new_tag_node)
    print(f"新增 SkillTagsConfigNode {NEW_TAG_ID} (Desc={NEW_TAG_DESC!r} default={NEW_TAG_DEFAULT})")

    # ========== 3. 新增 GET_SKILL_TAG_VALUE 32200004 ==========
    get_node = {
        "rid": 0,
        "type": {"class": "TSET_GET_SKILL_TAG_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": 4800.0, "y": 1900.0,
                         "width": 300.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": NEW_GET_TAG_EID,
            "Desc": f"读 tag {NEW_TAG_ID} 后撤距离",
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps({
                "ID": NEW_GET_TAG_EID,
                "SkillEffectType": SET_GET_SKILL_TAG_VALUE,
                "Params": [
                    make_param(4, pt=5),       # entity_type=SKILL=4 (Pattern A)
                    make_param(41, pt=5),      # 初始技能实例ID
                    make_param(NEW_TAG_ID),    # tag_id=320130
                    make_param(1),             # 取最终值
                    make_param(1),             # 占位
                ],
            }, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillEffectConfig_{NEW_GET_TAG_EID}",
            "SkillEffectType": SET_GET_SKILL_TAG_VALUE,
        },
    }
    refs.append(get_node)
    print(f"新增 GET_SKILL_TAG_VALUE {NEW_GET_TAG_EID} 读 tag {NEW_TAG_ID}")

    # ========== 4. 修改 32001832 位移模板 Param[4] = effect_return → 32200004 ==========
    for r in refs:
        cj_str = r["data"].get("ConfigJson", "")
        if not cj_str:
            continue
        try:
            cjr = json.loads(cj_str)
        except Exception:
            continue
        if cjr.get("ID") == DISPLACE_NODE_ID:
            old_v = cjr["Params"][4].get("Value")
            old_pt = cjr["Params"][4].get("ParamType")
            cjr["Params"][4] = make_param(NEW_GET_TAG_EID, pt=2)
            r["data"]["ConfigJson"] = json.dumps(cjr, ensure_ascii=False, separators=(",", ":"))
            print(f"修改 位移模板 {DISPLACE_NODE_ID} Param[4]: V={old_v}/PT={old_pt} -> V={NEW_GET_TAG_EID}/PT=2")
            break

    # ========== 5. 重排 rid + computeOrder ==========
    for i, r in enumerate(refs):
        r["rid"] = 1000 + i
        r["data"]["computeOrder"] = i
    d["nodes"] = [{"rid": 1000 + i} for i in range(len(refs))]

    # ========== 6. 重新 derive edges ==========
    sys.path.insert(0, str(Path(__file__).parent))
    from rewrite_30212009_v2 import derive_edges
    d["edges"] = derive_edges(refs)
    print(f"新边数: {len(d['edges'])}")

    SRC.write_text(json.dumps(d, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"\n✓ 写入 {SRC.relative_to(PROJECT_ROOT)}")
    print(f"  最终节点: {len(refs)}")


if __name__ == "__main__":
    main()
