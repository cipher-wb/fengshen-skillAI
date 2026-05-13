"""patch_30212017_mvp6a_attr91_spin.py — 用 MODIFY_ENTITY_ATTR_VALUE 驱动 attr=91 自旋

发现:
  BattleBulletAttrCollectComp.cs:91-93: case FACE_DIR → locateComp.LogicFace = newValue
  BattleLocateComp.cs SetEngineFace(): 每帧 ViewFace lerp 到 LogicFace + SyncRotation()
  → MODIFY attr 91 真的会驱动视觉旋转每一帧

替换路径:
  之前: ADD_SKILL_TAG 320198 (spin_angle) + effective_facing = self.facing + spin - 90
  现在: MODIFY attr=91 self.facing = NUM_CALC(self.facing - 1) + effective_facing = self.facing - 90
        视觉 + 飞行方向 由 self.facing 驱动 / 始终同步

OnTick 32900046 改造:
  Params: [ADD_angle, ADD_vR, CHANGE_POS] → [MODIFY_facing, ADD_vR, CHANGE_POS]
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

GET_FACING_ID = 32900055
ADD_ANGLE_ID  = 32900035   # 旧 ADD_SKILL_TAG，将被踢出 ORDER
EFF_FACING    = 32900072
ORDER_ID      = 32900046

alloc = IDAllocator()
new_numcalc_id = alloc.get_next('SkillEffectConfig')
new_modify_id  = alloc.get_next('SkillEffectConfig')
print(f'New: NUM_CALC self.facing-1 = {new_numcalc_id} / MODIFY_attr91 = {new_modify_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Node 1: NUM_CALC self.facing - 1 (3 items: GET_facing, ADD(3), -1)
numcalc_node = {
    "rid": next_rid,
    "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 70,
        "position": {"serializedVersion": "2", "x": 3450.0, "y": -150.0, "width": 240.0, "height": 110.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": new_numcalc_id,
        "Desc": "self.facing - 1 (每帧旋转步长 / 驱动 attr=91)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": new_numcalc_id, "SkillEffectType": 31,
            "Params": [
                {"Value": GET_FACING_ID, "ParamType": 2, "Factor": 0},
                {"Value": 3, "ParamType": 0, "Factor": 0},      # ADD
                {"Value": -1, "ParamType": 0, "Factor": 0},     # -1°
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{new_numcalc_id}",
        "SkillEffectType": 31,
    }
}

# Node 2: MODIFY_ENTITY_ATTR_VALUE  P=[self V=1 PT=5, attr V=91 PT=0, new_numcalc NodeRef PT=2]
modify_node = {
    "rid": next_rid + 1,
    "type": {"class": "TSET_MODIFY_ENTITY_ATTR_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 71,
        "position": {"serializedVersion": "2", "x": 3450.0, "y": -300.0, "width": 280.0, "height": 140.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": new_modify_id,
        "Desc": "MODIFY self.facing = self.facing - 1 (驱动视觉 + 飞行同步旋转)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": new_modify_id, "SkillEffectType": 12,
            "Params": [
                {"Value": 1, "ParamType": 5, "Factor": 0},      # self (MAIN_ENTITY)
                {"Value": 91, "ParamType": 0, "Factor": 0},     # attr ID = 91 FACE_DIR
                {"Value": new_numcalc_id, "ParamType": 2, "Factor": 0},  # value = NodeRef
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{new_modify_id}",
        "SkillEffectType": 12,
    }
}

data['references']['RefIds'].extend([numcalc_node, modify_node])
data['nodes'].extend([{"rid": next_rid}, {"rid": next_rid + 1}])
print('[ADD] 2 nodes')

# Replace ADD_angle in ORDER 32900046 P[0] with new MODIFY
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == ORDER_ID:
        old_p0 = cj['Params'][0]['Value']
        cj['Params'][0]['Value'] = new_modify_id
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "[每帧 OnTick] 3 项: MODIFY_facing / ADD_vR / CHANGE_POS"
        print(f'[FIX] ORDER 32900046 P[0]: {old_p0} (ADD_angle) → {new_modify_id} (MODIFY_facing)')
        break

# Restore effective_facing 32900072 to 3 items (remove spin_angle term)
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == EFF_FACING:
        cj['Params'] = [
            {"Value": GET_FACING_ID, "ParamType": 2, "Factor": 0},
            {"Value": 3, "ParamType": 0, "Factor": 0},
            {"Value": -90, "ParamType": 0, "Factor": 0},
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "effective_facing = self.facing - 90 (自旋已由 MODIFY 驱动 self.facing)"
        print('[FIX] effective_facing: 5 items → 3 items (remove spin_angle, just self.facing - 90)')
        break

# Edges
guid_by_id = {json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID'): r['data']['GUID']
               for r in data['references']['RefIds']
               if json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID') is not None}

# Remove old edges:
#   1) ADD_angle 32900035 → ORDER 32900046 (port 0)
#   2) GET_spin_angle 32900036 → effective_facing 32900072 (port 2 — spin_angle term removed)
add_angle_g = guid_by_id[ADD_ANGLE_ID]
order_g = guid_by_id[ORDER_ID]
get_spin_g = guid_by_id.get(32900036)
eff_g = guid_by_id[EFF_FACING]
removed = 0
new_edges = []
for e in data['edges']:
    if e['inputNodeGUID'] == add_angle_g and e['outputNodeGUID'] == order_g and e['inputPortIdentifier'] == '0':
        removed += 1
        continue
    if get_spin_g and e['inputNodeGUID'] == get_spin_g and e['outputNodeGUID'] == eff_g and e['inputPortIdentifier'] == '2':
        removed += 1
        continue
    new_edges.append(e)
data['edges'] = new_edges
print(f'[FIX] removed {removed} old edges')

# Add new edges
def make_edge(target_id, owner_id, outport='0'):
    return {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": guid_by_id[target_id],
        "outputNodeGUID": guid_by_id[owner_id],
        "inputFieldName": "ID", "outputFieldName": "PackedParamsOutput",
        "inputPortIdentifier": "0", "outputPortIdentifier": outport, "isVisible": True,
    }

# GET_facing → new NUM_CALC P[0]
data['edges'].append(make_edge(GET_FACING_ID, new_numcalc_id, "0"))
# NUM_CALC → MODIFY P[2]
data['edges'].append(make_edge(new_numcalc_id, new_modify_id, "2"))
# MODIFY → ORDER P[0] (replacing old ADD_angle)
data['edges'].append(make_edge(new_modify_id, ORDER_ID, "0"))
print(f'[ADD] 3 new edges / total = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
