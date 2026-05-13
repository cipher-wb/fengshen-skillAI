"""patch_30212017_mvp2b_t_accumulator.py — MVP-2b: 真振荡

改动:
1. SkillTag 321001 角色变更: angle_const=30 → angle_accumulator initial=0
2. 新加 ADD_SKILL_TAG_VALUE 302120185: angle_accumulator += 5 (每帧 / omega=5度/帧)
3. REPEAT body ORDER 302120175 Params: [CHANGE_POS] → [ADD_TAG, CHANGE_POS]
4. cos_scaled (302120182): cos / 50 → cos / 100 (振幅 ±100)
5. 加 edges 覆盖新增 NodeRef

⚠ 风险: REPEAT body 多项 Params (2 项) — MVP-1 卡过 / 但 30212010 真实样本能 work / 严格 mimic
"""
import json, uuid
from pathlib import Path

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

guid_by_id = {}
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') is not None:
        guid_by_id[cj['ID']] = r['data']['GUID']

# === 1. SkillTag 321001: angle_const=30 → angle_accumulator initial=0 ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 321001:
        cj['DefaultValue'] = 0
        cj['Desc'] = "MVP2b角度累加器(每帧+=omega)"
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print('[FIX] SkillTag 321001 → angle_accumulator initial=0')
        break

# === 2. Add ADD_SKILL_TAG_VALUE 302120185: angle_accumulator += 5 ===
add_tag_guid = str(uuid.uuid4())
add_tag_node = {
    "rid": 1016,
    "type": {"class": "TSET_ADD_SKILL_TAG_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": add_tag_guid, "computeOrder": 50,
        "position": {"serializedVersion":"2", "x": 1900.0, "y": 700.0, "width":280.0, "height":120.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 302120185, "Desc": "angle_accumulator += 5 (每帧 / omega=5度/帧)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": 302120185, "SkillEffectType": 47,
            "Params": [
                {"Value": 1, "ParamType": 5, "Factor": 0},     # P[0] target=self (主体单位)
                {"Value": 0, "ParamType": 0, "Factor": 0},     # P[1] entity-level Pattern B
                {"Value": 321001, "ParamType": 0, "Factor": 0},  # P[2] SkillTag ID
                {"Value": 5, "ParamType": 0, "Factor": 0},     # P[3] delta = 5
                {"Value": 0, "ParamType": 0, "Factor": 0},     # P[4]
            ],
        }, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_302120185",
        "SkillEffectType": 47,
    }
}
data['references']['RefIds'].append(add_tag_node)
data['nodes'].append({"rid": 1016})
guid_by_id[302120185] = add_tag_guid
print('[ADD] 302120185 ADD_SKILL_TAG angle += 5')

# === 3. REPEAT body ORDER 302120175: Params = [ADD_TAG, CHANGE_POS] ===
# Note: ADD must come BEFORE CHANGE_POS (so this frame uses updated angle).
# Position y must be ordered: ADD top(y=700) → CHANGE_POS bottom(y=1300)
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120175:
        cj['Params'] = [
            {"Value": 302120185, "ParamType": 0, "Factor": 0},  # ADD_TAG first
            {"Value": 302120180, "ParamType": 0, "Factor": 0},  # CHANGE_POS second
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "[每帧 ORDER body] 2 项: 1) ADD angle+=5  2) CHANGE_POS"
        print('[FIX] ORDER body Params = [ADD_TAG, CHANGE_POS] (2 items)')
        break

# === 4. cos_scaled (302120182): cos / 50 → cos / 100 (smaller amplitude) ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120182:
        cj['Params'][2]['Value'] = 100  # was 50
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "cos_scaled = cos / 100 = ±100 振荡 (amplitude reduced from 173 → 100)"
        print('[FIX] 302120182 cos_scaled: cos / 100 (amplitude ±100)')
        break

# === 5. Rewrite edges (add 1 new for body→ADD_TAG; reuse others) ===
def make_edge(target_id, owner_id, output_port='0'):
    return {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": guid_by_id[target_id],
        "outputNodeGUID": guid_by_id[owner_id],
        "inputFieldName": "ID",
        "outputFieldName": "PackedParamsOutput",
        "inputPortIdentifier": "0",
        "outputPortIdentifier": output_port,
        "isVisible": True,
    }

edges_spec = [
    (302120170, 302120171, "0"),
    (302120174, 302120173, "0"),
    (302120175, 302120174, "3"),
    # ORDER body multi-children (dynamic port='0' all)
    (302120185, 302120175, "0"),  # body → ADD_TAG (NEW)
    (302120180, 302120175, "0"),  # body → CHANGE_POS
    # CHANGE_POS children
    (302120177, 302120180, "1"),
    (302120184, 302120180, "2"),
    (302120176, 302120177, "0"),
    (302120181, 302120182, "0"),
    (302120179, 302120184, "0"),
    (302120182, 302120184, "2"),
]
data['edges'] = [make_edge(t, o, p) for (t, o, p) in edges_spec]
print(f'[FIX] edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

# Verify
data2 = json.loads(P.read_text(encoding='utf-8'))
for r in data2['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') == 321001:
        print(f'[VERIFY] SkillTag 321001 DefaultValue={cj.get("DefaultValue")}')
    if cj.get('ID') == 302120175:
        print(f'[VERIFY] ORDER body Params: {[p["Value"] for p in cj["Params"]]}')
    if cj.get('ID') == 302120182:
        print(f'[VERIFY] cos_scaled Params: {[p["Value"] for p in cj["Params"]]}')
    if cj.get('ID') == 302120185:
        print(f'[VERIFY] ADD_TAG exists, Params: {[p["Value"] for p in cj["Params"]]}')
