"""patch_30212017_mvp2b_v2_skilltag_proper.py — MVP-2b 真振荡（正规 SkillTag）

设计变更（基于 log 揭出的认知订正）:
- ❌ entity SkillTag slot (V=41 PT=5 namespace) — 在 bullet ctx 失效
- ✅ SkillTagsConfig 声明 + ADD_SKILL_TAG (跨技能模式 P[1]={V=30212017, PT=0}) + GET_SKILL_TAG + cos PT=2 NodeRef
  - 仿 30212010 32002231 (ADD 跨技能) / 32003151 (GET) / cos 用 PT=2 NodeRef 引用 GET 输出
  - 完全用项目"正规"SkillTag 机制

新节点（3 个）:
1. SkillTagsConfigNode 320198 (angle accumulator / 重用 SkillTag 系统声明)
2. ADD_SKILL_TAG_VALUE 302120186 - 仿 30212010 32002231 / P[1]={V=30212017, PT=0} (本技能命名空间)
3. GET_SKILL_TAG_VALUE 302120187 - 仿 30212010 32003151 / 读 320198 当前值

删除节点 (1 个):
- ADD_SKILL_TAG_VALUE 302120185 (entity slot 1500 / 实测失效)

修改:
- ORDER body 302120175 Params: [ADD_SKILL_TAG, CHANGE_POS] → [ADD_SKILL_TAG_320198, CHANGE_POS]
- MATH_COS 302120181 P[0]: {V=1500, PT=3} → {V=302120187, PT=2 NodeRef GET output}
"""
import json, uuid
from pathlib import Path

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

# === Step 1: Delete old ADD_SKILL_TAG 302120185 (entity slot version) ===
before = len(data['references']['RefIds'])
data['references']['RefIds'] = [r for r in data['references']['RefIds']
                                 if json.loads(r['data'].get('ConfigJson','{}') or '{}').get('ID') != 302120185]
data['nodes'] = [n for n in data['nodes'] if n.get('rid') != 1016]
print(f'[REMOVE] ADD_SKILL_TAG 302120185 (entity slot) - {before - len(data["references"]["RefIds"])} removed')

# === Step 2: Add 3 new nodes ===

# 2a. SkillTagsConfigNode 320198
skilltag_guid = str(uuid.uuid4())
skilltag_node = {
    "rid": 1017,
    "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": skilltag_guid, "computeOrder": 10,
        "position": {"serializedVersion":"2", "x": 1700.0, "y": 900.0, "width":237.0, "height":135.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 320198, "Desc": "SkillTag 声明",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
        "ConfigJson": json.dumps({
            "ID": 320198, "TagType": 0,
            "Desc": "MVP2b角度累加器(每帧+=5)",
            "NameKey": 0, "DefaultValue": 0,
            "FinalValueEffectID": 0, "RetainWhenDie": False,
        }, ensure_ascii=False),
        "Config2ID": "SkillTagsConfig_320198",
    }
}

# 2b. ADD_SKILL_TAG_VALUE 302120186 仿 30212010 32002231
add_tag_guid = str(uuid.uuid4())
add_tag_node = {
    "rid": 1018,
    "type": {"class": "TSET_ADD_SKILL_TAG_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": add_tag_guid, "computeOrder": 50,
        "position": {"serializedVersion":"2", "x": 1900.0, "y": 700.0, "width":280.0, "height":120.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 302120186, "Desc": "SkillTag 320198 += 5/帧 (跨技能模式 P[1]=30212017 本技能 ID 命名空间 / 仿 30212010 32002231)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": 302120186, "SkillEffectType": 97,
            "Params": [
                {"Value": 4, "ParamType": 5, "Factor": 0},        # P[0] V=4 = TCPT_MAIN_SKILL_DAMAGE_PROPERTY_ORIGIN_ENTITY
                {"Value": 30212017, "ParamType": 0, "Factor": 0}, # P[1] skill ID 30212017 命名空间
                {"Value": 320198, "ParamType": 0, "Factor": 0},   # P[2] SkillTag 320198
                {"Value": 5, "ParamType": 0, "Factor": 0},        # P[3] delta = 5
                {"Value": 1, "ParamType": 0, "Factor": 0},        # P[4] flag
            ],
        }, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_302120186",
        "SkillEffectType": 97,
    }
}

# 2c. GET_SKILL_TAG_VALUE 302120187 仿 30212010 32003151
get_tag_guid = str(uuid.uuid4())
get_tag_node = {
    "rid": 1019,
    "type": {"class": "TSET_GET_SKILL_TAG_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": get_tag_guid, "computeOrder": 70,
        "position": {"serializedVersion":"2", "x": 2700.0, "y": 1700.0, "width":280.0, "height":140.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 302120187, "Desc": "读 SkillTag 320198 当前值 (仿 30212010 32003151)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": 302120187, "SkillEffectType": 48,
            "Params": [
                {"Value": 4, "ParamType": 5, "Factor": 0},
                {"Value": 30212017, "ParamType": 0, "Factor": 0},
                {"Value": 320198, "ParamType": 0, "Factor": 0},
                {"Value": 1, "ParamType": 0, "Factor": 0},
                {"Value": 1, "ParamType": 0, "Factor": 0},
            ],
        }, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_302120187",
        "SkillEffectType": 48,
    }
}

data['references']['RefIds'].extend([skilltag_node, add_tag_node, get_tag_node])
data['nodes'].extend([{"rid":1017}, {"rid":1018}, {"rid":1019}])
print(f'[ADD] SkillTag 320198 + ADD_SKILL_TAG 302120186 + GET_SKILL_TAG 302120187')

# === Step 3: Modify ORDER body Params: [ADD_TAG_NEW, CHANGE_POS] ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120175:
        cj['Params'] = [
            {"Value": 302120186, "ParamType": 0, "Factor": 0},  # ADD_SKILL_TAG_NEW
            {"Value": 302120180, "ParamType": 0, "Factor": 0},  # CHANGE_POS
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "[每帧 ORDER body] 2 项: 1) ADD_SKILL_TAG 320198+=5  2) CHANGE_POS"
        print('[FIX] ORDER body Params = [ADD_SKILL_TAG_NEW, CHANGE_POS]')
        break

# === Step 4: cos.P[0] = {V=302120187, PT=2 NodeRef GET output} ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120181:
        cj['Params'] = [{"Value": 302120187, "ParamType": 2, "Factor": 0}]  # GET node NodeRef
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "cos(GET_SKILL_TAG 320198 PT=2 NodeRef) → [-10000, 10000]"
        print('[FIX] MATH_COS P[0] = GET_SKILL_TAG ref (PT=2 NodeRef)')
        break

# === Step 5: Rewrite edges ===
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
    (302120170, 302120171, "0"),
    (302120174, 302120173, "0"),
    (302120175, 302120174, "3"),
    # ORDER body multi-children (dynamic port='0')
    (302120186, 302120175, "0"),  # body → ADD_SKILL_TAG_NEW
    (302120180, 302120175, "0"),  # body → CHANGE_POS
    # CHANGE_POS
    (302120177, 302120180, "1"),
    (302120184, 302120180, "2"),
    (302120176, 302120177, "0"),
    # cos / newY chain
    (302120187, 302120181, "0"),  # cos.P[0] = GET node (NEW: PT=2 NodeRef)
    (302120181, 302120182, "0"),  # cos_scaled.P[0] = cos
    (302120179, 302120184, "0"),  # newY.P[0] = GET_Y
    (302120182, 302120184, "2"),  # newY.P[2] = cos_scaled
]
data['edges'] = [make_edge(t, o, p) for (t, o, p) in edges_spec]
print(f'[FIX] edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

# Verify
data2 = json.loads(P.read_text(encoding='utf-8'))
print(f'\n[VERIFY] total RefIds = {len(data2["references"]["RefIds"])}')
for r in data2['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    ID = cj.get('ID')
    if ID == 302120175:
        print(f'  ORDER body Params: {[p["Value"] for p in cj["Params"]]}')
    elif ID == 302120181:
        print(f'  MATH_COS Params: {[(p["Value"], p["ParamType"]) for p in cj["Params"]]}')
    elif ID == 302120186:
        print(f'  ADD_SKILL_TAG Params: {[(p["Value"], p["ParamType"]) for p in cj["Params"]]}')
    elif ID == 302120187:
        print(f'  GET_SKILL_TAG Params: {[(p["Value"], p["ParamType"]) for p in cj["Params"]]}')
    elif ID == 320198:
        print(f'  SkillTag 320198 DefaultValue: {cj.get("DefaultValue")}')
