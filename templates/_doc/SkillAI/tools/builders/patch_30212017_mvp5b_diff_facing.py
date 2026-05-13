"""patch_30212017_mvp5b_diff_facing.py — MVP-5b: 让 CREATE_B 用不同 birth heading

新加 1 SkillTag birth_facing_offset_B (default=180°)
改 CREATE_B (32900054) P[1] 从 {V=91, PT=1 attr=facing} → {V=新SkillTag, PT=3 SkillTag ref}

预期: CREATE_A 朝 caster facing 方向飞 / CREATE_B 朝 caster facing + 180° 方向飞（相反）
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

alloc = IDAllocator()
new_skilltag_id = alloc.get_next('SkillTagsConfig')
print(f'New SkillTag id={new_skilltag_id} (default=180)')

# Add SkillTag node (仿 320198/320199 schema)
next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1
new_st_guid = str(uuid.uuid4())
new_st_node = {
    "rid": next_rid,
    "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": new_st_guid, "computeOrder": 12,
        "position": {"serializedVersion": "2", "x": 1700.0, "y": 1300.0, "width": 237.0, "height": 135.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": new_skilltag_id, "Desc": "SkillTag 声明",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
        "ConfigJson": json.dumps({
            "ID": new_skilltag_id, "TagType": 0,
            "Desc": "MVP5b CREATE_B birth_facing_offset (180°)",
            "NameKey": 0, "DefaultValue": 180,
            "FinalValueEffectID": 0, "RetainWhenDie": False,
        }, ensure_ascii=False),
        "Config2ID": f"SkillTagsConfig_{new_skilltag_id}",
    }
}
data['references']['RefIds'].append(new_st_node)
data['nodes'].append({"rid": next_rid})
print(f'[ADD] SkillTag {new_skilltag_id}')

# Modify CREATE_B (32900054) Params[1] to use SkillTag ref
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson', '') or '{}')
    if cj.get('ID') == 32900054 and r['type']['class'] == 'TSET_CREATE_BULLET':
        old_p1 = cj['Params'][1]
        cj['Params'][1] = {"Value": new_skilltag_id, "ParamType": 3, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"MVP-5b CREATE_B (P[1] FACE_DIR = SkillTag {new_skilltag_id} = 180°)"
        print(f'[FIX] CREATE_B P[1]: {old_p1} → {{V={new_skilltag_id}, PT=3 SkillTag}}')
        break

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
