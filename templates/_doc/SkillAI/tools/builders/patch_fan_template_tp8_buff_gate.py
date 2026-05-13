"""
patch_fan_template_tp8_buff_gate.py
================================================================================
为「扇形分层弹幕」模板追加 TP[8] = 触发强化的 BuffID，并在循环体内加一层 buff 闸：

  - TP[8]=0           : 走老逻辑（保持向后兼容）
  - TP[8]=X & 有 buff : 走原强化闸 32100520
  - TP[8]=X & 没 buff : 走克隆的普通弹 CREATE_BULLET

同时更新千叶散华 32200006 模板调用：
  - ConfigJson.Params 追加 P[11]={V=320037, PT=0}
  - TemplateData.TemplateParams 追加第 9 项（同模板新 TP[8]）

新增节点（5 个）：
  32100528 rid=1355 TSET_CONDITION_EXECUTE  外层 buff 闸
  32100529 rid=1356 TSCT_OR                 OR 复合条件
  32100530 rid=1357 TSCT_VALUE_COMPARE      TP[8] == 0?
  32100531 rid=1358 TSCT_HAS_BUFF           施法者 has TP[8]?
  32100532 rid=1359 TSET_CREATE_BULLET      克隆的普通弹（false 分支用）

接线：
  ORDER 32100296 Params[3]: 32100520 → 32100528  (替换)
  32100528.Params: [32100529, 32100520, 32100532]  (cond/true/false)
  32100529.Params: [32100530, 32100531]            (OR 子条件)
  32100530.Params: [{V=9,PT=4}, {V=1,PT=0}, {V=0,PT=0}]    (TP[8]==0)
  32100531.Params: [{V=35,PT=5}, {V=9,PT=4}, {V=0,PT=0}]   (施法者 has TP[8])
  32100532.ConfigJson: 完整 copy 32100522 + ID 改为 32100532 + Desc

edges 变更：
  - 删 1 条: ORDER 32100296 → 32100520 (GUID c1285e58-1f96-466a-9278-f021bd6700e1)
  - 增 5 条:
      ORDER 32100296 → 32100528 (outPort=0 动态)
      32100528 → 32100529 cond (outPort=0)
      32100528 → 32100520 true (outPort=1)
      32100528 → 32100532 false (outPort=2)
      32100529 → 32100530 OR.P[0] (outPort=0 动态)
      32100529 → 32100531 OR.P[1] (outPort=0 动态)

模板根 32100001:
  - TemplateParams 追加 TP[8]（ParamUID=9 / Name="触发强化BuffID" / 默认 0）
  - TemplateParamsDesc 追加同 Name 文本
"""
from __future__ import annotations
import json
import os
import sys
import uuid

ROOT = r"<<PROJECT_ROOT_WIN>>"
TEMPLATE_FP = os.path.join(ROOT,
    r"Assets\Thirds\NodeEditor\SkillEditor\Saves\Jsons\技能模板\子弹\SkillGraph_【模板】扇形分层弹幕.json")
QYSH_FP = os.path.join(ROOT,
    r"Assets\Thirds\NodeEditor\SkillEditor\Saves\Jsons\宗门技能\木宗门技能\SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json")

# 节点 ID 常量
ID_ORDER_LOOP   = 32100296   # 循环体 ORDER（要改 Params[3]）
ID_OLD_GATE     = 32100520   # 老强化闸 CONDITION_EXECUTE (cond=N==0?)
ID_NORMAL_BUL   = 32100522   # 原普通弹 CREATE_BULLET（要 clone）

# 新分配
ID_OUTER_COND   = 32100528   # 新外层 buff 闸 COND
ID_OR           = 32100529   # OR 复合条件
ID_CMP_TP8_ZERO = 32100530   # TP[8]==0 比较
ID_HAS_BUFF     = 32100531   # 施法者 has TP[8]
ID_NORMAL_CLONE = 32100532   # 克隆的普通弹

RID_BASE = 1355  # 1355..1359

def new_guid():
    return str(uuid.uuid4())

def make_position(x, y):
    return {
        "serializedVersion": "2",
        "x": float(x),
        "y": float(y),
        "width": 280.0,
        "height": 200.0,
    }

def make_node(rid, cls, nid, desc, config_json_dict, x, y, skill_effect_type=None, skill_condition_type=None):
    """构造一个 RefId 节点项。
    config_json_dict: dict 包含 {ID, SkillEffectType/SkillConditionType, Params}
    """
    data = {
        "GUID": new_guid(),
        "computeOrder": 900,
        "position": make_position(x, y),
        "expanded": False,
        "debug": False,
        "nodeLock": False,
        "visible": True,
        "hideChildNodes": False,
        "hidePos": {"x": 0.0, "y": 0.0},
        "hideCounter": 0,
        "ID": nid,
        "Desc": desc,
        "paramVersion": 0,
        "templateParamVersion": 0,
        "IsTemplate": False,
        "TemplateFlags": 0,
        "TemplateParams": [],
        "TemplateParamsDesc": [],
        "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps(config_json_dict, ensure_ascii=False, separators=(",", ":")),
    }
    if skill_effect_type is not None:
        data["Config2ID"] = f"SkillEffectConfig_{nid}"
        data["SkillEffectType"] = skill_effect_type
    if skill_condition_type is not None:
        data["Config2ID"] = f"SkillConditionConfig_{nid}"
        data["SkillConditionType"] = skill_condition_type
    return {
        "rid": rid,
        "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": data,
    }

def make_edge(input_guid, output_guid, in_field="ID", out_field="PackedParamsOutput", in_port="0", out_port="0"):
    return {
        "GUID": new_guid(),
        "inputNodeGUID": input_guid,
        "outputNodeGUID": output_guid,
        "inputFieldName": in_field,
        "outputFieldName": out_field,
        "inputPortIdentifier": in_port,
        "outputPortIdentifier": out_port,
        "isVisible": True,
    }

def patch_template():
    with open(TEMPLATE_FP, "r", encoding="utf-8") as f:
        d = json.load(f)

    refs = d["references"]["RefIds"]
    nodes_arr = d["nodes"]
    edges = d["edges"]

    # === 1. 构造 nid -> RefId index 和 nid -> GUID ===
    nid_to_idx = {}
    nid_to_guid = {}
    for i, r in enumerate(refs):
        nid = r.get("data", {}).get("ID")
        g = r.get("data", {}).get("GUID")
        if isinstance(nid, int) and g:
            nid_to_idx[nid] = i
            nid_to_guid[nid] = g

    # === 2. 修改 ORDER 32100296 ConfigJson.Params[3] ===
    order_idx = nid_to_idx[ID_ORDER_LOOP]
    order_ref = refs[order_idx]
    cj = json.loads(order_ref["data"]["ConfigJson"])
    assert cj["Params"][3]["Value"] == ID_OLD_GATE, f"ORDER Params[3] expected {ID_OLD_GATE}, got {cj['Params'][3]}"
    cj["Params"][3]["Value"] = ID_OUTER_COND  # 替换为新外层 COND
    order_ref["data"]["ConfigJson"] = json.dumps(cj, ensure_ascii=False, separators=(",", ":"))

    # === 3. 构造新 5 节点 ===
    # 3.1 外层 COND 32100528
    outer_cond_cj = {
        "ID": ID_OUTER_COND,
        "SkillEffectType": 47,  # CONDITION_EXECUTE
        "Params": [
            {"Value": ID_OR,           "ParamType": 0, "Factor": 0},  # cond
            {"Value": ID_OLD_GATE,     "ParamType": 0, "Factor": 0},  # true: 走老强化闸
            {"Value": ID_NORMAL_CLONE, "ParamType": 0, "Factor": 0},  # false: 走克隆普通弹
        ],
    }
    outer_cond_node = make_node(
        rid=1355, cls="TSET_CONDITION_EXECUTE", nid=ID_OUTER_COND,
        desc="外层 buff 闸: TP[8]==0 OR HAS_BUFF(caster, TP[8])",
        config_json_dict=outer_cond_cj,
        x=5800.0, y=3600.0,
        skill_effect_type=47,
    )

    # 3.2 OR 32100529
    or_cj = {
        "ID": ID_OR,
        "SkillConditionType": 2,  # TSCT_OR
        "Params": [
            {"Value": ID_CMP_TP8_ZERO, "ParamType": 0, "Factor": 0},
            {"Value": ID_HAS_BUFF,     "ParamType": 0, "Factor": 0},
        ],
    }
    or_node = make_node(
        rid=1356, cls="TSCT_OR", nid=ID_OR,
        desc="OR: TP[8]==0 OR 施法者有 buff TP[8]",
        config_json_dict=or_cj,
        x=5500.0, y=3400.0,
        skill_condition_type=2,
    )

    # 3.3 VALUE_COMPARE TP[8]==0 32100530
    cmp_cj = {
        "ID": ID_CMP_TP8_ZERO,
        "SkillConditionType": 7,  # VALUE_COMPARE
        "Params": [
            {"Value": 9, "ParamType": 4, "Factor": 0},  # TP[8] (1-based: ParamUID=9)
            {"Value": 1, "ParamType": 0, "Factor": 0},  # op=1 ("==")
            {"Value": 0, "ParamType": 0, "Factor": 0},  # 字面量 0
        ],
    }
    cmp_node = make_node(
        rid=1357, cls="TSCT_VALUE_COMPARE", nid=ID_CMP_TP8_ZERO,
        desc="TP[8] (触发强化BuffID) == 0?",
        config_json_dict=cmp_cj,
        x=5200.0, y=3200.0,
        skill_condition_type=7,
    )

    # 3.4 HAS_BUFF 32100531
    has_buff_cj = {
        "ID": ID_HAS_BUFF,
        "SkillConditionType": 18,  # HAS_BUFF
        "Params": [
            {"Value": 35, "ParamType": 5, "Factor": 0},  # 施法者-根创建者实例 ID
            {"Value": 9,  "ParamType": 4, "Factor": 0},  # TP[8] = buff ID
            {"Value": 0,  "ParamType": 0, "Factor": 0},  # 来源不限
        ],
    }
    has_buff_node = make_node(
        rid=1358, cls="TSCT_HAS_BUFF", nid=ID_HAS_BUFF,
        desc="施法者 (V=35,PT=5) 身上有 TP[8] 指定的 buff?",
        config_json_dict=has_buff_cj,
        x=5200.0, y=3600.0,
        skill_condition_type=18,
    )

    # 3.5 克隆普通弹 32100532（完整 copy 32100522 ConfigJson + 改 ID/Desc）
    normal_ref = refs[nid_to_idx[ID_NORMAL_BUL]]
    normal_cj_str = normal_ref["data"]["ConfigJson"]
    normal_cj = json.loads(normal_cj_str)
    normal_cj["ID"] = ID_NORMAL_CLONE  # 改 ID
    normal_clone_node = make_node(
        rid=1359, cls="TSET_CREATE_BULLET", nid=ID_NORMAL_CLONE,
        desc="造普通弹 (no-buff 路径 / TP[8]>0 但施法者无 buff 时走这条)",
        config_json_dict=normal_cj,
        x=5800.0, y=4200.0,
        skill_effect_type=8,
    )

    new_nodes = [outer_cond_node, or_node, cmp_node, has_buff_node, normal_clone_node]
    new_guids = {
        ID_OUTER_COND:   outer_cond_node["data"]["GUID"],
        ID_OR:           or_node["data"]["GUID"],
        ID_CMP_TP8_ZERO: cmp_node["data"]["GUID"],
        ID_HAS_BUFF:     has_buff_node["data"]["GUID"],
        ID_NORMAL_CLONE: normal_clone_node["data"]["GUID"],
    }

    # === 4. 删 1 条 edge: ORDER 32100296 → 32100520 ===
    g_order = nid_to_guid[ID_ORDER_LOOP]
    g_old_gate = nid_to_guid[ID_OLD_GATE]
    before_count = len(edges)
    edges[:] = [
        e for e in edges
        if not (e.get("inputNodeGUID") == g_old_gate and e.get("outputNodeGUID") == g_order)
    ]
    after_count = len(edges)
    assert before_count - after_count == 1, f"expected to delete 1 edge, deleted {before_count - after_count}"

    # === 5. 增 6 条 edges ===
    new_edges = [
        # ORDER → 新外层 COND（ORDER 是动态端口 outPort=0）
        make_edge(input_guid=new_guids[ID_OUTER_COND], output_guid=g_order, out_port="0"),
        # 新外层 COND → OR (cond, outPort=0)
        make_edge(input_guid=new_guids[ID_OR], output_guid=new_guids[ID_OUTER_COND], out_port="0"),
        # 新外层 COND → 32100520 (true, outPort=1)
        make_edge(input_guid=g_old_gate, output_guid=new_guids[ID_OUTER_COND], out_port="1"),
        # 新外层 COND → 克隆普通弹 (false, outPort=2)
        make_edge(input_guid=new_guids[ID_NORMAL_CLONE], output_guid=new_guids[ID_OUTER_COND], out_port="2"),
        # OR → TP[8]==0 (动态 outPort=0)
        make_edge(input_guid=new_guids[ID_CMP_TP8_ZERO], output_guid=new_guids[ID_OR], out_port="0"),
        # OR → HAS_BUFF (动态 outPort=0)
        make_edge(input_guid=new_guids[ID_HAS_BUFF], output_guid=new_guids[ID_OR], out_port="0"),
    ]
    edges.extend(new_edges)

    # === 6. 把新节点追加到 nodes 数组 和 references.RefIds ===
    for n in new_nodes:
        nodes_arr.append({"rid": n["rid"]})
        refs.append(n)

    # === 7. 在 32100001 主节点追加 TP[8] ===
    main_idx = nid_to_idx[32100001]
    main_data = refs[main_idx]["data"]
    tp_list = main_data["TemplateParams"]
    tpd_list = main_data["TemplateParamsDesc"]
    new_tp_name = "触发强化BuffID (默认 0 = 无 buff 限制 / >0 时施法者需有此 buff 才触发强化)"
    new_tp = {
        "DefaultValueDesc": "",
        "Name": new_tp_name,
        "ParamUID": 9,
        "RefTypeName": "BuffConfig",
        "RefPortTypeNames": "",
        "DefalutParam": {},
        "DefalutParamJson": '{"Value":0,"ParamType":0,"Factor":0}',
        "isConfigId": True,
        "isEnum": False,
        "RefTableFullName": "TableDR.BuffConfig",
        "RefTableManagerName": "TableDR.BuffConfigManager",
        "RefPortTypeName": "",
        "RefPortTypeFullName": "",
        "IsFunctionReturn": False,
    }
    tp_list.append(new_tp)
    tpd_list.append(new_tp_name)

    # 校验
    assert len(tp_list) == 9, f"expected 9 TPs, got {len(tp_list)}"
    assert len(tpd_list) == 9, f"expected 9 TPDs, got {len(tpd_list)}"

    # === 8. 写回 ===
    with open(TEMPLATE_FP, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

    print(f"[Template] patched: +5 nodes, +6 edges, -1 edge, TP count 8→9")
    return new_guids

def patch_qysh(template_new_tp):
    """更新千叶散华 32200006 模板调用，追加 P[11]=320037 + TP[8] 副本"""
    with open(QYSH_FP, "r", encoding="utf-8") as f:
        d = json.load(f)
    refs = d["references"]["RefIds"]
    for r in refs:
        nid = r.get("data", {}).get("ID")
        if nid == 32200006:
            cj_str = r["data"]["ConfigJson"]
            cj = json.loads(cj_str)
            # 当前 11 项: P[0..1]=固定 / P[2]=模板根 / P[3]=BulletID / P[4..10]=TP[1..7]
            # 加 P[11] = TP[8] = 320037
            assert len(cj["Params"]) == 11, f"qysh expected 11 params, got {len(cj['Params'])}"
            cj["Params"].append({"Value": 320037, "ParamType": 0, "Factor": 0})
            r["data"]["ConfigJson"] = json.dumps(cj, ensure_ascii=False, separators=(",", ":"))

            # 同步 TemplateData.TemplateParams (8 → 9)
            td = r["data"].get("TemplateData", {})
            tp_list = td.get("TemplateParams", [])
            assert len(tp_list) == 8, f"qysh expected 8 TPs, got {len(tp_list)}"
            tp_list.append(dict(template_new_tp))  # 复制模板 TP[8]

            assert len(tp_list) == 9
            break
    with open(QYSH_FP, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
    print(f"[千叶散华] patched: ConfigJson.Params 11→12, TemplateData.TemplateParams 8→9, P[11]=320037")

def main():
    new_guids = patch_template()
    # 重新打开模板拿新 TP[8]
    with open(TEMPLATE_FP, "r", encoding="utf-8") as f:
        d = json.load(f)
    for r in d["references"]["RefIds"]:
        if r.get("data", {}).get("ID") == 32100001:
            new_tp = r["data"]["TemplateParams"][8]
            break
    patch_qysh(new_tp)
    print("\n=== Patch DONE ===")
    print(f"new node GUIDs: {new_guids}")

if __name__ == "__main__":
    main()
