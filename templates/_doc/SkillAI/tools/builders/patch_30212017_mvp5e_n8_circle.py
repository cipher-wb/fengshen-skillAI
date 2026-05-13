"""patch_30212017_mvp5e_n8_circle.py — MVP-5e: N=8 圆周辐射

复用 MVP-5d 验证过的模式（PT=2 NodeRef → NUM_CALC(caster_facing + offset)）。

保留:
  CREATE_A (32900045)  offset=0   (走 PT=1 attr=91 = caster.facing 直读)
  CREATE_B (32900054)  offset=90  (走 NUM_CALC 32900059 = caster_facing + 90)
  GET_caster_facing (32900058) — N=8 共用

新加 6 个 NUM_CALC + 6 个 CREATE_BULLET:
  Bullet C  offset=45
  Bullet D  offset=135
  Bullet E  offset=180
  Bullet F  offset=225
  Bullet G  offset=270
  Bullet H  offset=315

ROOT_ORDER 32900053 Params 从 4 项 → 10 项:
  [reset_angle, reset_vR, A, B, C, D, E, F, G, H]

⚠ 注意角度环绕 (caster_facing + 315 可能 > 360 / engine 应该自动处理 MATH_COS/SIN 输入)
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

GET_CASTER_FACING_ID = 32900058
ROOT_ORDER_ID = 32900053
BULLET_CONFIG_ID = 320258

# Allocate IDs
alloc = IDAllocator()
new_offsets = [45, 135, 180, 225, 270, 315]
new_nodes = []  # [(offset, numcalc_id, create_id), ...]
for off in new_offsets:
    nc_id = alloc.get_next('SkillEffectConfig')
    cb_id = alloc.get_next('SkillEffectConfig')
    new_nodes.append((off, nc_id, cb_id))
    print(f'Bullet @+{off}°: NUM_CALC={nc_id} / CREATE_BULLET={cb_id}')

# Find CREATE_B (32900054) as template
create_b_template = None
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == 32900054 and r['type']['class'] == 'TSET_CREATE_BULLET':
        create_b_template = r
        break
assert create_b_template, 'CREATE_B 32900054 not found'

create_b_cj = json.loads(create_b_template['data']['ConfigJson'])
next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Build new nodes
added = []
for i, (off, nc_id, cb_id) in enumerate(new_nodes):
    # NUM_CALC: caster_facing + off
    nc_node = {
        "rid": next_rid + i * 2,
        "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 41 + i,
            "position": {"serializedVersion": "2", "x": 2150.0, "y": 1700.0 + i * 200, "width": 240.0, "height": 110.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": nc_id, "Desc": f"caster.facing + {off}° (Bullet @+{off})",
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps({
                "ID": nc_id, "SkillEffectType": 31,
                "Params": [
                    {"Value": GET_CASTER_FACING_ID, "ParamType": 2, "Factor": 0},
                    {"Value": 3, "ParamType": 0, "Factor": 0},
                    {"Value": off, "ParamType": 0, "Factor": 0},
                ],
            }, ensure_ascii=False),
            "Config2ID": f"SkillEffectConfig_{nc_id}",
            "SkillEffectType": 31,
        }
    }

    # CREATE_BULLET clone of CREATE_B
    cb_cj = dict(create_b_cj)
    cb_cj['ID'] = cb_id
    cb_cj['Params'] = [dict(p) for p in create_b_cj['Params']]
    cb_cj['Params'][1] = {"Value": nc_id, "ParamType": 2, "Factor": 0}
    cb_node = {
        "rid": next_rid + i * 2 + 1,
        "type": {"class": "TSET_CREATE_BULLET", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": create_b_template['data']['computeOrder'] + 1 + i,
            "position": {"serializedVersion": "2", "x": -200.0 + i * 350, "y": 900.0 + (i % 2) * 200, "width": 280.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": cb_id, "Desc": f"MVP-5e Bullet @+{off}° (PT=2 NodeRef→NUM_CALC {nc_id})",
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": create_b_template['data'].get('TableTash', '0CFA05568A66FEA1DF3BA6FE40DB7080'),
            "ConfigJson": json.dumps(cb_cj, ensure_ascii=False),
            "Config2ID": f"SkillEffectConfig_{cb_id}",
            "SkillEffectType": 8,
        }
    }

    added.extend([nc_node, cb_node])
    data['references']['RefIds'].extend([nc_node, cb_node])
    data['nodes'].extend([{"rid": nc_node['rid']}, {"rid": cb_node['rid']}])

print(f'[ADD] {len(new_nodes)*2} nodes ({len(new_nodes)} NUM_CALC + {len(new_nodes)} CREATE_BULLET)')

# Append 6 new CREATE_* to ROOT_ORDER Params
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == ROOT_ORDER_ID:
        old_params = cj['Params']
        new_params = old_params + [{"Value": cb_id, "ParamType": 0, "Factor": 0} for _, _, cb_id in new_nodes]
        cj['Params'] = new_params
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "[MVP-5e] ROOT = [reset_angle, reset_vR, A, B, C, D, E, F, G, H] (N=8)"
        print(f'[FIX] ROOT_ORDER Params: {len(old_params)} → {len(new_params)} items')
        break

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

# Add edges
edges_added = 0
for off, nc_id, cb_id in new_nodes:
    # GET_caster_facing → NUM_CALC P[0]
    data['edges'].append(make_edge(GET_CASTER_FACING_ID, nc_id, "0"))
    # NUM_CALC → CREATE_BULLET P[1]
    data['edges'].append(make_edge(nc_id, cb_id, "1"))
    # ROOT_ORDER → CREATE_BULLET (dynamic port='0')
    data['edges'].append(make_edge(cb_id, ROOT_ORDER_ID, "0"))
    edges_added += 3

print(f'[ADD] {edges_added} edges / total = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
