"""patch_30212017_mvp16_dynamic_n.py — N 子弹数变成 SkillTag + REPEAT 动态生成

旧: 8 个写死的 CREATE_BULLET + 8 个写死视觉 NUM_CALC
新: 1 个 CREATE_BULLET + 1 个 REPEAT_EXECUTE 循环 N 次，每次:
    - GET counter (=当前迭代序号)
    - 动态计算 visual_angle = caster.facing + counter × (360 / N) - 90 + tip_tilt
    - CREATE_BULLET (P[1] = 上面 NodeRef)
    - ADD counter +=1

OnSkillStart 链调整:
  旧 ROOT_ORDER = [reset_vR, A, B, C, D, E, F, G, H]
  新 ROOT_ORDER = [reset_vR, reset_counter, spawn_repeat]

新增:
  - SkillTag 320940 `bullet_count` default 8
  - SkillTag 320941 `iter_counter` 运行时累加器 default 0
  - GET counter / ADD counter +=1 / MODIFY counter = 0 三个工具节点
  - NUM_CALC `angle_step` = counter × 360 / bullet_count
  - NUM_CALC `dynamic_visual_angle` = caster.facing + angle_step - 90 + tip_tilt
  - CREATE_BULLET 统一节点 (P[1] = dynamic_visual_angle)
  - ORDER body
  - REPEAT_EXECUTE: count=bullet_count(PT=3), body=ORDER, interval=1, isImmediate=1

删除:
  - 8 旧 CREATE_BULLET: 32900045/54/61/63/65/67/69/71
  - 8 旧视觉 NUM_CALC: 32900073/59/60/62/64/66/68/70
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

GET_CASTER_FACING_ID = 32900058
TIP_TILT_TAG_ID      = 320939
BULLET_CONFIG_ID     = 320258
ROOT_ORDER_ID        = 32900053

# ====== 分配新 ID ======
alloc = IDAllocator()
existing_st_ids = set()
existing_se_ids = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    nid = cj.get('ID')
    if r['type']['class'] == 'SkillTagsConfigNode':
        existing_st_ids.add(nid)
    elif nid:
        existing_se_ids.add(nid)

bullet_count_tag    = alloc.get_next('SkillTagsConfig')
while bullet_count_tag in existing_st_ids: bullet_count_tag = alloc.get_next('SkillTagsConfig')
iter_counter_tag    = alloc.get_next('SkillTagsConfig')
while iter_counter_tag in existing_st_ids or iter_counter_tag == bullet_count_tag:
    iter_counter_tag = alloc.get_next('SkillTagsConfig')

get_counter_id      = alloc.get_next('SkillEffectConfig')
add_counter_id      = alloc.get_next('SkillEffectConfig')
reset_counter_id    = alloc.get_next('SkillEffectConfig')
angle_step_id       = alloc.get_next('SkillEffectConfig')
dynamic_angle_id    = alloc.get_next('SkillEffectConfig')
dynamic_create_id   = alloc.get_next('SkillEffectConfig')
body_order_id       = alloc.get_next('SkillEffectConfig')
spawn_repeat_id     = alloc.get_next('SkillEffectConfig')

print(f'New SkillTags: bullet_count={bullet_count_tag} / iter_counter={iter_counter_tag}')
print(f'New SkillEffects:')
print(f'  GET counter={get_counter_id}')
print(f'  ADD counter={add_counter_id}')
print(f'  RESET counter={reset_counter_id}')
print(f'  NUM_CALC angle_step={angle_step_id}')
print(f'  NUM_CALC dynamic_visual_angle={dynamic_angle_id}')
print(f'  CREATE_BULLET (统一)={dynamic_create_id}')
print(f'  ORDER body={body_order_id}')
print(f'  REPEAT spawn={spawn_repeat_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

def make_node(rid, ID, cls, set_type, params, desc, pos, table_tash='0CFA05568A66FEA1DF3BA6FE40DB7080'):
    return {
        "rid": rid,
        "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 50,
            "position": {"serializedVersion": "2", "x": float(pos[0]), "y": float(pos[1]), "width": 280.0, "height": 160.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": table_tash,
            "ConfigJson": json.dumps({
                "ID": ID, "SkillEffectType": set_type, "Params": params,
            }, ensure_ascii=False),
            "Config2ID": f"SkillEffectConfig_{ID}",
            "SkillEffectType": set_type,
        }
    }

# ====== 加 2 个 SkillTag ======
def make_st(rid, ID, default, desc, x, y):
    return {
        "rid": rid,
        "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 17,
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
                "NameKey": 0, "DefaultValue": default,
                "FinalValueEffectID": 0, "RetainWhenDie": False,
            }, ensure_ascii=False),
            "Config2ID": f"SkillTagsConfig_{ID}",
        }
    }

NEW_NODES = []
NEW_NODES.append(make_st(next_rid,   bullet_count_tag, 8, '子弹数量（N 颗子弹 / 改 N=12 就 12 颗 / N=4 就 4 颗）', 500, 2900))
NEW_NODES.append(make_st(next_rid+1, iter_counter_tag, 0, '【运行时累加 不要改】子弹生成迭代序号', 500, 3100))

# GET counter
NEW_NODES.append(make_node(next_rid+2, get_counter_id, 'TSET_GET_SKILL_TAG_VALUE', 33, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": iter_counter_tag, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '读「子弹生成迭代序号」/ 0..N-1', (3000, 2900)))

# ADD counter += 1
NEW_NODES.append(make_node(next_rid+3, add_counter_id, 'TSET_ADD_SKILL_TAG_VALUE', 47, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": iter_counter_tag, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '【每次生成后】迭代序号 += 1', (3000, 3100)))

# Reset counter = 0 (OnSkillStart)
NEW_NODES.append(make_node(next_rid+4, reset_counter_id, 'TSET_MODIFY_SKILL_TAG_VALUE', 46, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": iter_counter_tag, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '【OnSkillStart】重置迭代序号 = 0', (2700, 2700)))

# NUM_CALC angle_step = counter × 360 / N (5 项)
NEW_NODES.append(make_node(next_rid+5, angle_step_id, 'TSET_NUM_CALCULATE', 31, [
    {"Value": get_counter_id, "ParamType": 2, "Factor": 0},     # counter
    {"Value": 5, "ParamType": 0, "Factor": 0},                  # MUL
    {"Value": 360, "ParamType": 0, "Factor": 0},                # 360
    {"Value": 6, "ParamType": 0, "Factor": 0},                  # DIV
    {"Value": bullet_count_tag, "ParamType": 3, "Factor": 0},   # N (SkillTag)
], 'angle_step = counter × 360 / N（当前子弹的角度偏移 度）', (3400, 2900)))

# NUM_CALC dynamic_visual_angle = caster.facing + angle_step + (-90) + tip_tilt (7 项)
NEW_NODES.append(make_node(next_rid+6, dynamic_angle_id, 'TSET_NUM_CALCULATE', 31, [
    {"Value": GET_CASTER_FACING_ID, "ParamType": 2, "Factor": 0},  # caster.facing
    {"Value": 3, "ParamType": 0, "Factor": 0},                     # ADD
    {"Value": angle_step_id, "ParamType": 2, "Factor": 0},         # angle_step
    {"Value": 3, "ParamType": 0, "Factor": 0},                     # ADD
    {"Value": -90, "ParamType": 0, "Factor": 0},                   # 视觉补偿
    {"Value": 3, "ParamType": 0, "Factor": 0},                     # ADD
    {"Value": TIP_TILT_TAG_ID, "ParamType": 3, "Factor": 0},       # tip_tilt
], '动态视觉角 = 主角朝向 + counter×(360/N) - 90 + tip_tilt', (3800, 2900)))

# CREATE_BULLET 统一节点
NEW_NODES.append(make_node(next_rid+7, dynamic_create_id, 'TSET_CREATE_BULLET', 8, [
    {"Value": BULLET_CONFIG_ID, "ParamType": 0, "Factor": 0},      # BulletConfig
    {"Value": dynamic_angle_id, "ParamType": 2, "Factor": 0},      # FACE_DIR = 动态视觉角
    {"Value": 59, "ParamType": 1, "Factor": 0},                    # X (caster attr)
    {"Value": 60, "ParamType": 1, "Factor": 0},                    # Y (caster attr)
    {"Value": 1, "ParamType": 5, "Factor": 0},                     # owner = MAIN_ENTITY
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
], '生成 1 颗叶子（由 REPEAT 循环 N 次调用）', (4200, 2900)))

# ORDER body = [dynamic_create, add_counter]
NEW_NODES.append(make_node(next_rid+8, body_order_id, 'TSET_ORDER_EXECUTE', 1, [
    {"Value": dynamic_create_id, "ParamType": 0, "Factor": 0},
    {"Value": add_counter_id, "ParamType": 0, "Factor": 0},
], '【REPEAT body】1.生成 1 颗叶子 / 2.序号 +=1', (4600, 2900)))

# REPEAT_EXECUTE: count=N(PT=3), body=ORDER, isImmediate=1
NEW_NODES.append(make_node(next_rid+9, spawn_repeat_id, 'TSET_REPEAT_EXECUTE', 3, [
    {"Value": 1, "ParamType": 0, "Factor": 0},                     # interval=1 (immediate 下其实不影响)
    {"Value": bullet_count_tag, "ParamType": 3, "Factor": 0},      # count = bullet_count SkillTag
    {"Value": 1, "ParamType": 0, "Factor": 0},                     # isImmediate=1
    {"Value": body_order_id, "ParamType": 0, "Factor": 0},         # body
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
], '【REPEAT】循环 N 次（同帧）/ 每次生成 1 颗叶子 + 序号+1', (5000, 2900)))

for n in NEW_NODES:
    data['references']['RefIds'].append(n)
    data['nodes'].append({"rid": n['rid']})
print(f'[ADD] {len(NEW_NODES)} nodes')

# ====== 修改 ROOT_ORDER 32900053: 移除 8 CREATE_BULLET / 加 reset_counter + spawn_repeat ======
OBSOLETE_CREATES = {32900045, 32900054, 32900061, 32900063, 32900065, 32900067, 32900069, 32900071}
OBSOLETE_VISUALS = {32900073, 32900059, 32900060, 32900062, 32900064, 32900066, 32900068, 32900070}
ALL_DEL_IDS = OBSOLETE_CREATES | OBSOLETE_VISUALS

for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == ROOT_ORDER_ID:
        # 保留 reset_vR (32900052) 等，移除 8 CREATE_BULLET, 加新 2 个
        keep = [p for p in cj['Params'] if p['Value'] not in OBSOLETE_CREATES]
        keep.append({"Value": reset_counter_id, "ParamType": 0, "Factor": 0})
        keep.append({"Value": spawn_repeat_id, "ParamType": 0, "Factor": 0})
        cj['Params'] = keep
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = '【OnSkillStart 总入口】1.重置半径累加 / 2.重置迭代序号 / 3.REPEAT 生成 N 颗子弹'
        print(f'[FIX] ROOT_ORDER Params: 8 CREATE → reset_counter + spawn_repeat')
        break

# ====== 删除 16 个废弃节点 ======
del_guids = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') in ALL_DEL_IDS:
        del_guids.add(r['data']['GUID'])

old_count = len(data['references']['RefIds'])
data['references']['RefIds'] = [r for r in data['references']['RefIds']
                                  if r['data']['GUID'] not in del_guids]
remaining_rids = set(r['rid'] for r in data['references']['RefIds'])
data['nodes'] = [n for n in data['nodes'] if n['rid'] in remaining_rids]
print(f'[DEL] {old_count - len(data["references"]["RefIds"])} obsolete nodes (8 CREATE + 8 NUM_CALC)')

# 删 edges
old_edges = len(data['edges'])
data['edges'] = [e for e in data['edges']
                  if e['inputNodeGUID'] not in del_guids and e['outputNodeGUID'] not in del_guids]
print(f'[DEL] {old_edges - len(data["edges"])} edges')

# ====== Edges ======
guid_by_id = {json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID'): r['data']['GUID']
               for r in data['references']['RefIds']
               if json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID') is not None}

def make_edge(target_id, owner_id, outport='0'):
    return {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": guid_by_id[target_id],
        "outputNodeGUID": guid_by_id[owner_id],
        "inputFieldName": "ID", "outputFieldName": "PackedParamsOutput",
        "inputPortIdentifier": "0", "outputPortIdentifier": outport, "isVisible": True,
    }

# angle_step: get_counter(P[0])
data['edges'].append(make_edge(get_counter_id, angle_step_id, "0"))
# dynamic_angle: caster.facing(P[0]) + angle_step(P[2])
data['edges'].append(make_edge(GET_CASTER_FACING_ID, dynamic_angle_id, "0"))
data['edges'].append(make_edge(angle_step_id, dynamic_angle_id, "2"))
# dynamic_create: dynamic_angle → P[1]
data['edges'].append(make_edge(dynamic_angle_id, dynamic_create_id, "1"))
# body ORDER: dynamic_create + add_counter
data['edges'].append(make_edge(dynamic_create_id, body_order_id, "0"))
data['edges'].append(make_edge(add_counter_id, body_order_id, "0"))
# spawn_repeat: body → P[3]
data['edges'].append(make_edge(body_order_id, spawn_repeat_id, "3"))
# ROOT_ORDER: reset_counter + spawn_repeat → P[0]
data['edges'].append(make_edge(reset_counter_id, ROOT_ORDER_ID, "0"))
data['edges'].append(make_edge(spawn_repeat_id, ROOT_ORDER_ID, "0"))
print(f'[ADD] 9 edges')

# ====== 更新 sticky note ======
for n in data.get('stickyNotes', []):
    if '风车' in n.get('title', ''):
        content = n['content']
        # 在 SkillTag 参数段加 bullet_count 段
        insert_pos = content.find('▌出生位置')
        if insert_pos > 0:
            new_section = f"""▌子弹数量
  {bullet_count_tag}「bullet_count」= 8 默认
    叶子总数 / 改 N=4 就 4 颗 / N=12 就 12 颗 / N=16 就 16 颗
    每颗角度自动 = (360 / N) × 序号 → 永远均匀分布

"""
            content = content[:insert_pos] + new_section + content[insert_pos:]
        # 速查里加一条
        qpos = content.find('【速查')
        if qpos > 0:
            speed_lines = '【速查：想要什么效果 → 改哪个】\n  改子弹数量 → 调 ' + str(bullet_count_tag) + '（如 N=12 / N=4）'
            content = content.replace('【速查：想要什么效果 → 改哪个】', speed_lines)
        # 加一条「运行时存储」
        runtime_section = '▌运行时存储（不要改！）'
        rt_pos = content.find(runtime_section)
        if rt_pos > 0:
            new_rt = f'▌运行时存储（不要改！）\n  {iter_counter_tag} 子弹生成迭代序号'
            content = content.replace(runtime_section, new_rt)
        n['content'] = content
        print('[FIX] sticky note 加 bullet_count + 改成动态 N')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(data["references"]["RefIds"])} / edges={len(data["edges"])}')
