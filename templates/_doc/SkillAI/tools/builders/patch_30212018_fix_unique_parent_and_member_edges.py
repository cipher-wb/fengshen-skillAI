"""patch_30212018_fix_unique_parent_and_member_edges.py — 两件大事：

1. 修复 unique-parent 违反: 复制 OnTick 控制流链 (REPEAT + body + body 子节点) 各一份给强化/普通
2. 加缺失的 member edges (BulletConfig → AfterBorn/BeforeBorn / SkillConfig → ROOT_ORDER)

复制清单（强化保留原 ID, 普通用新 ID）:
  32900194 REPEAT       → 32900194_n (新)
  32900133 OnTick body  → 32900133_n
  32900148 MODIFY_facing → 32900148_n
  32900138 ADD_r        → 32900138_n
  32900136 CHANGE_POS   → 32900136_n
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path('doc/SkillAI/tools').resolve()))
from id_allocator import IDAllocator

P = Path('<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212018【PoC】叶散风行.json')
data = json.loads(P.read_text(encoding='utf-8'))

# === Pre-Phase: 找当前 OnTick 链节点 reallocated 后 ID ===
# 旧 ID（30212017 PoC） / 当前 ID 已 reallocated 一次
# 32900194 = REPEAT (我之前加的)
# 32900133 = OnTick body
# 32900148, 32900138, 32900136 = body 三子
ONTICK_CHAIN = [32900194, 32900133, 32900148, 32900138, 32900136]

# 验证这些都存在
existing_se = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    nid = cj.get('ID')
    if nid: existing_se.add(nid)

for nid in ONTICK_CHAIN:
    if nid not in existing_se:
        print(f'⚠ {nid} not in graph!')

alloc = IDAllocator()
def alloc_id():
    while True:
        x = alloc.get_next('SkillEffectConfig')
        if x not in existing_se: existing_se.add(x); return x

# 分配 5 个新 ID 给普通版
id_map_normal = {old: alloc_id() for old in ONTICK_CHAIN}
print(f'Copy plan (强化保留 → 普通新ID):')
for old, new in id_map_normal.items(): print(f'  {old} → {new}')

# === Phase 1: 复制 5 个节点 ===
# 找各节点 source RefId
src_nodes = {}
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    if cj.get('ID') in ONTICK_CHAIN:
        src_nodes[cj['ID']] = r

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

def replace_in_obj(obj, m):
    if isinstance(obj, dict): return {k: replace_in_obj(v, m) for k,v in obj.items()}
    if isinstance(obj, list): return [replace_in_obj(v, m) for v in obj]
    if isinstance(obj, int) and obj in m: return m[obj]
    return obj

new_nodes_added = []
for old_id, new_id in id_map_normal.items():
    src = src_nodes[old_id]
    new_node = json.loads(json.dumps(src))  # deep copy
    new_node['rid'] = next_rid
    new_node['data']['GUID'] = str(uuid.uuid4())
    new_node['data']['ID'] = new_id
    # 重写 ConfigJson - 自己 ID + 内部引用 reallocate
    cj_str = new_node['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    cj_new = replace_in_obj(cj, id_map_normal)
    cj_new['ID'] = new_id
    new_node['data']['ConfigJson'] = json.dumps(cj_new, ensure_ascii=False)
    new_node['data']['Config2ID'] = f'SkillEffectConfig_{new_id}'
    # 位置偏移避免重叠
    if 'position' in new_node['data']:
        new_node['data']['position']['x'] = float(new_node['data']['position'].get('x', 0)) + 500
        new_node['data']['position']['y'] = float(new_node['data']['position'].get('y', 0)) + 500
    new_node['data']['Desc'] = '【普通版】' + new_node['data'].get('Desc', '')
    data['references']['RefIds'].append(new_node)
    data['nodes'].append({'rid': next_rid})
    new_nodes_added.append((next_rid, new_id))
    next_rid += 1
print(f'[ADD] {len(new_nodes_added)} 新节点 (普通版 OnTick 链)')

# === Phase 2: 改 32900166 P[0] 从 32900194 → 32900194_normal ===
new_repeat_normal_id = id_map_normal[32900194]
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    if cj.get('ID') == 32900166:
        cj['Params'][0]['Value'] = new_repeat_normal_id
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] 32900166 P[0]: 32900194 → {new_repeat_normal_id}')
        break

# === Phase 3: 复制 edges 内部链 (强化原版 edges 保留，加普通版 edges) ===
# 重建 guid map
guid_by_id = {}
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: cj = {}
    nid = cj.get('ID')
    if not nid and r['type']['class'] == 'RefConfigBaseNode': nid = r['data'].get('ManualID')
    if nid: guid_by_id.setdefault(nid, r['data']['GUID'])

# 原 edges 内涉及 ONTICK_CHAIN 节点的边 (除 32900194 → 32900166 那条要改 source)
# 32900194 → 32900166: 改 source 为 new_repeat_normal_id
# 其他 internal edges: 复制成普通版

internal_edges_to_copy = []
for e in data['edges']:
    # 内部 edge: input 和 output 都在 ONTICK_CHAIN
    src_id = None; dst_id = None
    for nid, g in guid_by_id.items():
        if g == e['inputNodeGUID']: src_id = nid
        if g == e['outputNodeGUID']: dst_id = nid
    if src_id in ONTICK_CHAIN and dst_id in ONTICK_CHAIN:
        internal_edges_to_copy.append((src_id, dst_id, e))

# 改 32900194 → 32900166 这条
for e in data['edges']:
    src_id = None; dst_id = None
    for nid, g in guid_by_id.items():
        if g == e['inputNodeGUID']: src_id = nid
        if g == e['outputNodeGUID']: dst_id = nid
    if src_id == 32900194 and dst_id == 32900166:
        # 改 inputNodeGUID 为 new REPEAT
        e['inputNodeGUID'] = guid_by_id[new_repeat_normal_id]
        print(f'[FIX] edge 32900194→32900166: source → {new_repeat_normal_id}')
        break

# 复制内部 edges (创建普通版的)
copied_edges = 0
for src_id, dst_id, e in internal_edges_to_copy:
    new_src = id_map_normal[src_id]
    new_dst = id_map_normal[dst_id]
    new_edge = dict(e)
    new_edge['GUID'] = str(uuid.uuid4())
    new_edge['inputNodeGUID'] = guid_by_id[new_src]
    new_edge['outputNodeGUID'] = guid_by_id[new_dst]
    data['edges'].append(new_edge)
    copied_edges += 1
print(f'[ADD] {copied_edges} internal edges (普通版 OnTick 链内部)')

# === Phase 4: 加 member edges (BulletConfig / SkillConfig) ===
def add_member_edge(src_id, dst_id):
    if src_id not in guid_by_id or dst_id not in guid_by_id:
        print(f'  ⚠ SKIP {src_id}→{dst_id}: id not in graph')
        return False
    e = {'GUID': str(uuid.uuid4()),
         'inputNodeGUID': guid_by_id[src_id],     # source / 子 SkillEffect
         'outputNodeGUID': guid_by_id[dst_id],     # destination / 父 BulletConfig/SkillConfig
         'inputFieldName':'ID','outputFieldName':'PackedMembersOutput',
         'inputPortIdentifier':'0','outputPortIdentifier':'0','isVisible':True}
    data['edges'].append(e)
    return True

# 检查现有 member edges
existing_member = set()
for e in data['edges']:
    if e['outputFieldName'] == 'PackedMembersOutput':
        # 用 GUID pair 标识
        existing_member.add((e['inputNodeGUID'], e['outputNodeGUID']))

mem_added = 0
mem_list = [
    (32900165, 320262, 'BulletConfig 320262.AfterBorn'),  # AfterBorn 强化
    (32900166, 320263, 'BulletConfig 320263.AfterBorn'),  # AfterBorn 普通
    (32900153, 320262, 'BulletConfig 320262.BeforeBorn'),
    (32900153, 320263, 'BulletConfig 320263.BeforeBorn'),
    (32900141, 30212018, 'SkillConfig 30212018.SkillEffectExecuteInfo'),
]
for src, dst, desc in mem_list:
    if src not in guid_by_id or dst not in guid_by_id:
        print(f'  ⚠ SKIP {src}→{dst}')
        continue
    key = (guid_by_id[src], guid_by_id[dst])
    if key in existing_member:
        print(f'  -- skip dup: {src}→{dst} ({desc})')
        continue
    if add_member_edge(src, dst):
        mem_added += 1
        print(f'  + member: {src}→{dst} ({desc})')
print(f'[ADD] {mem_added} member edges')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(data["references"]["RefIds"])} / edges={len(data["edges"])}')
