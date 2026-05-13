"""patch_30212018_copy_collision_chain.py — 复制 32003149/32003150 整条碰撞链到 30212018 本地

跨蓝图 RefConfigBaseNode 引用 ORDER 子项 SkillEditor 不识别 → P[1] 被自动清掉
解法: 把 32003149 / 32003150 + 它们递归依赖的所有子节点全部 deep copy 到 30212018
      + reallocate 所有 ID 避免冲突
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator, cls_to_table

SRC = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212010【木宗门】奇术_人阶_叶散风行.json')
DST = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212018【PoC】叶散风行.json')

src_data = json.loads(SRC.read_text(encoding='utf-8'))
dst_data = json.loads(DST.read_text(encoding='utf-8'))

# Build SRC node index by ID
src_by_id = {}  # nid → (rid, RefId dict)
for r in src_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID') or r['data'].get('ManualID')
    if nid: src_by_id[nid] = r

# === Recursive collect: which SkillEffectConfig nodes 32003149/32003150 depend on ===
needed = set()  # SkillEffectConfig IDs to copy
def collect(nid):
    if nid in needed: return
    if nid not in src_by_id: return
    r = src_by_id[nid]
    cls = r['type']['class']
    # 只递归 SkillEffectConfig 类节点 (SkillEffect/SkillCondition + 其它跨链如 RefConfigBaseNode 跳过)
    table = cls_to_table(cls)
    if table != 'SkillEffectConfig' and table != 'SkillConditionConfig':
        return  # 不复制 BulletConfig/ModelConfig/SkillTagsConfig 等
    needed.add(nid)
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: return
    # 收集 Params 内 ID 引用
    for p in cj.get('Params', []):
        v = p.get('Value')
        if isinstance(v, int) and v in src_by_id:
            collect(v)

collect(32003149)
collect(32003150)
print(f'Need to copy {len(needed)} SkillEffect/SkillCondition nodes from 30212010')

# === ID Allocator (避开已用 / DST 内 + 全工程 + SRC) ===
existing_se = set()
existing_st = set()
existing_sc = set()
existing_bc = set()
for r in dst_data['references']['RefIds']:
    cls = r['type']['class']
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID')
    if not nid: continue
    t = cls_to_table(cls)
    if t == 'SkillEffectConfig': existing_se.add(nid)
    elif t == 'SkillConditionConfig': existing_sc.add(nid)
    elif t == 'SkillTagsConfig': existing_st.add(nid)
    elif t == 'BulletConfig': existing_bc.add(nid)

alloc = IDAllocator(exclude_files=set())  # scan whole project
def alloc_id(table, existing):
    while True:
        x = alloc.get_next(table)
        if x not in existing:
            existing.add(x); return x

# === Build id_map: 30212010 ID → 新分配 ID ===
id_map = {}
for nid in needed:
    r = src_by_id[nid]
    cls = r['type']['class']
    t = cls_to_table(cls)
    if t == 'SkillEffectConfig':
        id_map[nid] = alloc_id('SkillEffectConfig', existing_se)
    elif t == 'SkillConditionConfig':
        id_map[nid] = alloc_id('SkillConditionConfig', existing_sc)

print(f'ID remap: {len(id_map)} entries')

# === Deep copy nodes to DST + 替换内部引用 ===
def replace_in_obj(obj, mapping):
    if isinstance(obj, dict): return {k: replace_in_obj(v, mapping) for k,v in obj.items()}
    if isinstance(obj, list): return [replace_in_obj(v, mapping) for v in obj]
    if isinstance(obj, int) and obj in mapping: return mapping[obj]
    return obj

next_rid = max(r['rid'] for r in dst_data['references']['RefIds']) + 1
for nid in needed:
    r_src = src_by_id[nid]
    new_id = id_map[nid]
    # Deep copy node
    new_node = json.loads(json.dumps(r_src))  # cheap deep copy
    new_node['rid'] = next_rid
    new_node['data']['GUID'] = str(uuid.uuid4())
    # 改 ID + Config2ID
    cj_str = new_node['data'].get('ConfigJson', '') or '{}'
    try:
        cj = json.loads(cj_str)
        cj_new = replace_in_obj(cj, id_map)
        cj_new['ID'] = new_id  # 自己 ID 一定换
        new_node['data']['ConfigJson'] = json.dumps(cj_new, ensure_ascii=False)
    except: pass
    if 'ID' in new_node['data']: new_node['data']['ID'] = new_id
    cls = new_node['type']['class']
    t = cls_to_table(cls)
    prefix = 'SkillEffectConfig_' if t == 'SkillEffectConfig' else ('SkillConditionConfig_' if t == 'SkillConditionConfig' else 'Unknown_')
    new_node['data']['Config2ID'] = f'{prefix}{new_id}'
    # 移动位置避免重叠
    if 'position' in new_node['data']:
        new_node['data']['position']['x'] = float(new_node['data']['position'].get('x', 0)) + 10000
    dst_data['references']['RefIds'].append(new_node)
    dst_data['nodes'].append({'rid': next_rid})
    next_rid += 1

print(f'Copied {len(needed)} nodes')

# === 复制 edges (限于 needed 节点之间) ===
src_guid_to_id = {}
for r in src_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID') or r['data'].get('ManualID')
    if nid: src_guid_to_id[r['data']['GUID']] = nid

# DST 内新节点的 ID → GUID
dst_id_to_guid = {}
for r in dst_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID') or r['data'].get('ManualID')
    if nid: dst_id_to_guid[nid] = r['data']['GUID']

copied_edges = 0
for e in src_data['edges']:
    src_id = src_guid_to_id.get(e['inputNodeGUID'])
    dst_id = src_guid_to_id.get(e['outputNodeGUID'])
    if src_id in needed and dst_id in needed:
        # 复制 edge 改 GUID
        new_src_id = id_map[src_id]
        new_dst_id = id_map[dst_id]
        if new_src_id in dst_id_to_guid and new_dst_id in dst_id_to_guid:
            new_edge = dict(e)
            new_edge['GUID'] = str(uuid.uuid4())
            new_edge['inputNodeGUID'] = dst_id_to_guid[new_src_id]
            new_edge['outputNodeGUID'] = dst_id_to_guid[new_dst_id]
            dst_data['edges'].append(new_edge)
            copied_edges += 1
print(f'Copied {copied_edges} edges')

# === 修改 30212018 内 32900165 / 32900166 P[1] 指向新本地 32003150_local / 32003149_local + outPort 改回 0 ===
new_premium_order_id = id_map[32003150]
new_normal_order_id = id_map[32003149]
print(f'New local: 32003150 → {new_premium_order_id} / 32003149 → {new_normal_order_id}')

for r in dst_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    if cj.get('ID') == 32900165:
        cj['Params'] = [
            {'Value': 32900133, 'ParamType': 0, 'Factor': 0},
            {'Value': new_premium_order_id, 'ParamType': 0, 'Factor': 0},
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] 32900165 P[1] → {new_premium_order_id}')
    elif cj.get('ID') == 32900166:
        cj['Params'] = [
            {'Value': 32900133, 'ParamType': 0, 'Factor': 0},
            {'Value': new_normal_order_id, 'ParamType': 0, 'Factor': 0},
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] 32900166 P[1] → {new_normal_order_id}')

# === 删除老 RefConfigBaseNode 32003150 / 32003149 ===
del_guids = set()
for r in dst_data['references']['RefIds']:
    if r['type']['class'] == 'RefConfigBaseNode' and r['data'].get('ManualID') in (32003149, 32003150):
        del_guids.add(r['data']['GUID'])
dst_data['references']['RefIds'] = [r for r in dst_data['references']['RefIds'] if r['data']['GUID'] not in del_guids]
remaining_rids = {r['rid'] for r in dst_data['references']['RefIds']}
dst_data['nodes'] = [n for n in dst_data['nodes'] if n['rid'] in remaining_rids]
dst_data['edges'] = [e for e in dst_data['edges'] if e['inputNodeGUID'] not in del_guids and e['outputNodeGUID'] not in del_guids]
print(f'[DEL] {len(del_guids)} RefConfigBaseNode (cross-blueprint refs)')

# === 加 edges 32900165/166 → 本地新 ORDER ===
def add_edge(src_id, dst_id, port='0', field='PackedParamsOutput'):
    if src_id not in dst_id_to_guid or dst_id not in dst_id_to_guid:
        print(f'  SKIP {src_id}→{dst_id}')
        return
    dst_data['edges'].append({
        'GUID': str(uuid.uuid4()),
        'inputNodeGUID': dst_id_to_guid[src_id],
        'outputNodeGUID': dst_id_to_guid[dst_id],
        'inputFieldName':'ID','outputFieldName':field,
        'inputPortIdentifier':'0','outputPortIdentifier':port,'isVisible':True
    })

# Fix outPort for 32900165/166 既有 edges 回 0
for e in dst_data['edges']:
    src = next((nid for nid, g in dst_id_to_guid.items() if g == e['inputNodeGUID']), None)
    dst = next((nid for nid, g in dst_id_to_guid.items() if g == e['outputNodeGUID']), None)
    if dst in (32900165, 32900166) and src == 32900133:
        e['outputPortIdentifier'] = '0'

# 加新 edges from local copies
add_edge(new_premium_order_id, 32900165, '0')
add_edge(new_normal_order_id, 32900166, '0')
print(f'[ADD] 2 edges to new local copies')

DST.write_text(json.dumps(dst_data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(dst_data["references"]["RefIds"])} / edges={len(dst_data["edges"])}')
