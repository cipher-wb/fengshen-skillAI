"""build_30212018_yesan_fengxing_poc.py — 新技能 30212018「叶散风行 PoC」

从 30212017 文件复制 → 改造成强化/普通双 BulletConfig + buff 判断的版本

不改原 30212010 / 30212017 / 320110 / 320112 / 32003149 / 32003150 / 320358。

==== 改造内容 ====
1. 复制 30212017.json → 30212018.json
2. 全部 SkillEffect/BulletConfig/SkillTag/Model 节点 ID 重分配（避开当前全工程已用）
3. 改 SkillConfigNode.ID 30212017 → 30212018
4. 删除 BulletConfig 320258（30212017 还在用 / 30212018 用新的）
5. 加 2 个新 BulletConfig:
   - 强化版（复制 320110，FlyType=0 Speed=0，AfterBorn=风车 OnTick 强化）
   - 普通版（复制 320112，同上，AfterBorn=风车 OnTick 普通）
6. 复制风车 OnTick body（reallocated 后）→ 2 个 ORDER 包装版（追加 32003150 / 32003149 引用）
7. body ORDER 改造：
   - 旧 [CREATE_BULLET, ADD counter]
   - 新 [CONDITION_EXECUTE, ADD counter]
     - CONDITION: AND[320358, counter%3==2]
     - true: CREATE 强化 / false: CREATE 普通
8. 删除旧单 CREATE_BULLET
9. 改 sticky note + 文件 path
"""
import json, uuid, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator, cls_to_table

SRC = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
DST = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212018【PoC】叶散风行.json')

print(f'Copying {SRC.name} → {DST.name}')
shutil.copyfile(SRC, DST)
data = json.loads(DST.read_text(encoding='utf-8'))

# ============ Phase 1: 重分配所有节点 ID（避开全工程已用）============
alloc = IDAllocator(exclude_files={str(SRC), str(DST)})

id_map = {}  # old_id → new_id
for r in data['references']['RefIds']:
    cls = r['type']['class']
    table = cls_to_table(cls)
    if not table or table == 'SkillConfig':
        continue
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try:
        cj = json.loads(cj_str)
    except Exception:
        continue
    old_id = cj.get('ID')
    if not isinstance(old_id, int) or old_id == 0:
        continue
    new_id = alloc.get_next(table)
    id_map[old_id] = new_id

print(f'Reallocations: {len(id_map)}')

# 替换所有引用（深度遍历）
def replace_in_obj(obj):
    if isinstance(obj, dict):
        return {k: replace_in_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_in_obj(v) for v in obj]
    if isinstance(obj, int) and obj in id_map:
        return id_map[obj]
    return obj

for r in data['references']['RefIds']:
    # data.ID
    if isinstance(r['data'].get('ID'), int) and r['data']['ID'] in id_map:
        r['data']['ID'] = id_map[r['data']['ID']]
    # data.Config2ID 字符串替换（如 "SkillEffectConfig_32900045"）
    if 'Config2ID' in r['data'] and isinstance(r['data']['Config2ID'], str):
        for old, new in id_map.items():
            r['data']['Config2ID'] = r['data']['Config2ID'].replace(f'_{old}', f'_{new}')
    # ConfigJson 内部所有引用
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    try:
        cj = json.loads(cj_str)
        cj_new = replace_in_obj(cj)
        r['data']['ConfigJson'] = json.dumps(cj_new, ensure_ascii=False)
    except Exception:
        pass
    # data.Desc 内的数字引用
    if 'Desc' in r['data'] and isinstance(r['data']['Desc'], str):
        d = r['data']['Desc']
        for old, new in sorted(id_map.items(), key=lambda x:-x[0]):  # 长 ID 先替换 防 substring
            d = d.replace(str(old), str(new))
        r['data']['Desc'] = d

print('All references updated')

# ============ Phase 2: 改 SkillConfig ID 30212017 → 30212018 ============
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if r['type']['class'] == 'SkillConfigNode' and cj.get('ID') == 30212017:
        cj['ID'] = 30212018
        r['data']['ID'] = 30212018
        r['data']['Config2ID'] = 'SkillConfig_30212018'
        r['data']['Desc'] = '30212018 [PoC] 叶散风行\n8 颗叶子风车扩散 + 每 3 发第 3 强化 (复用 320358 三重碧叶 buff)\nBulletConfig 强化/普通双版'
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print('[FIX] SkillConfigNode: 30212017 → 30212018')
        break

# ============ Phase 3: 删除 BulletConfig 320258 (30212017 用的) ============
del_guids = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if r['type']['class'] == 'BulletConfigNode' and cj.get('ID') == 320258:
        del_guids.add(r['data']['GUID'])
old_n = len(data['references']['RefIds'])
data['references']['RefIds'] = [r for r in data['references']['RefIds'] if r['data']['GUID'] not in del_guids]
remaining_rids = set(r['rid'] for r in data['references']['RefIds'])
data['nodes'] = [n for n in data['nodes'] if n['rid'] in remaining_rids]
data['edges'] = [e for e in data['edges'] if e['inputNodeGUID'] not in del_guids and e['outputNodeGUID'] not in del_guids]
print(f'[DEL] {old_n - len(data["references"]["RefIds"])} BulletConfig 320258 node + edges')

# ============ Phase 4: 找现有关键节点（reallocated ID）============
# 我们要找 reallocated 后的：
# - 原 32900046 OnTick body ORDER
# - 原 32900090 body ORDER
# - 原 32900089 dynamic CREATE_BULLET
# - 原 32900091 REPEAT
# - 原 32900088 dynamic_visual_angle
# - 原 32900084 GET counter

# 旧 ID → 新 ID
def n(old): return id_map.get(old, old)
old_ontick_order   = n(32900046)
old_body_order     = n(32900090)
old_dyn_create     = n(32900089)
old_repeat         = n(32900091)
old_dyn_angle      = n(32900088)
old_get_counter    = n(32900084)
old_root_order     = n(32900053)
old_add_counter    = n(32900085)
old_before_order   = n(32900080)
print(f'OnTick ORDER (was 32900046): {old_ontick_order}')
print(f'body ORDER (was 32900090): {old_body_order}')
print(f'REPEAT (was 32900091): {old_repeat}')
print(f'BeforeBorn ORDER (was 32900080): {old_before_order}')

# ============ Phase 5: 加 2 个新 BulletConfig (强化 / 普通) ============
# 从 30212010 蓝图读 src_premium (320110) / src_normal (320112)
PG = json.loads(Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212010【木宗门】奇术_人阶_叶散风行.json').read_text(encoding='utf-8'))
src_premium = None
src_normal = None
for r in PG['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if r['type']['class'] == 'BulletConfigNode':
        if cj.get('ID') == 320110: src_premium = cj
        elif cj.get('ID') == 320112: src_normal = cj
assert src_premium and src_normal

# 加 2 个 OnTick wrapper ORDER（在新 BulletConfig.AfterBorn 用）
# 强化版 = [原 OnTick body (reallocated), 32003150]
# 普通版 = [原 OnTick body (reallocated), 32003149]
alloc2 = IDAllocator(exclude_files={str(SRC)})
# 别忘了新分配也要避开当前 30212018 已用
existing_se = set()
existing_bc = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    nid = cj.get('ID')
    if r['type']['class'] == 'BulletConfigNode': existing_bc.add(nid)
    elif nid: existing_se.add(nid)

def alloc_se():
    while True:
        x = alloc2.get_next('SkillEffectConfig')
        if x not in existing_se: existing_se.add(x); return x
def alloc_bc():
    while True:
        x = alloc2.get_next('BulletConfig')
        if x not in existing_bc: existing_bc.add(x); return x

ontick_prem_order_id = alloc_se()
ontick_norm_order_id = alloc_se()
new_bc_premium_id    = alloc_bc()
new_bc_normal_id     = alloc_bc()
counter_mod3_id      = alloc_se()
counter_eq2_cond_id  = alloc_se()
strong_and_cond_id   = alloc_se()
create_premium_id    = alloc_se()
create_normal_id     = alloc_se()
condition_exec_id    = alloc_se()

print(f'New: ontick_prem={ontick_prem_order_id} / ontick_norm={ontick_norm_order_id}')
print(f'     BC 强化={new_bc_premium_id} / BC 普通={new_bc_normal_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

def add_node(rid, ID, cls, set_type, params, desc, table_tash='0CFA05568A66FEA1DF3BA6FE40DB7080'):
    node = {
        "rid": rid,
        "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 50,
            "position": {"serializedVersion": "2", "x": 6500.0, "y": float(rid * 30), "width": 280.0, "height": 160.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": table_tash,
            "ConfigJson": json.dumps({"ID": ID, "SkillEffectType": set_type, "Params": params}, ensure_ascii=False),
            "Config2ID": f"SkillEffectConfig_{ID}",
            "SkillEffectType": set_type,
        }
    }
    data['references']['RefIds'].append(node)
    data['nodes'].append({"rid": rid})
    return rid + 1

# OnTick wrapper ORDER (强化版): [原 OnTick body, 32003150]
next_rid = add_node(next_rid, ontick_prem_order_id, 'TSET_ORDER_EXECUTE', 1, [
    {"Value": old_ontick_order, "ParamType": 0, "Factor": 0},
    {"Value": 32003150, "ParamType": 0, "Factor": 0},  # 跨蓝图引用 30212010 强化子弹链
], '【强化子弹 AfterBorn】风车 OnTick + 引用 30212010.32003150 碰撞伤害')

next_rid = add_node(next_rid, ontick_norm_order_id, 'TSET_ORDER_EXECUTE', 1, [
    {"Value": old_ontick_order, "ParamType": 0, "Factor": 0},
    {"Value": 32003149, "ParamType": 0, "Factor": 0},  # 跨蓝图引用 30212010 普通子弹链
], '【普通子弹 AfterBorn】风车 OnTick + 引用 30212010.32003149 碰撞伤害')

# 新 BulletConfig × 2
def add_bc(rid, ID, src, desc, after_born, before_born):
    cj = dict(src)
    cj['ID'] = ID
    cj['FlyType'] = 0
    cj['Speed'] = 0
    cj['MaxSpeed'] = 0
    cj['AcceSpeed'] = 0
    cj['MaxDistance'] = 0
    cj['LastTime'] = 120
    cj['LifeFlag'] = 1
    cj['AfterBornSkillEffectExecuteInfo'] = {'SelectConfigID': 0, 'SkillEffectConfigID': after_born}
    cj['BeforeBornSkillEffectExecuteInfo'] = {'SelectConfigID': 0, 'SkillEffectConfigID': before_born}
    node = {
        "rid": rid,
        "type": {"class": "BulletConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 20,
            "position": {"serializedVersion": "2", "x": 7000.0, "y": float(rid * 30), "width": 280.0, "height": 400.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "DEFAULT_BULLET",
            "ConfigJson": json.dumps(cj, ensure_ascii=False),
            "Config2ID": f"BulletConfig_{ID}",
        }
    }
    data['references']['RefIds'].append(node)
    data['nodes'].append({"rid": rid})
    return rid + 1

next_rid = add_bc(next_rid, new_bc_premium_id, src_premium,
    '【风车版强化叶刃】复制 320110 / FlyType=0 / 风车 OnTick + 32003150 碰撞伤害',
    ontick_prem_order_id, old_before_order)
next_rid = add_bc(next_rid, new_bc_normal_id, src_normal,
    '【风车版普通叶刃】复制 320112 / FlyType=0 / 风车 OnTick + 32003149 碰撞伤害',
    ontick_norm_order_id, old_before_order)

# ============ Phase 6: 加 counter%3==2 判断 + AND[320358, ...] ============
next_rid = add_node(next_rid, counter_mod3_id, 'TSET_NUM_CALCULATE', 31, [
    {"Value": old_get_counter, "ParamType": 2, "Factor": 0},
    {"Value": 7, "ParamType": 0, "Factor": 0},  # MOD
    {"Value": 3, "ParamType": 0, "Factor": 0},
], 'counter % 3')

next_rid = add_node(next_rid, counter_eq2_cond_id, 'TSCT_VALUE_COMPARE', 0, [
    {"Value": counter_mod3_id, "ParamType": 2, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},  # op ==
    {"Value": 2, "ParamType": 0, "Factor": 0},
], '判断 counter%3 == 2（第 3, 6, 9 颗）')

next_rid = add_node(next_rid, strong_and_cond_id, 'TSCT_AND', 0, [
    {"Value": 320358, "ParamType": 0, "Factor": 0},  # 三重碧叶 has buff
    {"Value": counter_eq2_cond_id, "ParamType": 0, "Factor": 0},
], '强化条件 = 三重碧叶 buff && 第3/6/9颗')

# CREATE 强化 / 普通
def make_create(ID, bc_id, desc):
    return [
        {"Value": bc_id, "ParamType": 0, "Factor": 0},
        {"Value": old_dyn_angle, "ParamType": 2, "Factor": 0},
        {"Value": 59, "ParamType": 1, "Factor": 0},
        {"Value": 60, "ParamType": 1, "Factor": 0},
        {"Value": 1, "ParamType": 5, "Factor": 0},
    ] + [{"Value": 0, "ParamType": 0, "Factor": 0}] * 10

next_rid = add_node(next_rid, create_premium_id, 'TSET_CREATE_BULLET', 8,
    make_create(create_premium_id, new_bc_premium_id, '强化叶'),
    f'生成 1 颗强化叶（BulletConfig {new_bc_premium_id}）')
next_rid = add_node(next_rid, create_normal_id, 'TSET_CREATE_BULLET', 8,
    make_create(create_normal_id, new_bc_normal_id, '普通叶'),
    f'生成 1 颗普通叶（BulletConfig {new_bc_normal_id}）')

# CONDITION_EXECUTE: strong_cond ? premium : normal
next_rid = add_node(next_rid, condition_exec_id, 'TSET_CONDITION_EXECUTE', 0, [
    {"Value": strong_and_cond_id, "ParamType": 0, "Factor": 0},
    {"Value": create_premium_id, "ParamType": 0, "Factor": 0},
    {"Value": create_normal_id, "ParamType": 0, "Factor": 0},
], '强化条件成立 → 强化叶 / 否则 → 普通叶')

# ============ Phase 7: 修改 body ORDER（reallocated 老 body_order）============
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == old_body_order:
        # 原 Params: [old_dyn_create, old_add_counter]
        # 新 Params: [condition_exec, old_add_counter]
        cj['Params'] = [
            {"Value": condition_exec_id, "ParamType": 0, "Factor": 0},
            {"Value": old_add_counter, "ParamType": 0, "Factor": 0},
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = '【REPEAT body】1.CONDITION→强化或普通 / 2.counter+=1'
        print(f'[FIX] body ORDER {old_body_order}: CREATE → CONDITION')
        break

# ============ Phase 8: 删除原单 CREATE_BULLET (old_dyn_create) ============
del_guids = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == old_dyn_create:
        del_guids.add(r['data']['GUID'])
old_n = len(data['references']['RefIds'])
data['references']['RefIds'] = [r for r in data['references']['RefIds'] if r['data']['GUID'] not in del_guids]
remaining_rids = set(r['rid'] for r in data['references']['RefIds'])
data['nodes'] = [n for n in data['nodes'] if n['rid'] in remaining_rids]
data['edges'] = [e for e in data['edges'] if e['inputNodeGUID'] not in del_guids and e['outputNodeGUID'] not in del_guids]
print(f'[DEL] 旧 单 CREATE_BULLET {old_dyn_create}')

# ============ Phase 9: sticky note + path ============
data['path'] = '<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212018【PoC】叶散风行.json'

if data.get('stickyNotes'):
    data['stickyNotes'][0]['title'] = '30212018 叶散风行 PoC / 木宗门 · 人阶 · 奇术'
    data['stickyNotes'][0]['content'] = f"""【作用】
30212010「叶散风行」的风车版 PoC。8 颗叶子风车扩散 + 每 3 发的第 3 颗强化（吃三重碧叶 buff 加成）。

【流程】
1. 释放 → 锁定主角位置
2. REPEAT 循环 N 次同帧生成：
   - 计算当前 counter（0..N-1）
   - 判断：counter%3==2 && 有三重碧叶 buff？
     - 是 → 生成强化叶（BulletConfig {new_bc_premium_id} / 跟原 320110 同伤害）
     - 否 → 生成普通叶（BulletConfig {new_bc_normal_id} / 跟原 320112 同伤害）
   - counter+=1
3. 每颗 BeforeBorn → 瞬移到 主角 + initial_radius × 飞行方向
4. 每帧 OnTick：
   - 朝向 += spin_step（视觉 + θ 同步旋转）
   - 半径 r += r_step
   - 位置 = 主角 + r × dir(θ)
   - 原 32003150/32003149 碰撞伤害链每帧检测
5. 120 帧（2 秒）后子弹消失

【特殊条件】
- 三重碧叶 buff (320358) 不在 → 全部普通叶
- N < 3 → 无强化叶
- counter 序号是单次释放内独立计算（不跨次累加）

【参数】 — SkillTag 面板调节

▌子弹数量
  bullet_count = 8 / 改 4 / 12 / 16 任意

▌出生位置
  initial_radius = 200（叶子出现距主角多远，码）

▌自旋
  spin_step = -6（每帧旋转角度 / -6=1秒1圈 / 0=不转）

▌径向扩散
  r_step = 7（每帧半径 +7 / 2 秒到 1000 码）
  position_scale = 10000（不要改）

▌叶尖朝向
  tip_tilt = 30（叶尖外掰角度 / 30 适度 / 0 切向 / 90 径向外）

▌运行时（不要改）
  iter_counter / r_acc

【速查：想要什么效果 → 改哪个】
  子弹更多 → 调大 bullet_count
  叶子离主角更远 → 调大 initial_radius
  转得更快 → spin_step 调更负
  扩散更快 → r_step 调大
  不要旋转 → spin_step = 0

【联动】
- 三重碧叶 buff (320358 / buff 320037) 在期间释放才会出现强化叶
- 强化/普通子弹的碰撞伤害链复用 30212010 的 32003150 / 32003149
"""
    print('[FIX] sticky note (30212018 PoC)')

DST.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] 30212018 created at {DST}')
print(f'  RefIds={len(data["references"]["RefIds"])} / edges={len(data["edges"])}')
print(f'\n========== 关键 ID ==========')
print(f'SkillConfig: 30212018')
print(f'BulletConfig 强化: {new_bc_premium_id}')
print(f'BulletConfig 普通: {new_bc_normal_id}')
print(f'REPEAT: {old_repeat}')
print(f'body ORDER: {old_body_order}')
print(f'CONDITION: {condition_exec_id}')
