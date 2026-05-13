"""patch_30212018_copy_anim_sfx_unlock.py — 把 30212010 的 动作/特效/解控 链复制到 30212018

复制清单（11 个 SkillEffect/SkillCondition 节点）:
  - 32002975 CONDITION (解控分支判断)
  - 32002977 ORDER (解控子链 REMOVE+ADD_BUFF)
  - 32002978 REMOVE_BUFF
  - 32003612 ADD_BUFF (buff 320053 全局)
  - 320355 TSCT_VALUE_COMPARE
  - 32002976 GET_SKILL_TAG (读 SkillTag 320160 全局"本关卡卡号")
  - 13002635 PLAY_SOUND (sound 42030 全局)
  - 32002412 PLAY_ROLE_ANIM (anim 593 全局)
  - 32002411 ORDER (cast 特效集)
  - 32002408 CREATE_EFFECT (effect 3200332 全局)
  - 32002409 CREATE_EFFECT (3200333)
  - 32002410 CREATE_EFFECT (3200334)

不复制:
  - 32002226 (重置子弹角度 SkillTag 1002 / 30212018 不用 / 跳过)
  - 32002227 REPEAT (30212018 已有自己 32900164 替代)

修改 30212018 ROOT_ORDER 32900141 Params 顺序（按 30212010 节奏）:
  [reset_r, CONDITION解控, PLAY_SOUND, REPEAT生成子弹, PLAY_ROLE_ANIM, ORDER cast特效]
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator, cls_to_table

SRC = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212010【木宗门】奇术_人阶_叶散风行.json')
DST = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212018【PoC】叶散风行.json')

src_data = json.loads(SRC.read_text(encoding='utf-8'))
dst_data = json.loads(DST.read_text(encoding='utf-8'))

# 要复制的节点 IDs
COPY_LIST = [32002975, 32002977, 32002978, 32003612, 320355, 32002976,
             13002635, 32002412, 32002411, 32002408, 32002409, 32002410]

# Build src node index
src_by_id = {}
for r in src_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID') or r['data'].get('ManualID')
    if nid: src_by_id[nid] = r

# alloc 新 ID (避开 DST + 全工程已用)
existing_se = set(); existing_sc = set()
for r in dst_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID')
    if nid:
        t = cls_to_table(r['type']['class'])
        if t == 'SkillEffectConfig': existing_se.add(nid)
        elif t == 'SkillConditionConfig': existing_sc.add(nid)

alloc = IDAllocator()
def alloc_id(table, existing):
    while True:
        x = alloc.get_next(table)
        if x not in existing: existing.add(x); return x

# id_map: 旧→新
id_map = {}
for nid in COPY_LIST:
    r = src_by_id.get(nid)
    if not r:
        print(f'⚠ {nid} not found in 30212010, skip'); continue
    cls = r['type']['class']
    # 手动判定：TSCT_* 是 SkillCondition / TSET_* 是 SkillEffect
    if cls.startswith('TSCT_'):
        id_map[nid] = alloc_id('SkillConditionConfig', existing_sc)
    elif cls.startswith('TSET_'):
        id_map[nid] = alloc_id('SkillEffectConfig', existing_se)
    else:
        print(f'⚠ {nid} unknown class {cls}, skip')
print(f'ID remap: {len(id_map)} entries')
for o, n in id_map.items(): print(f'  {o} → {n}')

# Deep copy
def replace_in_obj(obj, m):
    if isinstance(obj, dict): return {k: replace_in_obj(v, m) for k,v in obj.items()}
    if isinstance(obj, list): return [replace_in_obj(v, m) for v in obj]
    if isinstance(obj, int) and obj in m: return m[obj]
    return obj

next_rid = max(r['rid'] for r in dst_data['references']['RefIds']) + 1
for old_id, new_id in id_map.items():
    r_src = src_by_id[old_id]
    new_node = json.loads(json.dumps(r_src))
    new_node['rid'] = next_rid
    new_node['data']['GUID'] = str(uuid.uuid4())
    new_node['data']['ID'] = new_id
    cj_str = new_node['data'].get('ConfigJson', '') or '{}'
    try:
        cj = json.loads(cj_str)
        cj_new = replace_in_obj(cj, id_map)
        cj_new['ID'] = new_id
        new_node['data']['ConfigJson'] = json.dumps(cj_new, ensure_ascii=False)
    except: pass
    cls = new_node['type']['class']
    prefix = 'SkillConditionConfig_' if cls.startswith('TSCT_') else 'SkillEffectConfig_'
    new_node['data']['Config2ID'] = f'{prefix}{new_id}'
    # 位置偏移避免重叠
    if 'position' in new_node['data']:
        new_node['data']['position']['x'] = float(new_node['data']['position'].get('x', 0)) + 12000
    dst_data['references']['RefIds'].append(new_node)
    dst_data['nodes'].append({'rid': next_rid})
    next_rid += 1
print(f'Copied {len(id_map)} nodes')

# 复制 edges (限于 COPY_LIST 之间)
src_guid_to_id = {}
for r in src_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID') or r['data'].get('ManualID')
    if nid: src_guid_to_id[r['data']['GUID']] = nid

dst_id_to_guid = {}
for r in dst_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID') or r['data'].get('ManualID')
    if nid: dst_id_to_guid[nid] = r['data']['GUID']

copied_edges = 0
for e in src_data['edges']:
    sid = src_guid_to_id.get(e['inputNodeGUID'])
    did = src_guid_to_id.get(e['outputNodeGUID'])
    if sid in COPY_LIST and did in COPY_LIST:
        new_sid = id_map[sid]; new_did = id_map[did]
        if new_sid in dst_id_to_guid and new_did in dst_id_to_guid:
            new_e = dict(e)
            new_e['GUID'] = str(uuid.uuid4())
            new_e['inputNodeGUID'] = dst_id_to_guid[new_sid]
            new_e['outputNodeGUID'] = dst_id_to_guid[new_did]
            dst_data['edges'].append(new_e)
            copied_edges += 1
print(f'Copied {copied_edges} internal edges')

# 修改 ROOT_ORDER 32900141 Params 加入新顺序
# 新顺序: [reset_r 32900140, CONDITION解控, PLAY_SOUND, REPEAT 32900164, PLAY_ROLE_ANIM, ORDER cast特效]
new_root_order = [
    {'Value': 32900140, 'ParamType': 0, 'Factor': 0},  # 已有: reset_r
    {'Value': id_map[32002975], 'ParamType': 0, 'Factor': 0},  # 新: 解控 CONDITION
    {'Value': id_map[13002635], 'ParamType': 0, 'Factor': 0},  # 新: PLAY_SOUND
    {'Value': 32900164, 'ParamType': 0, 'Factor': 0},  # 已有: REPEAT 子弹生成
    {'Value': id_map[32002412], 'ParamType': 0, 'Factor': 0},  # 新: PLAY_ROLE_ANIM
    {'Value': id_map[32002411], 'ParamType': 0, 'Factor': 0},  # 新: ORDER cast 特效集
]
for r in dst_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    if cj.get('ID') == 32900141:
        cj['Params'] = new_root_order
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = '【OnSkillStart】1.重置r 2.解控判断 3.音效 4.REPEAT生成子弹 5.播放动作 6.cast特效'
        print(f'[FIX] ROOT_ORDER 32900141: {len(new_root_order)} 项 (含解控/音效/动作/特效)')
        break

# 加 edges: ROOT_ORDER → 新加的 4 个子项 (outPort='0' dynamic)
def edge(src_id, dst_id, port='0', field='PackedParamsOutput'):
    if src_id not in dst_id_to_guid or dst_id not in dst_id_to_guid: return None
    return {'GUID': str(uuid.uuid4()),
            'inputNodeGUID': dst_id_to_guid[src_id],
            'outputNodeGUID': dst_id_to_guid[dst_id],
            'inputFieldName':'ID','outputFieldName':field,
            'inputPortIdentifier':'0','outputPortIdentifier':port,'isVisible':True}

# 重建 dst_id_to_guid (新节点的 GUID 加入)
dst_id_to_guid = {}
for r in dst_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID') or r['data'].get('ManualID')
    if nid: dst_id_to_guid[nid] = r['data']['GUID']

added_root_edges = 0
for new_child in (id_map[32002975], id_map[13002635], id_map[32002412], id_map[32002411]):
    e = edge(new_child, 32900141, '0')
    if e:
        dst_data['edges'].append(e)
        added_root_edges += 1
print(f'[ADD] {added_root_edges} ROOT_ORDER → 新子项 edges (dynamic port=0)')

DST.write_text(json.dumps(dst_data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(dst_data["references"]["RefIds"])} / edges={len(dst_data["edges"])}')
