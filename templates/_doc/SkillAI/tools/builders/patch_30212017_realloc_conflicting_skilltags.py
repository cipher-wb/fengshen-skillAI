"""patch_30212017_realloc_conflicting_skilltags.py — 重分配冲突 SkillTag ID

冲突:
  320198 跟 SkillGraph_30532000 (天阶心法 枯荣万灵决) 同 ID → 主干 NodeEditor 导 excel 失败
  320199 同上

重分配:
  用 id_allocator.get_next() 扫全工程跳过已占 ID
  更新所有引用（SkillTagsConfigNode 自身 + 所有 ConfigJson Params 内 PT=3/PT=0 引用）
"""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

# Allocate 2 new SkillTag IDs (id_allocator scans all SkillGraph_*.json including 30532000)
# IMPORTANT: 不要 exclude 30212017 本文件，否则 alloc 会避开本文件已占的 320931-320935 反而冲突
alloc = IDAllocator()
new_320198 = alloc.get_next('SkillTagsConfig')
new_320199 = alloc.get_next('SkillTagsConfig')

# Sanity check: 不能跟本文件已存在的其他 SkillTag 撞
existing_ids = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if r['type']['class'] == 'SkillTagsConfigNode':
        existing_ids.add(cj.get('ID'))

while new_320198 in existing_ids:
    new_320198 = alloc.get_next('SkillTagsConfig')
while new_320199 in existing_ids or new_320199 == new_320198:
    new_320199 = alloc.get_next('SkillTagsConfig')

print(f'New: 320198 → {new_320198} (旧 angle_acc 已废弃但保留节点)')
print(f'New: 320199 → {new_320199} (vR_acc 活跃使用)')

REMAP = {320198: new_320198, 320199: new_320199}

# === 1. 改 SkillTagsConfigNode 自身的 ID + ConfigJson 内 ID + Config2ID ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if r['type']['class'] != 'SkillTagsConfigNode':
        continue
    old_id = cj.get('ID')
    if old_id in REMAP:
        new_id = REMAP[old_id]
        cj['ID'] = new_id
        r['data']['ID'] = new_id
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Config2ID'] = f'SkillTagsConfig_{new_id}'
        print(f'[FIX] SkillTagsConfigNode {old_id} → {new_id}')

# === 2. 扫所有节点的 ConfigJson Params, 替换引用 ===
ref_count = 0
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    if not cj_str:
        continue
    cj = json.loads(cj_str)
    changed = False
    # 扫 Params
    for p in cj.get('Params', []):
        v = p.get('Value')
        if v in REMAP:
            p['Value'] = REMAP[v]
            changed = True
            ref_count += 1
    if changed:
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)

print(f'[FIX] 替换 Params 引用 {ref_count} 处')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved')
print(f'    重打开 SkillEditor 验证 320198/320199 已变成 {new_320198}/{new_320199}')
