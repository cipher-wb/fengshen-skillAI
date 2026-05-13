"""patch_30212018_rename_v2_simple.py — 改 30212018 → 30212010 AIgen (简化版)

跟 v1 相比，跳过 320100 复制 (320100 定义在 30212011 三重碧叶蓝图，不在 30212010 / 不受影响)。

操作:
1. 改新蓝图 SkillConfigNode.ID: 30212018 → 30212010
2. 改 path 字段
3. 批量替换 PoC → AIgen (所有 Desc / sticky note / title)
4. 写新文件 SkillGraph_30212010_AIgen_叶散风行.json (中文方括号留给用户改)

⚠️ 用户操作 (本 patch 不做):
- 把原 SkillGraph_30212010_xxx.json mv 到 .json.bak 或别处 (避免 SkillConfig.ID=30212010 冲突)
- 删除老的 SkillGraph_30212018 文件
"""
import json
from pathlib import Path

JSON_DIR = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons')
SRC_NEW = next(JSON_DIR.rglob('SkillGraph_30212018*.json'))
DST_NEW = SRC_NEW.parent / 'SkillGraph_30212010_AIgen_叶散风行.json'

dst_data = json.loads(SRC_NEW.read_text(encoding='utf-8'))

# Step 1: 改 SkillConfigNode ID
for r in dst_data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    if r['type']['class'] == 'SkillConfigNode' and cj.get('ID') == 30212018:
        cj['ID'] = 30212010
        r['data']['ID'] = 30212010
        r['data']['Config2ID'] = 'SkillConfig_30212010'
        r['data']['Desc'] = '30212010 [AIgen] 叶散风行 (AI 生成版)\n8 颗叶子风车扩散 + 每 3 发第 3 强化\n复用 320037 三重碧叶 buff / 30212011 三重碧叶技能的 320100 飞叶计数器'
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] SkillConfig.ID: 30212018 → 30212010')
        break

# Step 2: path
dst_data['path'] = str(DST_NEW.relative_to(JSON_DIR.parent.parent.parent.parent).as_posix())
print(f'[FIX] path = {dst_data["path"]}')

# Step 3: 批量 PoC → AIgen
fixed = 0
for r in dst_data['references']['RefIds']:
    d = r['data'].get('Desc', '')
    if 'PoC' in d:
        r['data']['Desc'] = d.replace('PoC', 'AIgen')
        fixed += 1
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try: cj = json.loads(cj_str)
    except: continue
    if isinstance(cj, dict) and 'Desc' in cj and isinstance(cj['Desc'], str) and 'PoC' in cj['Desc']:
        cj['Desc'] = cj['Desc'].replace('PoC', 'AIgen')
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        fixed += 1
print(f'[FIX] {fixed} Desc PoC → AIgen')

for n in dst_data.get('stickyNotes', []):
    for k in ('title', 'content'):
        if 'PoC' in n.get(k, ''):
            n[k] = n[k].replace('PoC', 'AIgen').replace('30212018', '30212010')
print('[FIX] sticky note')

# Write new file
DST_NEW.write_text(json.dumps(dst_data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[WRITE] {DST_NEW.name}')
print(f'\n⚠️ 请你手动操作:')
print(f'  1. 把原 SkillGraph_30212010_xxx_叶散风行.json mv 到 .json.bak 或别处 (避免 ID 冲突)')
print(f'  2. 老 SkillGraph_30212018_PoC_叶散风行.json 可删除')
print(f'  3. 把新文件 SkillGraph_30212010_AIgen_叶散风行.json 改名加方括号 (可选 / 当前无中文方括号)')
