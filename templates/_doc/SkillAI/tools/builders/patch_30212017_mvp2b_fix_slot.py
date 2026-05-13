"""patch_30212017_mvp2b_fix_slot.py — MVP-2b 修复

根因（log 揭出）:
- MATH_COS P[0]={V=321001, PT=3} 报错 "Cannot Find SkillEffectConfig Data ConfigID:321001"
- 引擎把 PT=3 + V=321001 当 SkillEffectConfig 查 / 因为 321001 是 SkillTagsConfig.ID 不是 SkillEffect.ID
- 真相: PT=3 = TPT_SKILL_PARAM 实际读 entity 私有 SkillTag slot (整数 slot ID / 不需要 SkillTagsConfigNode 声明)

修法（仿 30212010 真实样本 66001776 / 66001609 / 66001755 模式）:
1. 删 SkillTagsConfigNode 321001 (无用 / 不该有)
2. ADD_SKILL_TAG_VALUE 302120185 Params 完全重写仿 30212010 32002231 模式:
   P[0]={V=1, PT=5}     主体单位
   P[1]={V=41, PT=5}    实体级 tag 命名空间标志
   P[2]={V=1500, PT=0}  slot ID = 1500 (任意未用过 / 30212010 用 1004-1007)
   P[3]={V=5, PT=0}     delta = 5
   P[4]={V=1, PT=0}     flag (固定 1)
3. MATH_COS 302120181 P[0] = {V=1500, PT=3}  ← 改用 slot ID

ID 1500 选择: 30212010 用 1004-1007 / 我们用 1500 段位避冲突 / MVP-3+ 可用 1501+
"""
import json
from pathlib import Path

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

SLOT_ID = 1500  # entity-level slot for angle accumulator

# === 1. Delete SkillTagsConfigNode 321001 ===
before = len(data['references']['RefIds'])
data['references']['RefIds'] = [r for r in data['references']['RefIds']
                                 if not (r['type']['class'] == 'SkillTagsConfigNode'
                                         and json.loads(r['data'].get('ConfigJson','{}') or '{}').get('ID') == 321001)]
removed = before - len(data['references']['RefIds'])
print(f'[REMOVE] SkillTagsConfigNode 321001: {removed} removed')

# Also remove its node entry (find rid 1012 = was the SkillTag)
data['nodes'] = [n for n in data['nodes'] if n.get('rid') != 1012]

# === 2. Rewrite ADD_SKILL_TAG_VALUE 302120185 Params (仿 30212010 32002231) ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120185:
        cj['Params'] = [
            {"Value": 1, "ParamType": 5, "Factor": 0},        # 主体单位
            {"Value": 41, "ParamType": 5, "Factor": 0},       # 实体级 tag 命名空间
            {"Value": SLOT_ID, "ParamType": 0, "Factor": 0},  # slot ID = 1500
            {"Value": 5, "ParamType": 0, "Factor": 0},        # delta = 5
            {"Value": 1, "ParamType": 0, "Factor": 0},        # flag = 1
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"entity SkillTag slot {SLOT_ID} += 5/帧 (angle 累加 / 仿 30212010 32002231)"
        print(f'[FIX] ADD_SKILL_TAG 302120185 Params (仿真实样本)')
        break

# === 3. MATH_COS 302120181 P[0] = {V=1500, PT=3} ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120181:
        cj['Params'] = [
            {"Value": SLOT_ID, "ParamType": 3, "Factor": 0},  # PT=3 读 slot value
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"cos(entity slot {SLOT_ID} angle) → [-10000, 10000]"
        print(f'[FIX] MATH_COS 302120181 P[0] = slot {SLOT_ID} PT=3')
        break

# === 4. Edges - keep all that don't touch SkillTag 321001 ===
# (no edge references SkillTag GUID, so nothing to remove)
print(f'[INFO] edges = {len(data["edges"])} (no SkillTag edge to remove)')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

# Verify
data2 = json.loads(P.read_text(encoding='utf-8'))
for r in data2['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') == 302120185:
        print(f'[VERIFY] ADD_SKILL_TAG Params: {[(p["Value"], p["ParamType"]) for p in cj["Params"]]}')
    if cj.get('ID') == 302120181:
        print(f'[VERIFY] MATH_COS Params: {[(p["Value"], p["ParamType"]) for p in cj["Params"]]}')
# Confirm SkillTag deleted
has_skilltag_321001 = any(json.loads(r['data'].get('ConfigJson','{}') or '{}').get('ID') == 321001
                          for r in data2['references']['RefIds'])
print(f'[VERIFY] SkillTag 321001 still present: {has_skilltag_321001} (expect False)')
print(f'[VERIFY] total RefIds = {len(data2["references"]["RefIds"])}')
