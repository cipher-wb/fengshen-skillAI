"""patch_30212017_mvp5c_facing_drive.py — MVP-5c: 飞行方向跟随 facing

新加 3 节点:
- GET_facing: GET_ENTITY_ATTR self.attr=91
- MATH_COS(facing): cos(self.facing)
- MATH_SIN(facing): sin(self.facing)

改造 OnTick 公式（newX/newY 链式 7 项）:
  newX = ((cos_facing * vR_acc) / 10000) + self.X
  newY = ((sin_facing * vR_acc) / 10000) + self.Y

⚠ 暂时移除 cos_angle 振荡（newY 之前的 cos(angle)/100 部分）
  保持 MVP-5c 简单 / 让 2 颗朝不同方向飞先验证
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

alloc = IDAllocator()
get_facing_id = alloc.get_next('SkillEffectConfig')
cos_facing_id = alloc.get_next('SkillEffectConfig')
sin_facing_id = alloc.get_next('SkillEffectConfig')
print(f'New: GET_facing={get_facing_id} / COS_facing={cos_facing_id} / SIN_facing={sin_facing_id}')

# Find anchor node guid (any existing one — for position offset)
next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Node 1: GET_ENTITY_ATTR self.facing
get_facing_guid = str(uuid.uuid4())
get_facing_node = {
    "rid": next_rid,
    "type": {"class": "TSET_GET_ENTITY_ATTR_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": get_facing_guid, "computeOrder": 72,
        "position": {"serializedVersion": "2", "x": 3300.0, "y": 100.0, "width": 280.0, "height": 140.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": get_facing_id, "Desc": "读 self.attr=91 (bullet 自身 facing / birth heading)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": get_facing_id, "SkillEffectType": 32,
            "Params": [
                {"Value": 1, "ParamType": 5, "Factor": 0},
                {"Value": 91, "ParamType": 0, "Factor": 0},
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{get_facing_id}",
        "SkillEffectType": 32,
    }
}

# Node 2: COS(facing)
cos_facing_guid = str(uuid.uuid4())
cos_facing_node = {
    "rid": next_rid+1,
    "type": {"class": "TSET_MATH_COS", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": cos_facing_guid, "computeOrder": 82,
        "position": {"serializedVersion": "2", "x": 3600.0, "y": 100.0, "width": 200.0, "height": 80.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": cos_facing_id, "Desc": "cos(self.facing) → [-10000, 10000]",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": cos_facing_id, "SkillEffectType": 51,
            "Params": [{"Value": get_facing_id, "ParamType": 2, "Factor": 0}],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{cos_facing_id}",
        "SkillEffectType": 51,
    }
}

# Node 3: SIN(facing)
sin_facing_guid = str(uuid.uuid4())
sin_facing_node = {
    "rid": next_rid+2,
    "type": {"class": "TSET_MATH_SIN", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": sin_facing_guid, "computeOrder": 83,
        "position": {"serializedVersion": "2", "x": 3600.0, "y": 250.0, "width": 200.0, "height": 80.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": sin_facing_id, "Desc": "sin(self.facing) → [-10000, 10000]",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": sin_facing_id, "SkillEffectType": 50,
            "Params": [{"Value": get_facing_id, "ParamType": 2, "Factor": 0}],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{sin_facing_id}",
        "SkillEffectType": 50,
    }
}

data['references']['RefIds'].extend([get_facing_node, cos_facing_node, sin_facing_node])
data['nodes'].extend([{"rid": next_rid}, {"rid": next_rid+1}, {"rid": next_rid+2}])
print('[ADD] 3 nodes')

# Modify newX NUM_CALC (32900047) to chain: ((cos*vR)/10000) + GET_X (7 items)
GET_VR_ID = 32900041
GET_X_ID = 32900042
GET_Y_ID = 32900048
NEW_X_NUM_CALC = 32900047
NEW_Y_NUM_CALC = 32900050

for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == NEW_X_NUM_CALC:
        cj['Params'] = [
            {"Value": cos_facing_id, "ParamType": 2, "Factor": 0},   # cos(facing)
            {"Value": 5, "ParamType": 0, "Factor": 0},                # MUL
            {"Value": GET_VR_ID, "ParamType": 2, "Factor": 0},        # vR
            {"Value": 6, "ParamType": 0, "Factor": 0},                # DIV
            {"Value": 10000, "ParamType": 0, "Factor": 0},            # 10000
            {"Value": 3, "ParamType": 0, "Factor": 0},                # ADD
            {"Value": GET_X_ID, "ParamType": 2, "Factor": 0},         # GET_X
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "newX = ((cos_facing*vR)/10000) + GET_X (链式 7 项 / 飞行方向跟 facing)"
        print(f'[FIX] newX NUM_CALC {NEW_X_NUM_CALC} → 7 项链式')
    elif cj.get('ID') == NEW_Y_NUM_CALC:
        cj['Params'] = [
            {"Value": sin_facing_id, "ParamType": 2, "Factor": 0},
            {"Value": 5, "ParamType": 0, "Factor": 0},
            {"Value": GET_VR_ID, "ParamType": 2, "Factor": 0},
            {"Value": 6, "ParamType": 0, "Factor": 0},
            {"Value": 10000, "ParamType": 0, "Factor": 0},
            {"Value": 3, "ParamType": 0, "Factor": 0},
            {"Value": GET_Y_ID, "ParamType": 2, "Factor": 0},
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "newY = ((sin_facing*vR)/10000) + GET_Y (链式 7 项 / 飞行方向跟 facing)"
        print(f'[FIX] newY NUM_CALC {NEW_Y_NUM_CALC} → 7 项链式（暂去 cos_angle 振荡）')

# Build guid map
guid_by_id = {json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID'): r['data']['GUID']
               for r in data['references']['RefIds']
               if json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID') is not None}

def make_edge(target_id, owner_id, outport='0'):
    return {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": guid_by_id[target_id],
        "outputNodeGUID": guid_by_id[owner_id],
        "inputFieldName": "ID", "outputFieldName": "PackedParamsOutput",
        "inputPortIdentifier": "0", "outputPortIdentifier": outport, "isVisible": True,
    }

# Remove old edges referencing newX (32900047) and newY (32900050) inputs that are now obsolete
def edge_matches(e, target_id_set, owner_id):
    return e['inputNodeGUID'] in {guid_by_id[i] for i in target_id_set} and e['outputNodeGUID'] == guid_by_id[owner_id]

owner_guids_to_clean = {guid_by_id[NEW_X_NUM_CALC], guid_by_id[NEW_Y_NUM_CALC]}
data['edges'] = [e for e in data['edges'] if e['outputNodeGUID'] not in owner_guids_to_clean]

# Add new edges for newX (cos_facing → GET_VR → GET_X) and newY (sin_facing → GET_VR → GET_Y) + cos/sin → GET_facing
new_edges = [
    (get_facing_id, cos_facing_id, "0"),
    (get_facing_id, sin_facing_id, "0"),
    (cos_facing_id, NEW_X_NUM_CALC, "0"),
    (GET_VR_ID, NEW_X_NUM_CALC, "2"),
    (GET_X_ID, NEW_X_NUM_CALC, "6"),
    (sin_facing_id, NEW_Y_NUM_CALC, "0"),
    (GET_VR_ID, NEW_Y_NUM_CALC, "2"),
    (GET_Y_ID, NEW_Y_NUM_CALC, "6"),
]
for t, o, p in new_edges:
    data['edges'].append(make_edge(t, o, p))
print(f'[FIX] edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
