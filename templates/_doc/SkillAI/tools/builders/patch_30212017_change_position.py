"""patch_30212017_change_position.py

3 个修复:
1. 删 MODIFY (302120178) — modify attr=59 不能驱动 entity transform
2. 加 GET_Y (302120179) + CHANGE_POSITION (302120180) — 用 30212010 模式
3. ORDER body Params 改成 [CHANGE_POSITION] 仅 1 项 — 解决"参数列表 vs 连线"不一致报错
"""
import json, uuid
from pathlib import Path

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

get_y_guid = str(uuid.uuid4())
change_pos_guid = str(uuid.uuid4())

get_y_node = {
    "rid": 1010,
    "type": {"class": "TSET_GET_ENTITY_ATTR_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": get_y_guid, "computeOrder": 100,
        "position": {"serializedVersion":"2", "x": 3000.0, "y": 1100.0, "width":200.0, "height":80.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 302120179, "Desc": "取子弹自身 PosY (浮动节点 / 被 CHANGE_POS P[2] 引用)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({"ID":302120179, "SkillEffectType":32,
            "Params":[
                {"Value":1,"ParamType":5,"Factor":0},
                {"Value":60,"ParamType":0,"Factor":0},
            ]}, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_302120179",
        "SkillEffectType": 32,
    }
}

change_pos_node = {
    "rid": 1011,
    "type": {"class": "TSET_CHANGE_ENTITY_POSITION", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": change_pos_guid, "computeOrder": 110,
        "position": {"serializedVersion":"2", "x": 3300.0, "y": 1300.0, "width":280.0, "height":140.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 302120180,
        "Desc": "改子弹自身位置 (newX, currentY, mode=2) 仿 30212010 rid=1125 模式",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({"ID":302120180, "SkillEffectType":22,
            "Params":[
                {"Value":1,"ParamType":5,"Factor":0},
                {"Value":302120177,"ParamType":2,"Factor":0},
                {"Value":302120179,"ParamType":2,"Factor":0},
                {"Value":2,"ParamType":0,"Factor":0},
                {"Value":0,"ParamType":0,"Factor":0},
            ]}, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_302120180",
        "SkillEffectType": 22,
    }
}

data['references']['RefIds'] = [r for r in data['references']['RefIds'] if r['rid'] != 1009]
data['nodes'] = [n for n in data['nodes'] if n.get('rid') != 1009]
data['references']['RefIds'].append(get_y_node)
data['references']['RefIds'].append(change_pos_node)
data['nodes'].append({"rid": 1010})
data['nodes'].append({"rid": 1011})

for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120175:
        cj['Params'] = [{"Value": 302120180, "ParamType": 0, "Factor": 0}]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "[每帧 ORDER body] 仅 1 项 = CHANGE_POSITION 302120180"
        print('[FIX] ORDER body Params = [CHANGE_POSITION] only')
        break

guid_by_id = {}
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') is not None:
        guid_by_id[cj['ID']] = r['data']['GUID']
    else:
        guid_by_id[r['data'].get('ID')] = r['data']['GUID']

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
    (302120180, 302120175, "0"),
    (302120177, 302120180, "1"),
    (302120179, 302120180, "2"),
    (302120176, 302120177, "0"),
]
data['edges'] = [make_edge(t, o, port) for (t, o, port) in edges_spec]
print(f'[FIX] edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print('[OK] saved')
