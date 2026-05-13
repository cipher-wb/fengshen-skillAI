#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
patch_30212009_indicator_n_tag.py

两个小改动：
  1. 指示器去 tag 绑定，固定 90 度
     - SkillIndicatorParamTagConfigIds: [320147] -> []
     - SkillTagsList 删 320147 entry
     - 删 SkillTagsConfigNode 320147
  2. 新建 tag 320129「千叶散华总子弹数N」default=30
     - 复用之前删除的 320129 ID
     - SkillTagsConfigNode 加 320129
     - SkillConfig.SkillTagsList 加 {320129, Value=30}
     - 新增 GET_SKILL_TAG_VALUE 节点 32200003 (Pattern A 读 tag 320129)
     - 32200001/32200002 Params[4] 由 V=30/PT=0 改为 V=32200003/PT=2
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC = PROJECT_ROOT / "<<SKILLGRAPH_JSONS_ROOT>>宗门技能/SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json"

# 新增 effect ID
NEW_GET_TAG_EID = 32200003   # GET_SKILL_TAG_VALUE 读 320129
NEW_TAG_ID = 320129
NEW_TAG_DESC = "千叶散华总子弹数N"
NEW_TAG_DEFAULT = 30
NEW_TAG_VALUE_IN_LIST = 30   # SkillTagsList 中的 Value

# 已知正确的 SkillEffectType
SET_GET_SKILL_TAG_VALUE = 48


def make_param(value, pt=0, factor=0):
    return {"Value": value, "ParamType": pt, "Factor": factor}


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    d = json.loads(SRC.read_text(encoding="utf-8"))
    refs = d["references"]["RefIds"]

    # ========== Step 1: 找 SkillConfigNode + 修改字段 ==========
    sc_ref = next(
        r for r in refs
        if r.get("type", {}).get("class", "").split(".")[-1] == "SkillConfigNode"
    )
    cj = json.loads(sc_ref["data"]["ConfigJson"])

    # (1.1) 指示器去 tag 绑定
    old_tag_ids = cj.get("SkillIndicatorParamTagConfigIds", [])
    cj["SkillIndicatorParamTagConfigIds"] = []
    cj["SkillIndicatorParam"] = [90]   # 固定 90°
    print(f"指示器: tag_ids={old_tag_ids} -> [] / param=[90]")

    # (1.2) SkillTagsList: 删 320147、加 320129
    new_tags_list = [t for t in cj.get("SkillTagsList", [])
                     if t.get("SkillTagConfigID") != 320147]
    new_tags_list.append({
        "SkillTagConfigID": NEW_TAG_ID,
        "Value": NEW_TAG_VALUE_IN_LIST,
        "DescKey": 0,
    })
    cj["SkillTagsList"] = new_tags_list
    sc_ref["data"]["ConfigJson"] = json.dumps(cj, ensure_ascii=False, separators=(",", ":"))
    print(f"SkillTagsList: 删 320147 + 加 {{320129, Value=30}} -> 共 {len(new_tags_list)} 项")

    # ========== Step 2: 删 SkillTagsConfigNode 320147 ==========
    refs_kept = []
    deleted = 0
    for r in refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        if cls == "SkillTagsConfigNode":
            try:
                cjr = json.loads(r["data"].get("ConfigJson", "{}"))
                if cjr.get("ID") == 320147:
                    deleted += 1
                    continue
            except Exception:
                pass
        refs_kept.append(r)
    refs = refs_kept
    d["references"]["RefIds"] = refs
    print(f"删除 SkillTagsConfigNode 320147: {deleted} 个")

    # ========== Step 3: 新增 SkillTagsConfigNode 320129 ==========
    new_tag_node = {
        "rid": 0,  # 后排
        "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": 4500.0, "y": 1800.0,
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

    # ========== Step 4: 新增 GET_SKILL_TAG_VALUE 32200003 ==========
    # Pattern A: Params=[entity_type=4/PT=5, skill_inst=41/PT=5, tag_id, get_final=1, ?=1]
    get_node = {
        "rid": 0,
        "type": {"class": "TSET_GET_SKILL_TAG_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": 4800.0, "y": 1500.0,
                         "width": 300.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": NEW_GET_TAG_EID,
            "Desc": f"读 tag {NEW_TAG_ID} 总子弹数 N",
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps({
                "ID": NEW_GET_TAG_EID,
                "SkillEffectType": SET_GET_SKILL_TAG_VALUE,
                "Params": [
                    make_param(4, pt=5),       # entity_type=SKILL=4
                    make_param(41, pt=5),      # 初始技能实例ID
                    make_param(NEW_TAG_ID),    # tag_id=320129
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

    # ========== Step 5: 修改 32200001/32200002 Params[4] ==========
    for r in refs:
        cj_str = r["data"].get("ConfigJson", "")
        if not cj_str:
            continue
        try:
            cjr = json.loads(cj_str)
        except Exception:
            continue
        if cjr.get("ID") in (32200001, 32200002):
            cjr["Params"][4] = make_param(NEW_GET_TAG_EID, pt=2)  # PT=2 effect_return
            r["data"]["ConfigJson"] = json.dumps(cjr, ensure_ascii=False, separators=(",", ":"))
            print(f"修改 RUN_TEMPLATE {cjr['ID']} Param[4]: V=30/PT=0 -> V={NEW_GET_TAG_EID}/PT=2")

    # ========== Step 6: 重排 rid + computeOrder ==========
    for i, r in enumerate(refs):
        r["rid"] = 1000 + i
        r["data"]["computeOrder"] = i
    d["nodes"] = [{"rid": 1000 + i} for i in range(len(refs))]

    # ========== Step 7: 重新 derive edges ==========
    # 复用 rewrite_30212009_v2 的 derive_edges
    sys.path.insert(0, str(Path(__file__).parent))
    from rewrite_30212009_v2 import derive_edges
    d["edges"] = derive_edges(refs)
    print(f"新边数: {len(d['edges'])}")

    # ========== Step 8: 写盘 ==========
    SRC.write_text(json.dumps(d, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"\n✓ 写入 {SRC.relative_to(PROJECT_ROOT)}")
    print(f"  最终节点: {len(refs)}")


if __name__ == "__main__":
    main()
