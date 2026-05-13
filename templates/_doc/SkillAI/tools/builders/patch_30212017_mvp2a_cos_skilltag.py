"""patch_30212017_mvp2a_cos_skilltag.py — MVP-2a 增量

目标：在 MVP-1 基础上验证 cos 节点 + SkillTag + 浮动节点多层链。
效果：子弹 X 仍直线右移 / Y 加 cos(30°)*50/10000 偏移（cos 是常数 → Y 出生瞬间跳一下偏移然后保持）。

新增 3 节点：
1. SkillTag 321001 (angle_const, DefaultValue=30)
2. MATH_COS 302120181 (input=SkillTag 321001 PT=3) → cos(30°)
3. NUM_CALC 302120182 (chain: GET_Y + cos*50/10000) — 7 项 Params 链式

NUM_CALC 操作符（30212010 grep 验证）：3=ADD / 5=MUL / 6=DIV / 7=MOD

修改：
- CHANGE_POSITION P[2] 由 {V=GET_Y, PT=2} 改 {V=newY_NUM_CALC, PT=2}

edges：删 1（CHANGE_POSITION→GET_Y）/ 加 3（CHANGE_POSITION→newY_NUM_CALC, NUM_CALC→GET_Y, NUM_CALC→COS）

PT=3 (TPT_SKILL_PARAM SkillTag ref) 不需要 edge（通过 ID 直接查表）— 仿 30212010 cos→SkillTag 1006 无边。
"""
import json, uuid
from pathlib import Path

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

# Find GUIDs
guid_by_id = {}
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') is not None:
        guid_by_id[cj['ID']] = r['data']['GUID']

# === Add new nodes ===
skilltag_guid = str(uuid.uuid4())
cos_guid = str(uuid.uuid4())
newy_calc_guid = str(uuid.uuid4())

# 1. SkillTag 321001 (entity-level Pattern B / angle constant)
skilltag_node = {
    "rid": 1012,
    "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": skilltag_guid, "computeOrder": 5,
        "position": {"serializedVersion":"2", "x": 2700.0, "y": 1500.0, "width":237.0, "height":135.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 321001, "Desc": "SkillTag 声明",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
        "ConfigJson": json.dumps({
            "ID": 321001,
            "TagType": 0,
            "Desc": "MVP2a角度常量(用于cos输入)",
            "NameKey": 0,
            "DefaultValue": 30,
            "FinalValueEffectID": 0,
            "RetainWhenDie": False,
        }, ensure_ascii=False),
        "Config2ID": "SkillTagsConfig_321001",
    }
}

# 2. MATH_COS (Type=51) — input is SkillTag 321001 via PT=3
cos_node = {
    "rid": 1013,
    "type": {"class": "TSET_MATH_COS", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": cos_guid, "computeOrder": 80,
        "position": {"serializedVersion":"2", "x": 3000.0, "y": 1500.0, "width":200.0, "height":80.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 302120181, "Desc": "cos(angle_SkillTag) 输出 [-10000, 10000] 定点化",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": 302120181, "SkillEffectType": 51,
            "Params": [{"Value": 321001, "ParamType": 3, "Factor": 0}],
        }, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_302120181",
        "SkillEffectType": 51,
    }
}

# 3. NUM_CALC newY chain: GET_Y + cos*50/10000 (7 params chain)
# Operators (validated from 30212010): 3=ADD 5=MUL 6=DIV
newy_calc_node = {
    "rid": 1014,
    "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": newy_calc_guid, "computeOrder": 120,
        "position": {"serializedVersion":"2", "x": 3300.0, "y": 1500.0, "width":300.0, "height":160.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x":0.0,"y":0.0}, "hideCounter": 0,
        "ID": 302120182, "Desc": "newY = self.Y + cos(30°)*50/10000 (链式 NUM_CALC / 仿 30212010 66001758)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": 302120182, "SkillEffectType": 31,
            "Params": [
                {"Value": 302120179, "ParamType": 2, "Factor": 0},  # GET_Y
                {"Value": 3, "ParamType": 0, "Factor": 0},          # ADD
                {"Value": 302120181, "ParamType": 2, "Factor": 0},  # COS
                {"Value": 5, "ParamType": 0, "Factor": 0},          # MUL
                {"Value": 50, "ParamType": 0, "Factor": 0},         # 50
                {"Value": 6, "ParamType": 0, "Factor": 0},          # DIV
                {"Value": 10000, "ParamType": 0, "Factor": 0},      # /10000
            ],
        }, ensure_ascii=False),
        "Config2ID": "SkillEffectConfig_302120182",
        "SkillEffectType": 31,
    }
}

data['references']['RefIds'].append(skilltag_node)
data['references']['RefIds'].append(cos_node)
data['references']['RefIds'].append(newy_calc_node)
data['nodes'].append({"rid": 1012})
data['nodes'].append({"rid": 1013})
data['nodes'].append({"rid": 1014})

guid_by_id[321001] = skilltag_guid
guid_by_id[302120181] = cos_guid
guid_by_id[302120182] = newy_calc_guid

print(f'[ADD] SkillTag 321001 / COS 302120181 / NUM_CALC 302120182')

# === Modify CHANGE_POSITION P[2]: GET_Y ref → newY_calc ref ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120180:  # CHANGE_POSITION
        cj['Params'][2] = {"Value": 302120182, "ParamType": 2, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] CHANGE_POSITION P[2] = newY_calc (302120182)')
        break

# === Rewrite edges ===
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
    # MVP-1 框架
    (302120170, 302120171, "0"),  # CREATE_BULLET P[0] = BulletConfig
    (302120174, 302120173, "0"),  # AfterBorn ORDER P[0] = REPEAT
    (302120175, 302120174, "3"),  # REPEAT P[3] = ORDER body
    (302120180, 302120175, "0"),  # ORDER body P[0] = CHANGE_POSITION (only 1 item)
    (302120177, 302120180, "1"),  # CHANGE_POSITION P[1] = newX NUM_CALC
    (302120182, 302120180, "2"),  # CHANGE_POSITION P[2] = newY NUM_CALC (NEW - was GET_Y)
    (302120176, 302120177, "0"),  # newX NUM_CALC P[0] = GET_X

    # MVP-2a 新增
    (302120179, 302120182, "0"),  # newY NUM_CALC P[0] = GET_Y
    (302120181, 302120182, "2"),  # newY NUM_CALC P[2] = COS
]
data['edges'] = [make_edge(t, o, p) for (t, o, p) in edges_spec]
print(f'[FIX] edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

# Self-verify (grep mode)
data2 = json.loads(P.read_text(encoding='utf-8'))
ids_present = set()
for r in data2['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') is not None:
        ids_present.add(cj['ID'])
required = {30212017, 302120170, 302120171, 302120173, 302120174, 302120175,
            302120176, 302120177, 302120179, 302120180, 302120181, 302120182, 321001}
missing = required - ids_present
extra = ids_present - required - {302120172}  # ModelConfig 3200303 or similar
print(f'\n[VERIFY] node IDs OK: missing={missing}')
print(f'[VERIFY] total RefIds = {len(data2["references"]["RefIds"])}')
print(f'[VERIFY] total edges = {len(data2["edges"])}')

# Verify CHANGE_POSITION P[2]
for r in data2['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') == 302120180:
        print(f'[VERIFY] CHANGE_POSITION P[2] = {cj["Params"][2]}')
        assert cj['Params'][2]['Value'] == 302120182, 'P[2] not updated!'
        print('[OK] verified')
