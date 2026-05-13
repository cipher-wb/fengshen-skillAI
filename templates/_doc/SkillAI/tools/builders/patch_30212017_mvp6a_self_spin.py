"""patch_30212017_mvp6a_self_spin.py — MVP-6a: 子弹自旋（每帧 facing += 1°）

复用废弃的 angle_acc (320198) → 改为自旋累加器 spin_angle

OnTick (32900046):
  ADD_angle (32900035)  spin_angle += 1 (原 +5，改为 +1)
  ADD_vR    (32900040)  vR_acc += 1 (不变)
  CHANGE_POS (32900049)
    ← newX (32900047) ← cos_facing (32900056)
                          ← effective_facing (new NUM_CALC) ← self.facing (32900055) + spin_angle (32900036)
    ← newY (32900050) ← sin_facing (32900057) ← same NUM_CALC

预期视觉:
  8 颗子弹各自 facing 每帧 +1° → 螺旋远离主角 (vR 也每帧加速 → 螺旋外扩)
  所有 bullet 共享相同 +1°/帧，因为是相对自身 facing 偏移 → 整体看像风车旋转
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

GET_FACING_ID    = 32900055   # GET self.facing
GET_SPIN_ANGLE   = 32900036   # GET angle_acc (复用为 spin_angle)
COS_FACING       = 32900056
SIN_FACING       = 32900057
ADD_ANGLE        = 32900035   # ADD angle_acc +5 (改为 +1)

alloc = IDAllocator()
effective_facing_id = alloc.get_next('SkillEffectConfig')
print(f'New NUM_CALC effective_facing = {effective_facing_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Build effective_facing NUM_CALC: self.facing + spin_angle (3 项)
eff_node = {
    "rid": next_rid,
    "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 75,
        "position": {"serializedVersion": "2", "x": 3450.0, "y": 50.0, "width": 240.0, "height": 110.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": effective_facing_id,
        "Desc": "effective_facing = self.facing + spin_angle (自旋驱动)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": effective_facing_id, "SkillEffectType": 31,
            "Params": [
                {"Value": GET_FACING_ID, "ParamType": 2, "Factor": 0},   # self.facing
                {"Value": 3, "ParamType": 0, "Factor": 0},                # ADD
                {"Value": GET_SPIN_ANGLE, "ParamType": 2, "Factor": 0},  # spin_angle
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{effective_facing_id}",
        "SkillEffectType": 31,
    }
}
data['references']['RefIds'].append(eff_node)
data['nodes'].append({"rid": next_rid})
print('[ADD] effective_facing NUM_CALC')

# Modify cos_facing P[0], sin_facing P[0], ADD_angle step (P[3])
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == COS_FACING:
        old = cj['Params'][0]
        cj['Params'][0] = {"Value": effective_facing_id, "ParamType": 2, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"cos(effective_facing) — driven by self.facing+spin_angle"
        print(f'[FIX] cos_facing P[0]: {old} → effective_facing NodeRef')
    elif cj.get('ID') == SIN_FACING:
        old = cj['Params'][0]
        cj['Params'][0] = {"Value": effective_facing_id, "ParamType": 2, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"sin(effective_facing) — driven by self.facing+spin_angle"
        print(f'[FIX] sin_facing P[0]: {old} → effective_facing NodeRef')
    elif cj.get('ID') == ADD_ANGLE:
        old_step = cj['Params'][3]['Value']
        cj['Params'][3]['Value'] = 1
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "OnTick: spin_angle += 1 (自旋 / 60°/秒)"
        print(f'[FIX] ADD_angle step: {old_step} → 1')

# Build guid map
guid_by_id = {json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID'): r['data']['GUID']
               for r in data['references']['RefIds']
               if json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID') is not None}

# Remove old edges: GET_facing → cos_facing/sin_facing (port 0)
cos_g = guid_by_id[COS_FACING]
sin_g = guid_by_id[SIN_FACING]
get_facing_g = guid_by_id[GET_FACING_ID]
removed = 0
new_edges = []
for e in data['edges']:
    if (e['inputPortIdentifier'] == '0' and
        e['inputNodeGUID'] == get_facing_g and
        e['outputNodeGUID'] in (cos_g, sin_g)):
        removed += 1
        continue
    new_edges.append(e)
data['edges'] = new_edges
print(f'[FIX] removed {removed} old edges (GET_facing → cos/sin P[0])')

# Add new edges
def make_edge(target_id, owner_id, outport='0'):
    return {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": guid_by_id[target_id],
        "outputNodeGUID": guid_by_id[owner_id],
        "inputFieldName": "ID", "outputFieldName": "PackedParamsOutput",
        "inputPortIdentifier": "0", "outputPortIdentifier": outport, "isVisible": True,
    }

# GET_facing → effective_facing P[0]
data['edges'].append(make_edge(GET_FACING_ID, effective_facing_id, "0"))
# GET_spin_angle → effective_facing P[2]
data['edges'].append(make_edge(GET_SPIN_ANGLE, effective_facing_id, "2"))
# effective_facing → cos_facing P[0]
data['edges'].append(make_edge(effective_facing_id, COS_FACING, "0"))
# effective_facing → sin_facing P[0]
data['edges'].append(make_edge(effective_facing_id, SIN_FACING, "0"))
print(f'[ADD] 4 new edges / total = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
