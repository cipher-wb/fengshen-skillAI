"""patch_30212018_rename_to_30212010_aigen.py — 把 30212018 PoC 改名 + 升 ID 为 30212010 AIgen

操作:
1. 把 SkillTag 320100 (原 30212010 定义) 复制到新蓝图（保留 ID / 加 AIgen Desc）
2. 改 SkillConfigNode.ID: 30212018 → 30212010
3. 批量替换 PoC → AIgen (data.Desc + ConfigJson.Desc + sticky note + title)
4. 写新文件: SkillGraph_30212010【AIgen】叶散风行.json
5. 原 30212018 文件保留 (用户手动删 / 或留作 PoC 备份)
6. 原 30212010 文件由用户手动 mv 出本目录 (后缀 .bak 或别处)
"""
import json, uuid
from pathlib import Path

JSON_DIR = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons')
# 用 glob 绕开中文路径编码问题
SRC_NEW = next(JSON_DIR.rglob('SkillGraph_30212018*.json'))
SRC_OLD = next(JSON_DIR.rglob('SkillGraph_30212010*奇术*叶散风行.json'))
DST_NEW = SRC_NEW.parent / 'SkillGraph_30212010_AIgen_叶散风行.json'  # 文件名暂不带方括号 / 后面用户可以手动加

src_old_data = json.loads(SRC_OLD.read_text(encoding='utf-8'))
dst_data = json.loads(SRC_NEW.read_text(encoding='utf-8'))

# === Step 1: 复制 SkillTag 320100 定义到新蓝图 (Desc 改 AIgen) ===
node_320100 = None
for r in src_old_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    if r['type']['class'] == 'SkillTagsConfigNode' and cj.get('ID') == 320100:
        node_320100 = json.loads(json.dumps(r))
        break

if not node_320100:
    raise RuntimeError('320100 not found in old 30212010')

next_rid = max(r['rid'] for r in dst_data['references']['RefIds']) + 1
node_320100['rid'] = next_rid
node_320100['data']['GUID'] = str(uuid.uuid4())
if 'position' in node_320100['data']:
    node_320100['data']['position']['x'] = float(node_320100['data']['position'].get('x', 0)) + 5000

cj = json.loads(node_320100['data']['ConfigJson'])
cj['Desc'] = '叶散风行AIgen-飞叶计数器'
node_320100['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
node_320100['data']['Desc'] = '叶散风行AIgen-飞叶计数器（继承自原 30212010）'
dst_data['references']['RefIds'].append(node_320100)
dst_data['nodes'].append({'rid': next_rid})
print(f'[ADD] SkillTag 320100 复制（ID 保留 / Desc 改 AIgen）')

# === Step 2: 改 SkillConfigNode ID 30212018 → 30212010 ===
for r in dst_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    if r['type']['class'] == 'SkillConfigNode' and cj.get('ID') == 30212018:
        cj['ID'] = 30212010
        r['data']['ID'] = 30212010
        r['data']['Config2ID'] = 'SkillConfig_30212010'
        r['data']['Desc'] = '30212010 [AIgen] 叶散风行 (AI 生成)\n8 颗叶子风车扩散 + 每 3 发第 3 强化\n复用 320037 三重碧叶 buff / 320100 飞叶计数器'
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] SkillConfig.ID: 30212018 → 30212010')
        break

# Step 3: path 字段
dst_data['path'] = '<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212010【AIgen】叶散风行.json'

# === Step 4: 批量替换 PoC → AIgen ===
fixed_count = 0
for r in dst_data['references']['RefIds']:
    d = r['data'].get('Desc', '')
    if 'PoC' in d:
        r['data']['Desc'] = d.replace('PoC', 'AIgen')
        fixed_count += 1
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    changed = False
    if 'Desc' in cj and isinstance(cj['Desc'], str) and 'PoC' in cj['Desc']:
        cj['Desc'] = cj['Desc'].replace('PoC', 'AIgen')
        changed = True
    if changed:
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        fixed_count += 1
print(f'[FIX] {fixed_count} Desc PoC → AIgen')

# Sticky note
for n in dst_data.get('stickyNotes', []):
    if 'PoC' in n.get('title', ''):
        n['title'] = n['title'].replace('PoC', 'AIgen').replace('30212018', '30212010')
    if 'PoC' in n.get('content', ''):
        n['content'] = n['content'].replace('PoC', 'AIgen').replace('30212018', '30212010')
print('[FIX] sticky note PoC→AIgen / 30212018→30212010')

# === Step 5: 写新文件 ===
DST_NEW.write_text(json.dumps(dst_data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[WRITE] {DST_NEW.name}')
print(f'\n⚠️ 请手动处理:')
print(f'  1. 把原 {SRC_OLD.name} mv 到别处 (如加 .json.bak 后缀) — 避免 SkillConfig.ID=30212010 冲突')
print(f'  2. {SRC_NEW.name} (老 30212018) 可手动删除')
