"""patch_30212017_mvp6a_fix_visual_orient.py — MVP-6a 修复: 叶尖朝飞行方向

问题:
  叶子 prefab 局部 Z+ 是 "tip" 方向 / 引擎 facing 0° 对应世界 +X
  → 视觉旋转 (rotation.y = -facing) 让 tip 永远比 flight 方向落后 90°
  用户实测: 8 颗叶子尖尖朝切向 / 不朝径向飞行方向

修法（解耦视觉 vs 飞行）:
  CREATE_BULLET P[1] (= 出生 entity.faceDir = 视觉旋转) = (cf + offset_i - 90)
  effective_facing (= cos/sin 用的 flight 角)  = self.facing + spin_angle + 90

  净效果:
    视觉 tip 方向 = cf + offset_i - 90 + 90 = cf + offset_i (径向 / 用户期望)
    飞行方向    = cf + offset_i + spin (径向 + 旋转 / 跟之前一样)
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

GET_CASTER_FACING = 32900058
EFF_FACING = 32900072
CREATE_A_ID = 32900045
# All NUM_CALC nodes that compute (cf + offset) for CREATE_B..H
NUM_CALC_NODES = {
    32900059: 90,
    32900060: 45,
    32900062: 135,
    32900064: 180,
    32900066: 225,
    32900068: 270,
    32900070: 315,
}

alloc = IDAllocator()
new_num_calc_a = alloc.get_next('SkillEffectConfig')
print(f'New NUM_CALC for CREATE_A: {new_num_calc_a} (= caster_facing - 90)')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# 1. Add NUM_CALC for CREATE_A: caster_facing - 90 (3-item: GET_caster, ADD(3), -90)
new_a_node = {
    "rid": next_rid,
    "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 76,
        "position": {"serializedVersion": "2", "x": 2150.0, "y": 1300.0, "width": 240.0, "height": 110.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": new_num_calc_a,
        "Desc": "caster.facing - 90 (CREATE_A visual / 抵消叶尖 prefab 局部 Z+ 偏移)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": new_num_calc_a, "SkillEffectType": 31,
            "Params": [
                {"Value": GET_CASTER_FACING, "ParamType": 2, "Factor": 0},
                {"Value": 3, "ParamType": 0, "Factor": 0},      # ADD
                {"Value": -90, "ParamType": 0, "Factor": 0},    # -90°
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{new_num_calc_a}",
        "SkillEffectType": 31,
    }
}
data['references']['RefIds'].append(new_a_node)
data['nodes'].append({"rid": next_rid})
print(f'[ADD] NUM_CALC {new_num_calc_a} (caster_facing - 90)')

# 2. Change CREATE_A P[1] from {V=91, PT=1} → {V=new_num_calc_a, PT=2}
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == CREATE_A_ID and r['type']['class'] == 'TSET_CREATE_BULLET':
        old = dict(cj['Params'][1])
        cj['Params'][1] = {"Value": new_num_calc_a, "ParamType": 2, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"MVP-6a-fix CREATE_A FACE_DIR = NodeRef({new_num_calc_a}) = caster_facing - 90"
        print(f'[FIX] CREATE_A P[1]: {old} → {{V={new_num_calc_a}, PT=2}}')
        break

# 3. Modify 7 existing NUM_CALC nodes (subtract 90 from offset)
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    nid = cj.get('ID')
    if nid in NUM_CALC_NODES:
        old_off = NUM_CALC_NODES[nid]
        new_off = old_off - 90
        cj['Params'][2]['Value'] = new_off
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"caster.facing + {new_off}° (Bullet visual, 飞行实为 cf+{old_off}°)"
        print(f'[FIX] NUM_CALC {nid}: cf+{old_off} → cf+{new_off}')

# 4. Modify effective_facing 32900072 from 3 items to 5 items: add +90 at end
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == EFF_FACING:
        cj['Params'] = [
            {"Value": 32900055, "ParamType": 2, "Factor": 0},  # GET self.facing
            {"Value": 3, "ParamType": 0, "Factor": 0},          # ADD
            {"Value": 32900036, "ParamType": 2, "Factor": 0},  # GET spin_angle
            {"Value": 3, "ParamType": 0, "Factor": 0},          # ADD
            {"Value": 90, "ParamType": 0, "Factor": 0},         # +90 视觉补偿
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "effective_facing = self.facing + spin_angle + 90 (+90 = 视觉偏移补偿)"
        print(f'[FIX] effective_facing 32900072: 3 items → 5 items (+90 at tail)')
        break

# 5. Build edges
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

# GET_caster_facing → new NUM_CALC (port 0)
data['edges'].append(make_edge(GET_CASTER_FACING, new_num_calc_a, "0"))
# new NUM_CALC → CREATE_A P[1]
data['edges'].append(make_edge(new_num_calc_a, CREATE_A_ID, "1"))
print(f'[ADD] 2 new edges / total = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
