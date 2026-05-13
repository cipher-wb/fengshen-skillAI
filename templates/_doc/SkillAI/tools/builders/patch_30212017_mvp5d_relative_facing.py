"""patch_30212017_mvp5d_relative_facing.py — MVP-5d: CREATE_B 朝向 = caster.facing + 90 (相对偏移)

问题（MVP-5c 之后）:
  SkillTag 320931 写死 default=90 / 是绝对世界角
  → 主角朝右 (0°)  : CREATE_A=0°, CREATE_B=90°  → 90°夹角 ✓
  → 主角朝上 (90°) : CREATE_A=90°, CREATE_B=90° → 重叠 ✗
  → 主角朝左 (180°): CREATE_A=180°, CREATE_B=90° → 90°夹角但方向不对

修法:
  新加 GET_ENTITY_ATTR 读 caster.facing (V=4 PT=5 / attr=91)
  新加 NUM_CALC: caster_facing + 90 (3 项: GET, ADD(3), 90)
  改 CREATE_B P[1] 从 {V=320931, PT=3 SkillTag} → {V=NUM_CALC_id, PT=2 NodeRef}

数据流:
  GET_caster_facing → NUM_CALC(caster+90) → CREATE_B P[1] FACE_DIR

效果（预期）:
  CREATE_A 朝向 = caster.facing
  CREATE_B 朝向 = caster.facing + 90°
  无论主角朝哪都恒定 90° 夹角 / 不再重叠
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

alloc = IDAllocator()
get_caster_facing_id = alloc.get_next('SkillEffectConfig')
numcalc_plus90_id    = alloc.get_next('SkillEffectConfig')
print(f'New: GET_caster_facing={get_caster_facing_id} / NUM_CALC(caster+90)={numcalc_plus90_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Node 1: GET_ENTITY_ATTR caster.facing (V=4 TCPT_MAIN_SKILL_DAMAGE_PROPERTY_ORIGIN_ENTITY = caster / attr=91)
get_caster_guid = str(uuid.uuid4())
get_caster_node = {
    "rid": next_rid,
    "type": {"class": "TSET_GET_ENTITY_ATTR_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": get_caster_guid, "computeOrder": 30,
        "position": {"serializedVersion": "2", "x": 1800.0, "y": 1500.0, "width": 280.0, "height": 140.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": get_caster_facing_id, "Desc": "读 caster.facing (V=4 PT=5 释放者 / attr=91)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": get_caster_facing_id, "SkillEffectType": 32,
            "Params": [
                {"Value": 4, "ParamType": 5, "Factor": 0},   # TCPT_MAIN_SKILL_DAMAGE_PROPERTY_ORIGIN_ENTITY = caster
                {"Value": 91, "ParamType": 0, "Factor": 0},  # attr=91 FACE_DIR
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{get_caster_facing_id}",
        "SkillEffectType": 32,
    }
}

# Node 2: NUM_CALC caster_facing + 90 (3 项链式)
numcalc_guid = str(uuid.uuid4())
numcalc_node = {
    "rid": next_rid + 1,
    "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": numcalc_guid, "computeOrder": 40,
        "position": {"serializedVersion": "2", "x": 2150.0, "y": 1500.0, "width": 240.0, "height": 110.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": numcalc_plus90_id, "Desc": "caster.facing + 90 (CREATE_B 相对偏移)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": numcalc_plus90_id, "SkillEffectType": 31,
            "Params": [
                {"Value": get_caster_facing_id, "ParamType": 2, "Factor": 0},  # caster.facing NodeRef
                {"Value": 3, "ParamType": 0, "Factor": 0},                     # ADD
                {"Value": 90, "ParamType": 0, "Factor": 0},                    # 90°
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{numcalc_plus90_id}",
        "SkillEffectType": 31,
    }
}

data['references']['RefIds'].extend([get_caster_node, numcalc_node])
data['nodes'].extend([{"rid": next_rid}, {"rid": next_rid + 1}])
print('[ADD] 2 nodes (GET_caster_facing + NUM_CALC caster+90)')

# Modify CREATE_B (32900054) P[1] FACE_DIR → PT=2 NodeRef to NUM_CALC
CREATE_B_ID = 32900054
old_p1 = None
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == CREATE_B_ID and r['type']['class'] == 'TSET_CREATE_BULLET':
        old_p1 = dict(cj['Params'][1])
        cj['Params'][1] = {"Value": numcalc_plus90_id, "ParamType": 2, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"MVP-5d CREATE_B FACE_DIR = NodeRef({numcalc_plus90_id}) = caster.facing + 90°"
        print(f'[FIX] CREATE_B P[1]: {old_p1} → {{V={numcalc_plus90_id}, PT=2 NodeRef}}')
        break

# Build guid map (after new nodes added)
guid_by_id = {json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID'): r['data']['GUID']
               for r in data['references']['RefIds']
               if json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID') is not None}

# Remove old edge: SkillTag 320931 → CREATE_B P[1] (if exists)
create_b_guid = guid_by_id[CREATE_B_ID]
skilltag_320931_guid = guid_by_id.get(320931)
removed = 0
new_edges = []
for e in data['edges']:
    if (e['outputNodeGUID'] == create_b_guid and
        e['inputPortIdentifier'] == '1' and
        skilltag_320931_guid is not None and
        e['inputNodeGUID'] == skilltag_320931_guid):
        removed += 1
        continue
    new_edges.append(e)
data['edges'] = new_edges
print(f'[FIX] removed {removed} old edge(s) (SkillTag 320931 → CREATE_B P[1])')

# Add new edges
def make_edge(target_id, owner_id, outport='0'):
    return {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": guid_by_id[target_id],
        "outputNodeGUID": guid_by_id[owner_id],
        "inputFieldName": "ID", "outputFieldName": "PackedParamsOutput",
        "inputPortIdentifier": "0", "outputPortIdentifier": outport, "isVisible": True,
    }

# GET_caster_facing → NUM_CALC P[0]
data['edges'].append(make_edge(get_caster_facing_id, numcalc_plus90_id, "0"))
# NUM_CALC → CREATE_B P[1]
data['edges'].append(make_edge(numcalc_plus90_id, CREATE_B_ID, "1"))
print(f'[ADD] 2 new edges / total edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
