"""patch_30212017_mvp8_extract_skilltags.py — 提取 3 个可调 SkillTag 参数

让策划在 SkillEditor 里通过 SkillTag 面板直接调，不用动 JSON / Python builder。

新加 SkillTag (各自 default value):
  spin_step_per_frame  default=-8   (每帧 facing 旋转 / 480°/秒 / 负=顺时针)
  vR_step_per_frame    default=1    (每帧径向速度累加)
  vR_initial           default=5    (出生时初始径向速度)

改造:
  NUM_CALC 32900074 P[2]:  常量 -8 → SkillTag spin_step_per_frame (PT=3)
  ADD_vR   32900040 P[3]:  常量 1  → SkillTag vR_step_per_frame   (PT=3)
  reset_vR 32900052 P[3]:  常量 5  → SkillTag vR_initial          (PT=3)
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

alloc = IDAllocator()
spin_step_id = alloc.get_next('SkillTagsConfig')
vR_step_id   = alloc.get_next('SkillTagsConfig')
vR_init_id   = alloc.get_next('SkillTagsConfig')
print(f'New SkillTags: spin_step={spin_step_id} / vR_step={vR_step_id} / vR_initial={vR_init_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Build 3 SkillTagsConfig nodes (仿 320198 / 320199 schema)
def make_skilltag(rid, ID, default_value, desc, x, y):
    return {
        "rid": rid,
        "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 13,
            "position": {"serializedVersion": "2", "x": float(x), "y": float(y), "width": 237.0, "height": 135.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
            "ConfigJson": json.dumps({
                "ID": ID, "TagType": 0,
                "Desc": desc,
                "NameKey": 0, "DefaultValue": default_value,
                "FinalValueEffectID": 0, "RetainWhenDie": False,
            }, ensure_ascii=False),
            "Config2ID": f"SkillTagsConfig_{ID}",
        }
    }

nodes_new = [
    make_skilltag(next_rid,     spin_step_id, -8, '每帧 facing 旋转角度（°/帧，负=顺时针）',  500.0, 1700.0),
    make_skilltag(next_rid + 1, vR_step_id,   1,  '每帧径向速度累加',                       500.0, 1900.0),
    make_skilltag(next_rid + 2, vR_init_id,   5,  '出生时初始径向速度',                     500.0, 2100.0),
]
for n in nodes_new:
    data['references']['RefIds'].append(n)
    data['nodes'].append({"rid": n['rid']})
print(f'[ADD] 3 SkillTagsConfig nodes')

# Modify 3 nodes to reference SkillTags via PT=3
EDITS = [
    (32900074, 2, spin_step_id, 'spin_step'),  # NUM_CALC self.facing + spin_step
    (32900040, 3, vR_step_id,   'vR_step'),    # ADD_SKILL_TAG vR_acc += step
    (32900052, 3, vR_init_id,   'vR_initial'), # MODIFY_SKILL_TAG vR = initial
]

for target_id, param_idx, skilltag_id, tag_name in EDITS:
    for r in data['references']['RefIds']:
        cj_str = r['data'].get('ConfigJson', '') or '{}'
        cj = json.loads(cj_str)
        if cj.get('ID') == target_id:
            old = dict(cj['Params'][param_idx])
            cj['Params'][param_idx] = {"Value": skilltag_id, "ParamType": 3, "Factor": 0}
            r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
            print(f'[FIX] {target_id} P[{param_idx}]: {old} → SkillTag {skilltag_id} ({tag_name})')
            break

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(data["references"]["RefIds"])} / edges={len(data["edges"])}')
