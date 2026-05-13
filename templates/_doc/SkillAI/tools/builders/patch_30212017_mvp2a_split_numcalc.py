"""patch_30212017_mvp2a_split_numcalc.py

修复 MVP-2a：链式 NUM_CALC 左结合，把"Y + cos*50/10000"拆成 2 个节点。

旧（错）：
  302120182 (newY) 7 项链式：
    P[0]=GET_Y P[1]=3(ADD) P[2]=COS P[3]=5(MUL) P[4]=50 P[5]=6(DIV) P[6]=10000
  = ((Y+cos)*50)/10000 = (43+8660)*50/10000 = 43.5 → 43 (整数截断 / Y 不变)

新（对）：
  302120182 (cos_scaled): COS / 50 = 8660/50 = 173
    P[0]=COS (PT=2) P[1]=6(DIV) P[2]=50

  302120184 (newY): GET_Y + cos_scaled = 43+173 = 216  ← Y 偏移 173 可见
    P[0]=GET_Y (PT=2) P[1]=3(ADD) P[2]=302120182 (PT=2)

CHANGE_POSITION P[2] 改引用 302120184 (而非旧的 302120182)
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

# === 1. Repurpose 302120182 as cos_scaled (3 项 / cos/50) ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120182:
        cj['Params'] = [
            {"Value": 302120181, "ParamType": 2, "Factor": 0},  # COS
            {"Value": 6, "ParamType": 0, "Factor": 0},          # DIV
            {"Value": 50, "ParamType": 0, "Factor": 0},         # /50
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "cos_scaled = cos / 50 (= 173 当 cos(30°)=8660)"
        print('[FIX] 302120182 (cos_scaled): COS / 50')
        break

# === 2. Add new NUM_CALC 302120184 newY = GET_Y + cos_scaled ===
newy_calc_guid = str(uuid.uuid4())
newy_calc_node = {
    "rid": 1015,
    "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": newy_calc_guid, "computeOrder": 130,
        "position": {"serializedVersion":"2", "x": 3500.0, "y": 1500.0, "width":300.0, "height":140.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 302120184,
        "Desc": "newY = GET_Y + cos_scaled (3 项 / 拆解链式优先级避免左结合截断)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": 302120184, "SkillEffectType": 31,
            "Params": [
                {"Value": 302120179, "ParamType": 2, "Factor": 0},  # GET_Y
                {"Value": 3, "ParamType": 0, "Factor": 0},          # ADD
                {"Value": 302120182, "ParamType": 2, "Factor": 0},  # cos_scaled
            ],
        }, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_302120184",
        "SkillEffectType": 31,
    }
}
data['references']['RefIds'].append(newy_calc_node)
data['nodes'].append({"rid": 1015})
guid_by_id[302120184] = newy_calc_guid
print('[ADD] 302120184 newY = GET_Y + cos_scaled')

# === 3. CHANGE_POSITION P[2]: 302120182 → 302120184 ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120180:
        cj['Params'][2] = {"Value": 302120184, "ParamType": 2, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print('[FIX] CHANGE_POSITION P[2] = newY_final (302120184)')
        break

# === 4. Rewrite edges ===
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
    (302120180, 302120175, "0"),
    (302120177, 302120180, "1"),  # CHANGE_POS P[1] = newX
    (302120184, 302120180, "2"),  # CHANGE_POS P[2] = newY_final (CHANGED)
    (302120176, 302120177, "0"),  # newX.P[0] = GET_X
    (302120181, 302120182, "0"),  # cos_scaled.P[0] = COS (CHANGED)
    (302120179, 302120184, "0"),  # newY_final.P[0] = GET_Y
    (302120182, 302120184, "2"),  # newY_final.P[2] = cos_scaled
]
data['edges'] = [make_edge(t, o, p) for (t, o, p) in edges_spec]
print(f'[FIX] edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

# Verify
data2 = json.loads(P.read_text(encoding='utf-8'))
for r in data2['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') == 302120182:
        print(f'[VERIFY] 302120182 cos_scaled Params: {[p["Value"] for p in cj["Params"]]}')
    if cj.get('ID') == 302120184:
        print(f'[VERIFY] 302120184 newY_final Params: {[p["Value"] for p in cj["Params"]]}')
    if cj.get('ID') == 302120180:
        print(f'[VERIFY] 302120180 CHANGE_POS P[2]: {cj["Params"][2]}')
