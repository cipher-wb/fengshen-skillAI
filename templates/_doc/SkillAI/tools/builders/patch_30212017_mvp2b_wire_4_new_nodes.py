"""patch_30212017_mvp2b_wire_4_new_nodes.py — MVP-2b 把用户在 SkillEditor 里创建的 4 节点配通

用户 SkillEditor 创建的 4 个节点（保留 SkillEditor 给的 ID 和 GUID）：
  320198    SkillTagsConfigNode      angle 累加器 (DefaultValue=0)
  32900035  TSET_ADD_SKILL_TAG_VALUE  每帧 angle += 5
  32900036  TSET_GET_SKILL_TAG_VALUE  读 angle 当前值
  32900037  TSET_MATH_COS             cos(angle)

填 Params:
  32900035 P[2]={V=320198, PT=0} / P[3]={V=5, PT=0}
  32900036 P[2]={V=320198, PT=0}
  32900037 P[0]={V=32900036, PT=2 NodeRef GET 输出}
  302120184 NUM_CALC newY 链式 = GET_Y + cos/100

改 ORDER body 302120175 Params: [ADD_SKILL_TAG_NEW, CHANGE_POSITION]（2 项 / 动态端口=0）
改 CHANGE_POSITION 302120180 P[2]: GET_Y → newY NUM_CALC 302120184

加 edges:
  ADD_SKILL_TAG ← ORDER body (P[0] 仿动态端口)
  GET_SKILL_TAG → MATH_COS.input (PT=2 NodeRef)
  GET_Y → NUM_CALC 302120184.input
  MATH_COS → NUM_CALC 302120184.P[2]
  NUM_CALC 302120184 → CHANGE_POSITION.P[2]
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

print(f'GUID map size: {len(guid_by_id)}')

# === Patch ADD_SKILL_TAG 32900035: P[2]=320198 P[3]=5 ===
# (P[0]=4 PT=5, P[1]=41 PT=5 保留 SkillEditor 默认)
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 32900035:
        cj['Params'][2] = {'Value': 320198, 'ParamType': 0, 'Factor': 0}  # SkillTag ID
        cj['Params'][3] = {'Value': 5, 'ParamType': 0, 'Factor': 0}        # delta = 5
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] 32900035 ADD_SKILL_TAG P[2]=320198 P[3]=5')
        break

# === Patch GET_SKILL_TAG 32900036: P[2]=320198 ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 32900036:
        cj['Params'][2] = {'Value': 320198, 'ParamType': 0, 'Factor': 0}  # SkillTag ID
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] 32900036 GET_SKILL_TAG P[2]=320198')
        break

# === Patch MATH_COS 32900037: P[0]={V=32900036, PT=2 NodeRef} ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 32900037:
        cj['Params'] = [{'Value': 32900036, 'ParamType': 2, 'Factor': 0}]  # GET_SKILL_TAG output ref
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] 32900037 MATH_COS P[0]=NodeRef(32900036)')
        break

# === Patch NUM_CALC 302120184: newY = GET_Y + MATH_COS / 100 ===
# Formula left-to-right: ((GET_Y ADD cos) DIV 100) — but we want GET_Y + (cos/100)
# Chain: P0=GET_Y, op=ADD, P2=cos, op=DIV, P4=100 → ((GET_Y + cos) / 100) — WRONG
# Need 2 nodes for proper math priority. Reuse 302120184 as "cos / 100", reuse another
# Actually: try with chain ((GET_Y + cos) / 100) = (43+8660)/100 = 87 ≈ GET_Y ≈ same as Y
# Let me use simpler: newY = GET_Y + (cos / 100)
# Since 302120184 exists, set it as: P0=GET_Y, op=ADD, P2=cos
# AND change CHANGE_POS to use this output — cos in this case is from 32900037 raw
# Use raw cos and accept large amplitude: newY = GET_Y + cos (range ±10000 = ±10000 units = too far)
# Better: do GET_Y + (cos/100). Need to chain in 302120184: P0=cos, op=DIV, P2=100, op=ADD, P4=GET_Y
# Left-to-right: ((cos / 100) + GET_Y) = (8660/100)+43 = 86+43 = 129 ✓ visible
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120184:
        cj['Params'] = [
            {'Value': 32900037, 'ParamType': 2, 'Factor': 0},   # cos (NodeRef)
            {'Value': 6, 'ParamType': 0, 'Factor': 0},          # DIV
            {'Value': 100, 'ParamType': 0, 'Factor': 0},        # 100
            {'Value': 3, 'ParamType': 0, 'Factor': 0},          # ADD
            {'Value': 302120179, 'ParamType': 2, 'Factor': 0},  # GET_Y (NodeRef)
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "newY = (cos / 100) + GET_Y  (链式左结合 / 振幅 ±100)"
        print(f'[FIX] 302120184 NUM_CALC newY: (cos/100) + GET_Y')
        break

# === Patch CHANGE_POSITION 302120180 P[2]: GET_Y → NUM_CALC newY (302120184) ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120180:
        cj['Params'][2] = {'Value': 302120184, 'ParamType': 2, 'Factor': 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] 302120180 CHANGE_POS P[2] = NUM_CALC newY (302120184)')
        break

# === Patch ORDER body 302120175: Params = [ADD_SKILL_TAG, CHANGE_POSITION] ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson','{}') or '{}'
    if not cj_str: continue
    cj = json.loads(cj_str)
    if cj.get('ID') == 302120175:
        cj['Params'] = [
            {'Value': 32900035, 'ParamType': 0, 'Factor': 0},   # ADD_SKILL_TAG_NEW (first)
            {'Value': 302120180, 'ParamType': 0, 'Factor': 0},  # CHANGE_POSITION (second)
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "[每帧 ORDER body] 2 项: ADD angle+=5 → CHANGE_POS"
        print(f'[FIX] 302120175 ORDER body: [ADD_SKILL_TAG, CHANGE_POSITION]')
        break

# === Adjust positions for SkillEditor sort (ORDER children by position.y asc) ===
# ADD_SKILL_TAG should come BEFORE CHANGE_POSITION → ADD lower y, CHANGE higher y
add_skilltag_node = None
change_pos_node = None
for r in data['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    if cj.get('ID') == 32900035:
        add_skilltag_node = r
    elif cj.get('ID') == 302120180:
        change_pos_node = r
if add_skilltag_node and change_pos_node:
    add_skilltag_node['data']['position']['y'] = 500.0
    change_pos_node['data']['position']['y'] = 1500.0
    print(f'[FIX] Position y: ADD_SKILL_TAG=500 / CHANGE_POS=1500 (确保 ORDER 排序)')

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
    # Bullet creation chain (already work)
    (302120170, 302120171, "0"),   # CREATE_BULLET → BulletConfig
    (302120174, 302120173, "0"),   # AfterBorn → REPEAT
    (302120175, 302120174, "3"),   # REPEAT → body (REPEAT.P[3] body / not dynamic-port)

    # ORDER body multi-children (dynamic port='0')
    (32900035, 302120175, "0"),    # body → ADD_SKILL_TAG_NEW
    (302120180, 302120175, "0"),   # body → CHANGE_POSITION

    # CHANGE_POSITION inputs
    (302120177, 302120180, "1"),   # CHANGE_POS P[1] = newX NUM_CALC
    (302120184, 302120180, "2"),   # CHANGE_POS P[2] = newY NUM_CALC

    # newX chain
    (302120176, 302120177, "0"),   # newX P[0] = GET_X

    # newY chain (cos / 100 + GET_Y)
    (32900037, 302120184, "0"),    # newY P[0] = cos
    (302120179, 302120184, "4"),   # newY P[4] = GET_Y

    # cos input
    (32900036, 32900037, "0"),     # cos P[0] = GET_SKILL_TAG
]
data['edges'] = [make_edge(t, o, p) for (t, o, p) in edges_spec]
print(f'[FIX] edges = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

# Verify
data2 = json.loads(P.read_text(encoding='utf-8'))
print(f'\n[VERIFY] total RefIds = {len(data2["references"]["RefIds"])}')
print(f'[VERIFY] total edges = {len(data2["edges"])}')
for r in data2['references']['RefIds']:
    cj = json.loads(r['data'].get('ConfigJson','{}') or '{}')
    ID = cj.get('ID')
    if ID in (32900035, 32900036, 32900037, 302120184, 302120180, 302120175):
        print(f'  ID={ID}: {[(p["Value"], p["ParamType"]) for p in cj.get("Params",[])]}')
