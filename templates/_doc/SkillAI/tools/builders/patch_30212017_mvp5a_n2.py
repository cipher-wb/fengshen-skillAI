"""patch_30212017_mvp5a_n2.py — MVP-5a: spawn N=2 子弹

新加 1 个 CREATE_BULLET 节点 (同 BulletConfig / 同 AfterBorn 链)
修改 ROOT_ORDER Params 加 4 项: [reset_angle, reset_vR, CREATE_A, CREATE_B]

预期视觉:
- 如果 SkillTag per-caster 共享 → 两颗共享 angle/vR slot / 每帧 ADD 触发 2 次 / 累加翻倍 / X+Y 行为异常
- 如果 SkillTag per-bullet → 两颗各自累加 / 完全同步 / 视觉重叠 = 1 颗

通过 log 判断: 看 32900035 (ADD_angle) 在一帧内执行次数 + GET_angle iResult 增长速度
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

alloc = IDAllocator()  # 不 exclude / 看到当前文件已用 ID
create_b_id = alloc.get_next('SkillEffectConfig')
print(f'New CREATE_B id={create_b_id}')

# Find existing CREATE_A (32900045) as template
create_a = None
root_order = None  # 32900053
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson', '') or '{}')
    if cj.get('ID') == 32900045 and r['type']['class'] == 'TSET_CREATE_BULLET':
        create_a = r
    elif cj.get('ID') == 32900053:
        root_order = r

if not create_a or not root_order:
    raise RuntimeError("CREATE_A 32900045 or ROOT_ORDER 32900053 not found")

# Clone CREATE_A → CREATE_B (same Params / new GUID + ID)
create_a_cj = json.loads(create_a['data']['ConfigJson'])
create_b_cj = dict(create_a_cj)
create_b_cj['ID'] = create_b_id
create_b_cj['Params'] = create_a_cj['Params']  # exactly same Params (same BulletConfig)

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1
create_b_node = {
    "rid": next_rid,
    "type": dict(create_a['type']),
    "data": {
        "GUID": str(uuid.uuid4()),
        "computeOrder": create_a['data']['computeOrder'] + 1,
        "position": {"serializedVersion": "2", "x": float(create_a['data']['position']['x'] + 350),
                     "y": float(create_a['data']['position']['y'] + 100), "width": 280.0, "height": 200.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": create_b_id, "Desc": f"MVP-5a CREATE_B (spawn 第 2 颗 / 同 BulletConfig 320258)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": create_a['data'].get('TableTash', '0CFA05568A66FEA1DF3BA6FE40DB7080'),
        "ConfigJson": json.dumps(create_b_cj, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{create_b_id}",
        "SkillEffectType": 8,  # CREATE_BULLET
    }
}
data['references']['RefIds'].append(create_b_node)
data['nodes'].append({"rid": next_rid})
print(f'[ADD] CREATE_B node rid={next_rid} ID={create_b_id}')

# Modify ROOT_ORDER Params to include CREATE_B (after CREATE_A)
root_cj = json.loads(root_order['data']['ConfigJson'])
old_params = root_cj['Params']
# Insert CREATE_B after CREATE_A in the list (last position currently is CREATE_A = 32900045)
new_params = old_params + [{"Value": create_b_id, "ParamType": 0, "Factor": 0}]
root_cj['Params'] = new_params
root_order['data']['ConfigJson'] = json.dumps(root_cj, ensure_ascii=False)
root_order['data']['Desc'] = "[MVP-5a] OnSkillStart ROOT = [reset_angle, reset_vR, CREATE_A, CREATE_B]"
print(f'[FIX] ROOT_ORDER Params: 3 → {len(new_params)} items')

# Add edge: ROOT_ORDER → CREATE_B (dynamic port='0')
guid_by_id = {json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID'): r['data']['GUID']
               for r in data['references']['RefIds']
               if json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID') is not None}

data['edges'].append({
    "GUID": str(uuid.uuid4()),
    "inputNodeGUID": guid_by_id[create_b_id],
    "outputNodeGUID": guid_by_id[32900053],
    "inputFieldName": "ID", "outputFieldName": "PackedParamsOutput",
    "inputPortIdentifier": "0", "outputPortIdentifier": "0", "isVisible": True,
})
print(f'[FIX] edges += 1 = {len(data["edges"])}')

# Adjust positions for ORDER sort: ROOT children y ascending
# Existing: reset_angle (y=100), reset_vR (y=300), CREATE_A
# Set CREATE_A y=500, CREATE_B y=700 (sort: angle → vR → A → B)
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson', '') or '{}')
    ID = cj.get('ID')
    if ID == 32900045:  # CREATE_A
        r['data']['position']['y'] = 500.0
    elif ID == create_b_id:  # CREATE_B
        r['data']['position']['y'] = 700.0
print('[FIX] Positions: CREATE_A y=500 / CREATE_B y=700 (ORDER sort)')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
