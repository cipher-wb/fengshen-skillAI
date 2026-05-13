"""patch_30212017_mvp3_vR_acceleration.py — MVP-3 vR 加速

新增 3 节点（仿用户 SkillEditor 创建的 32900035 / 320198 schema）：
- SkillTag 320199 (vR_acc / DefaultValue=5 / 起始 vR=5)
- TSET_ADD_SKILL_TAG_VALUE 32900040 (每帧 vR_acc += 1 / aR=1/帧)
- TSET_GET_SKILL_TAG_VALUE 32900041 (读 vR_acc 当前值)

改造:
- newX NUM_CALC 302120177 Params: [GET_X, ADD, 5 常量] → [GET_X, ADD, GET_vR_acc PT=2 NodeRef]
- ORDER body 302120175 Params: [ADD_angle, CHANGE_POS] → [ADD_angle, ADD_vR_acc, CHANGE_POS]

实测预期: X 加速向右飞 + Y 按 cos 振荡（MVP-2b 保留）
"""
import json, uuid
from pathlib import Path

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

# === Add 3 new nodes ===

# E: SkillTagsConfigNode 320199 (vR_acc)
skilltag_guid = str(uuid.uuid4())
skilltag_node = {
    "rid": 1016,
    "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": skilltag_guid, "computeOrder": 11,
        "position": {"serializedVersion":"2", "x": 1700.0, "y": 1100.0, "width":237.0, "height":135.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 320199, "Desc": "SkillTag 声明",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
        "ConfigJson": json.dumps({
            "ID": 320199, "TagType": 0,
            "Desc": "MVP3 vR累加器(初始5, 每帧+1)",
            "NameKey": 0, "DefaultValue": 5,
            "FinalValueEffectID": 0, "RetainWhenDie": False,
        }, ensure_ascii=False),
        "Config2ID": "SkillTagsConfig_320199",
    }
}

# F: ADD_SKILL_TAG_VALUE 32900040 (vR_acc += 1 per frame)
add_vr_guid = str(uuid.uuid4())
add_vr_node = {
    "rid": 1017,
    "type": {"class": "TSET_ADD_SKILL_TAG_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": add_vr_guid, "computeOrder": 51,
        "position": {"serializedVersion":"2", "x": 1900.0, "y": 900.0, "width":280.0, "height":120.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 32900040, "Desc": "vR_acc += 1 (aR 加速度 / 仿 32900035 schema)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": 32900040, "SkillEffectType": 97,
            "Params": [
                {"Value": 4, "ParamType": 5, "Factor": 0},
                {"Value": 41, "ParamType": 5, "Factor": 0},
                {"Value": 320199, "ParamType": 0, "Factor": 0},
                {"Value": 1, "ParamType": 0, "Factor": 0},  # delta = 1
                {"Value": 1, "ParamType": 0, "Factor": 0},
            ],
        }, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_32900040",
        "SkillEffectType": 97,
    }
}

# G: GET_SKILL_TAG_VALUE 32900041 (read vR_acc value)
get_vr_guid = str(uuid.uuid4())
get_vr_node = {
    "rid": 1018,
    "type": {"class": "TSET_GET_SKILL_TAG_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": get_vr_guid, "computeOrder": 71,
        "position": {"serializedVersion":"2", "x": 2700.0, "y": 1900.0, "width":280.0, "height":140.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 32900041, "Desc": "读 vR_acc 当前值 (仿 32900036)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": 32900041, "SkillEffectType": 48,
            "Params": [
                {"Value": 4, "ParamType": 5, "Factor": 0},
                {"Value": 41, "ParamType": 5, "Factor": 0},
                {"Value": 320199, "ParamType": 0, "Factor": 0},
                {"Value": 1, "ParamType": 0, "Factor": 0},
                {"Value": 1, "ParamType": 0, "Factor": 0},
            ],
        }, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_32900041",
        "SkillEffectType": 48,
    }
}

data['references']['RefIds'].extend([skilltag_node, add_vr_node, get_vr_node])
data['nodes'].extend([{"rid":1016}, {"rid":1017}, {"rid":1018}])
print('[ADD] SkillTag 320199 + ADD 32900040 + GET 32900041')

# === Modify newX NUM_CALC 302120177: P[2] 5 常量 → GET_vR_acc (PT=2 NodeRef) ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120177:
        cj['Params'][2] = {"Value": 32900041, "ParamType": 2, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "newX = GET_X + vR_acc 当前值 (动态加速 / 仿 MVP-2b cos 链)"
        print('[FIX] newX 302120177 P[2] = GET_vR_acc (PT=2)')
        break

# === Modify ORDER body 302120175 Params: [ADD_angle, ADD_vR, CHANGE_POS] ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120175:
        cj['Params'] = [
            {"Value": 32900035, "ParamType": 0, "Factor": 0},  # ADD_angle (MVP-2b)
            {"Value": 32900040, "ParamType": 0, "Factor": 0},  # ADD_vR (MVP-3 新)
            {"Value": 302120180, "ParamType": 0, "Factor": 0}, # CHANGE_POS
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "[每帧 ORDER body] 3 项: ADD_angle / ADD_vR / CHANGE_POS"
        print('[FIX] ORDER body Params = [ADD_angle, ADD_vR, CHANGE_POS] (3 items)')
        break

# === Adjust positions to ensure SkillEditor sorts ORDER children correctly ===
# y position ascending = execution order: ADD_angle (low y) → ADD_vR (mid) → CHANGE_POS (high y)
position_map = {
    32900035: 500.0,   # ADD_angle (top)
    32900040: 800.0,   # ADD_vR (middle)
    302120180: 1500.0, # CHANGE_POS (bottom)
}
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') in position_map:
        r['data']['position']['y'] = position_map[cj['ID']]
print(f'[FIX] Position y: ADD_angle=500 / ADD_vR=800 / CHANGE_POS=1500')

# === Rewrite edges ===
guid_by_id = {}
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') is not None:
        guid_by_id[cj['ID']] = r['data']['GUID']

def make_edge(target_id, owner_id, output_port='0'):
    return {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": guid_by_id[target_id],
        "outputNodeGUID": guid_by_id[owner_id],
        "inputFieldName": "ID",
        "outputFieldName": "PackedParamsOutput",
        "inputPortIdentifier": "0",
        "outputPortIdentifier": output_port,
        "isVisible": True,
    }

edges_spec = [
    # Bullet creation (unchanged)
    (302120170, 302120171, "0"),
    (302120174, 302120173, "0"),
    (302120175, 302120174, "3"),

    # ORDER body 3 children (dynamic port '0')
    (32900035, 302120175, "0"),    # ADD_angle
    (32900040, 302120175, "0"),    # ADD_vR (NEW)
    (302120180, 302120175, "0"),   # CHANGE_POS

    # CHANGE_POS
    (302120177, 302120180, "1"),
    (302120184, 302120180, "2"),

    # newX chain (CHANGED: now refs GET_vR)
    (302120176, 302120177, "0"),   # newX P[0] = GET_X
    (32900041, 302120177, "2"),    # newX P[2] = GET_vR (NEW NodeRef)

    # cos / newY chain (MVP-2b unchanged)
    (32900036, 32900037, "0"),
    (32900037, 302120184, "0"),
    (302120179, 302120184, "4"),
]
data['edges'] = [make_edge(t, o, p) for (t, o, p) in edges_spec]
print(f'[FIX] edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

# Verify
data2 = json.loads(P.read_text(encoding='utf-8'))
print(f'\n[VERIFY] total RefIds = {len(data2["references"]["RefIds"])}')
for r in data2['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') in (320199, 32900040, 32900041, 302120177, 302120175):
        print(f'  ID={cj.get("ID")}: {[(p["Value"], p["ParamType"]) for p in cj.get("Params",[])][:6]}')
