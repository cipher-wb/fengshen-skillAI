"""patch_30212017_add_reset.py — 加 OnSkillStart 重置节点

问题: SkillTag entity slot 跨次释放不重置 / vR_acc 累到 1000+ / 飞太远

修法: 在 OnSkillStart 链最前面加 2 个 MODIFY_SKILL_TAG (重置 angle + vR) + 1 个 ORDER 包装
新 SkillConfig.SkillEffectExecuteInfo = 新 ORDER → [MODIFY_angle=0, MODIFY_vR=5, CREATE_BULLET]

用 id_allocator 自动分配新 ID (ip=32 段位)
仿 30212010 ID=66001776 真实 MODIFY_SKILL_TAG 模式: P[3]={V=常量, PT=0} 直接设值
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

alloc = IDAllocator()  # do NOT exclude target file - we want to see its existing IDs

# Allocate 3 new IDs in ip=32 segment
modify_angle_id = alloc.get_next('SkillEffectConfig')
modify_vr_id    = alloc.get_next('SkillEffectConfig')
root_order_id   = alloc.get_next('SkillEffectConfig')
print(f'New IDs: MODIFY_angle={modify_angle_id} / MODIFY_vR={modify_vr_id} / ROOT_ORDER={root_order_id}')

# Build 3 new node entries (仿用户 SkillEditor 已加的 SkillEffect 节点 schema)
def make_node(rid, ID, cls, desc, params, computeOrder=20, pos=(0, 0)):
    return {
        "rid": rid,
        "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": computeOrder,
            "position": {"serializedVersion": "2", "x": float(pos[0]), "y": float(pos[1]), "width": 280.0, "height": 120.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps({
                "ID": ID,
                "SkillEffectType": 46 if cls == 'TSET_MODIFY_SKILL_TAG_VALUE' else 1,  # 46=MODIFY / 1=ORDER
                "Params": params,
            }, ensure_ascii=False),
            "Config2ID": f"SkillEffectConfig_{ID}",
            "SkillEffectType": 46 if cls == 'TSET_MODIFY_SKILL_TAG_VALUE' else 1,
        }
    }

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Node 1: MODIFY angle SkillTag 320198 = 0
modify_angle = make_node(
    rid=next_rid, ID=modify_angle_id, cls='TSET_MODIFY_SKILL_TAG_VALUE',
    desc='OnSkillStart: 重置 angle SkillTag 320198 = 0',
    params=[
        {"Value": 4, "ParamType": 5, "Factor": 0},
        {"Value": 41, "ParamType": 5, "Factor": 0},
        {"Value": 320198, "ParamType": 0, "Factor": 0},
        {"Value": 0, "ParamType": 0, "Factor": 0},   # 设值 = 0
        {"Value": 1, "ParamType": 0, "Factor": 0},
    ],
    pos=(0, 100),
)
# Node 2: MODIFY vR_acc SkillTag 320199 = 5
modify_vr = make_node(
    rid=next_rid+1, ID=modify_vr_id, cls='TSET_MODIFY_SKILL_TAG_VALUE',
    desc='OnSkillStart: 重置 vR_acc SkillTag 320199 = 5',
    params=[
        {"Value": 4, "ParamType": 5, "Factor": 0},
        {"Value": 41, "ParamType": 5, "Factor": 0},
        {"Value": 320199, "ParamType": 0, "Factor": 0},
        {"Value": 5, "ParamType": 0, "Factor": 0},   # 设值 = 5
        {"Value": 1, "ParamType": 0, "Factor": 0},
    ],
    pos=(0, 300),
)

# Find current SkillConfig & CREATE_BULLET to get IDs
skill_config_node = None
create_bullet_id = None
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson', '') or '{}')
    if r['type']['class'] == 'SkillConfigNode' and cj.get('ID') == 30212017:
        skill_config_node = r
    elif r['type']['class'] == 'TSET_CREATE_BULLET':
        create_bullet_id = cj.get('ID')

if not skill_config_node or not create_bullet_id:
    raise RuntimeError("Cannot find SkillConfig or CREATE_BULLET")
print(f'Found CREATE_BULLET id={create_bullet_id}')

# Node 3: ROOT_ORDER = [MODIFY_angle, MODIFY_vR, CREATE_BULLET]
root_order = make_node(
    rid=next_rid+2, ID=root_order_id, cls='TSET_ORDER_EXECUTE',
    desc='OnSkillStart ROOT (新): [reset angle, reset vR, CREATE_BULLET]',
    params=[
        {"Value": modify_angle_id, "ParamType": 0, "Factor": 0},
        {"Value": modify_vr_id, "ParamType": 0, "Factor": 0},
        {"Value": create_bullet_id, "ParamType": 0, "Factor": 0},
    ],
    pos=(-400, 200),
)

data['references']['RefIds'].extend([modify_angle, modify_vr, root_order])
data['nodes'].extend([{"rid": next_rid}, {"rid": next_rid+1}, {"rid": next_rid+2}])

# Update SkillConfig.SkillEffectExecuteInfo.SkillEffectConfigID = root_order_id
sc_cj_str = skill_config_node['data'].get('ConfigJson', '') or '{}'
sc_cj = json.loads(sc_cj_str)
old_root = sc_cj.get('SkillEffectExecuteInfo', {}).get('SkillEffectConfigID')
sc_cj.setdefault('SkillEffectExecuteInfo', {})['SkillEffectConfigID'] = root_order_id
skill_config_node['data']['ConfigJson'] = json.dumps(sc_cj, ensure_ascii=False)
print(f'SkillConfig.SkillEffectExecuteInfo: {old_root} -> {root_order_id}')

# Add edges (ORDER dynamic-port='0' for all multi-children)
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

# ROOT_ORDER → 3 children
data['edges'].append(make_edge(modify_angle_id, root_order_id, "0"))
data['edges'].append(make_edge(modify_vr_id, root_order_id, "0"))
data['edges'].append(make_edge(create_bullet_id, root_order_id, "0"))
print(f'[FIX] edges += 3 = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])}')
