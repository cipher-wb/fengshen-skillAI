"""patch_30212010_install_windmill.py — 30212010 叶散风行 移植 30212017 风车机制

目标:
  替换 32002227 REPEAT 和它后面的子弹生成逻辑，改成风车模型
  保留原碰撞 + 伤害 + 击退链 (32003150 强化 / 32003149 普通)
  保留原"三重碧叶 buff" check (320358)
  新加 "counter % 3 == 2 (第 3,6,9... 颗强化)" 判断

新建:
  - BulletConfig × 2: 复制 320110/320112 改 FlyType=0, Speed=0, 接风车 OnTick/BeforeBorn
  - SkillTag × 8: bullet_count / spin_step / r_step / initial_radius / position_scale / tip_tilt / iter_counter / r_acc
  - SkillEffect ~30: 风车 OnTick 节点 + BeforeBorn 节点 + counter%3 判断 + 2 个 CREATE_BULLET + CONDITION + REPEAT body

修改:
  - 32002225 ORDER P[3]: 32002227 → 新 REPEAT
  - 32002225 ORDER 加 reset_counter, reset_r 前置

不改 (保留):
  - 320110 / 320112 原 BulletConfig
  - 32003149 / 32003150 原碰撞伤害击退链
  - 320358 三重碧叶 buff check
  - 32002225 ORDER 其他 P[0-2,4,5] 节点
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212010【木宗门】奇术_人阶_叶散风行.json')
data = json.loads(P.read_text(encoding='utf-8'))

# ============ 收集已用 ID（避免重分配冲突） ============
existing_st_ids = set()
existing_se_ids = set()
existing_bc_ids = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    nid = cj.get('ID')
    if r['type']['class'] == 'SkillTagsConfigNode': existing_st_ids.add(nid)
    elif r['type']['class'] == 'BulletConfigNode':  existing_bc_ids.add(nid)
    elif nid: existing_se_ids.add(nid)

alloc = IDAllocator()
def alloc_st():
    while True:
        x = alloc.get_next('SkillTagsConfig')
        if x not in existing_st_ids: existing_st_ids.add(x); return x
def alloc_se():
    while True:
        x = alloc.get_next('SkillEffectConfig')
        if x not in existing_se_ids: existing_se_ids.add(x); return x
def alloc_bc():
    while True:
        x = alloc.get_next('BulletConfig')
        if x not in existing_bc_ids: existing_bc_ids.add(x); return x

# ============ Phase 1: 复制 BulletConfig 320110/320112 ============
src_premium = None  # 320110
src_normal  = None  # 320112
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if r['type']['class'] == 'BulletConfigNode':
        if cj.get('ID') == 320110: src_premium = cj
        elif cj.get('ID') == 320112: src_normal = cj
assert src_premium and src_normal, '320110/320112 not found'

new_premium_bc_id = alloc_bc()
new_normal_bc_id  = alloc_bc()
print(f'New BulletConfig: 风车强化={new_premium_bc_id} / 风车普通={new_normal_bc_id}')

# Phase 2 ID 预分配
sk_bullet_count    = alloc_st()
sk_spin_step       = alloc_st()
sk_r_step          = alloc_st()
sk_initial_radius  = alloc_st()
sk_position_scale  = alloc_st()
sk_tip_tilt        = alloc_st()
sk_iter_counter    = alloc_st()
sk_r_acc           = alloc_st()

# Phase 3 SkillEffect 预分配
get_caster_facing  = alloc_se()
get_self_facing    = alloc_se()
get_self_X         = alloc_se()
get_self_Y         = alloc_se()
get_caster_X       = alloc_se()
get_caster_Y       = alloc_se()
get_r_acc          = alloc_se()
get_counter        = alloc_se()
add_counter        = alloc_se()
reset_counter      = alloc_se()
reset_r_acc        = alloc_se()
add_r_acc          = alloc_se()
neg_tilt_numcalc   = alloc_se()
effective_facing   = alloc_se()
cos_facing         = alloc_se()
sin_facing         = alloc_se()
new_facing_calc    = alloc_se()
modify_facing      = alloc_se()
newX_calc          = alloc_se()
newY_calc          = alloc_se()
change_pos_ontick  = alloc_se()
ontick_premium_order = alloc_se()
ontick_normal_order  = alloc_se()
X_spawn_calc       = alloc_se()
Y_spawn_calc       = alloc_se()
change_pos_before  = alloc_se()
beforeborn_order   = alloc_se()
angle_step_calc    = alloc_se()
dynamic_visual_calc= alloc_se()
counter_mod3_calc  = alloc_se()
counter_eq2_cond   = alloc_se()
strong_cond_and    = alloc_se()
create_premium     = alloc_se()
create_normal      = alloc_se()
condition_premium  = alloc_se()
body_order         = alloc_se()
new_repeat         = alloc_se()
init_radius_bridge = alloc_se()  # 用于 reset_r 把 SkillTag 桥接到 NodeRef
print('All IDs allocated')

# ============ Helpers ============
def add_node(rid, ID, cls, set_type, params, desc, extra_fields=None, table_tash='0CFA05568A66FEA1DF3BA6FE40DB7080'):
    node = {
        "rid": rid,
        "type": {"class": cls, "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 50,
            "position": {"serializedVersion": "2", "x": 5000.0, "y": float(rid * 30), "width": 280.0, "height": 160.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": table_tash,
            "ConfigJson": json.dumps({
                "ID": ID, "SkillEffectType": set_type, "Params": params,
                **(extra_fields or {}),
            }, ensure_ascii=False),
            "Config2ID": f"SkillEffectConfig_{ID}",
            "SkillEffectType": set_type,
        }
    }
    data['references']['RefIds'].append(node)
    data['nodes'].append({"rid": rid})
    return node

def add_skilltag(rid, ID, default, desc):
    cj = {"ID": ID, "TagType": 0, "Desc": desc, "NameKey": 0,
          "DefaultValue": default, "FinalValueEffectID": 0, "RetainWhenDie": False}
    node = {
        "rid": rid,
        "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 17,
            "position": {"serializedVersion": "2", "x": 5500.0, "y": float(rid * 30), "width": 237.0, "height": 135.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
            "ConfigJson": json.dumps(cj, ensure_ascii=False),
            "Config2ID": f"SkillTagsConfig_{ID}",
        }
    }
    data['references']['RefIds'].append(node)
    data['nodes'].append({"rid": rid})
    return node

def add_bullet_config(rid, ID, src_dict, fly_type, speed, desc, after_born_id, before_born_id):
    cj = dict(src_dict)
    cj['ID'] = ID
    cj['FlyType'] = fly_type
    cj['Speed'] = speed
    cj['MaxSpeed'] = 0
    cj['AcceSpeed'] = 0
    cj['MaxDistance'] = 0
    cj['LastTime'] = 120  # 2 秒生命
    cj['LifeFlag'] = 1
    cj['AfterBornSkillEffectExecuteInfo'] = {'SelectConfigID': 0, 'SkillEffectConfigID': after_born_id}
    cj['BeforeBornSkillEffectExecuteInfo'] = {'SelectConfigID': 0, 'SkillEffectConfigID': before_born_id}
    node = {
        "rid": rid,
        "type": {"class": "BulletConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 20,
            "position": {"serializedVersion": "2", "x": 6000.0, "y": float(rid * 30), "width": 280.0, "height": 400.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "DEFAULT_BULLET_HASH",
            "ConfigJson": json.dumps(cj, ensure_ascii=False),
            "Config2ID": f"BulletConfig_{ID}",
        }
    }
    data['references']['RefIds'].append(node)
    data['nodes'].append({"rid": rid})
    return node

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1
rid = next_rid

# ============ Phase 2: 8 SkillTags ============
add_skilltag(rid, sk_bullet_count, 8, '子弹数量 N（改 4/8/12/16）/ 等距均匀分布'); rid += 1
add_skilltag(rid, sk_spin_step, -6, '自旋速度（°/帧 / -6=1秒1圈 / 0=不转）'); rid += 1
add_skilltag(rid, sk_r_step, 7, '半径扩大速度（每帧 +N / 7=2秒扩 800 码）'); rid += 1
add_skilltag(rid, sk_initial_radius, 200, '出生半径（叶子离主角多远爆发出现 / 200=2m）'); rid += 1
add_skilltag(rid, sk_position_scale, 10000, '位移分母（固定值 / 不要改）'); rid += 1
add_skilltag(rid, sk_tip_tilt, 30, '叶尖外掰角度（° / 30=适度 / 90=纯径向外 / 0=纯切向）'); rid += 1
add_skilltag(rid, sk_iter_counter, 0, '【运行时累加 不要改】子弹生成序号'); rid += 1
add_skilltag(rid, sk_r_acc, 0, '【运行时累加 不要改】子弹半径累加值'); rid += 1
print('Phase 2 OK: 8 SkillTags')

# ============ Phase 3a: BulletConfig × 2（先占 ID，AfterBorn/BeforeBorn 后填）============
prem_bc_node = add_bullet_config(rid, new_premium_bc_id, src_premium, 0, 0,
    '【风车版强化子弹】（复制 320110 / FlyType=0 Speed=0 / 接风车 OnTick+原碰撞伤害链）',
    ontick_premium_order, beforeborn_order); rid += 1
norm_bc_node = add_bullet_config(rid, new_normal_bc_id, src_normal, 0, 0,
    '【风车版普通子弹】（复制 320112 / FlyType=0 Speed=0 / 接风车 OnTick+原碰撞伤害链）',
    ontick_normal_order, beforeborn_order); rid += 1
print('Phase 3a OK: 2 BulletConfig')

# ============ Phase 3b: 风车 OnTick + BeforeBorn 节点 ============
# GET self.facing (attr=91)
add_node(rid, get_self_facing, 'TSET_GET_ENTITY_ATTR_VALUE', 32, [
    {"Value": 1, "ParamType": 5, "Factor": 0},
    {"Value": 91, "ParamType": 0, "Factor": 0},
], '读「子弹当前朝向」'); rid += 1

# GET self.X
add_node(rid, get_self_X, 'TSET_GET_ENTITY_ATTR_VALUE', 32, [
    {"Value": 1, "ParamType": 5, "Factor": 0},
    {"Value": 59, "ParamType": 0, "Factor": 0},
], '读「子弹当前 X」'); rid += 1

# GET self.Y
add_node(rid, get_self_Y, 'TSET_GET_ENTITY_ATTR_VALUE', 32, [
    {"Value": 1, "ParamType": 5, "Factor": 0},
    {"Value": 60, "ParamType": 0, "Factor": 0},
], '读「子弹当前 Y」'); rid += 1

# GET caster.X (caster scope V=4)
add_node(rid, get_caster_X, 'TSET_GET_ENTITY_ATTR_VALUE', 32, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 59, "ParamType": 0, "Factor": 0},
], '读「主角 X」/ 风车中心'); rid += 1

# GET caster.Y
add_node(rid, get_caster_Y, 'TSET_GET_ENTITY_ATTR_VALUE', 32, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 60, "ParamType": 0, "Factor": 0},
], '读「主角 Y」'); rid += 1

# GET caster.facing
add_node(rid, get_caster_facing, 'TSET_GET_ENTITY_ATTR_VALUE', 32, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 91, "ParamType": 0, "Factor": 0},
], '读「主角朝向」'); rid += 1

# GET r_acc
add_node(rid, get_r_acc, 'TSET_GET_SKILL_TAG_VALUE', 48, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": sk_r_acc, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '读「半径累加 r」'); rid += 1

# GET counter
add_node(rid, get_counter, 'TSET_GET_SKILL_TAG_VALUE', 48, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": sk_iter_counter, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '读「子弹生成序号 counter」'); rid += 1

# neg_tilt = tip_tilt × -1
add_node(rid, neg_tilt_numcalc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": sk_tip_tilt, "ParamType": 3, "Factor": 0},
    {"Value": 5, "ParamType": 0, "Factor": 0},
    {"Value": -1, "ParamType": 0, "Factor": 0},
], 'neg_tilt = -tip_tilt'); rid += 1

# effective_facing = self.facing + 90 + neg_tilt (5项 / +90 抵消视觉补偿)
add_node(rid, effective_facing, 'TSET_NUM_CALCULATE', 31, [
    {"Value": get_self_facing, "ParamType": 2, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": 90, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": neg_tilt_numcalc, "ParamType": 2, "Factor": 0},
], 'effective_facing = self.facing + 90 - tip_tilt'); rid += 1

# cos / sin of effective_facing
add_node(rid, cos_facing, 'TSET_MATH_COS', 51, [
    {"Value": effective_facing, "ParamType": 2, "Factor": 0},
], 'cos(effective_facing)'); rid += 1
add_node(rid, sin_facing, 'TSET_MATH_SIN', 50, [
    {"Value": effective_facing, "ParamType": 2, "Factor": 0},
], 'sin(effective_facing)'); rid += 1

# new_facing = self.facing + spin_step
add_node(rid, new_facing_calc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": get_self_facing, "ParamType": 2, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": sk_spin_step, "ParamType": 3, "Factor": 0},
], '下一帧朝向 = 当前朝向 + spin_step'); rid += 1

# MODIFY self.facing = new_facing (每帧旋转 / 驱动视觉 + θ)
add_node(rid, modify_facing, 'TSET_MODIFY_ENTITY_ATTR_VALUE', 12, [
    {"Value": 1, "ParamType": 5, "Factor": 0},
    {"Value": 91, "ParamType": 0, "Factor": 0},
    {"Value": new_facing_calc, "ParamType": 2, "Factor": 0},
], '【每帧步骤1·旋转】self.facing = 当前朝向 + spin_step'); rid += 1

# ADD r_acc += r_step
add_node(rid, add_r_acc, 'TSET_ADD_SKILL_TAG_VALUE', 97, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": sk_r_acc, "ParamType": 0, "Factor": 0},
    {"Value": sk_r_step, "ParamType": 3, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '【每帧步骤2·半径扩大】r += r_step'); rid += 1

# newX = (cos × r_acc) / 10000 + caster.X
add_node(rid, newX_calc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": cos_facing, "ParamType": 2, "Factor": 0},
    {"Value": 5, "ParamType": 0, "Factor": 0},
    {"Value": get_r_acc, "ParamType": 2, "Factor": 0},
    {"Value": 6, "ParamType": 0, "Factor": 0},
    {"Value": 10000, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": get_caster_X, "ParamType": 2, "Factor": 0},
], '新 X = cos × r / 10000 + 主角.X'); rid += 1
add_node(rid, newY_calc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": sin_facing, "ParamType": 2, "Factor": 0},
    {"Value": 5, "ParamType": 0, "Factor": 0},
    {"Value": get_r_acc, "ParamType": 2, "Factor": 0},
    {"Value": 6, "ParamType": 0, "Factor": 0},
    {"Value": 10000, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": get_caster_Y, "ParamType": 2, "Factor": 0},
], '新 Y = sin × r / 10000 + 主角.Y'); rid += 1

# CHANGE_POSITION OnTick
add_node(rid, change_pos_ontick, 'TSET_CHANGE_ENTITY_POSITION', 22, [
    {"Value": 1, "ParamType": 5, "Factor": 0},
    {"Value": newX_calc, "ParamType": 2, "Factor": 0},
    {"Value": newY_calc, "ParamType": 2, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
], '【每帧步骤3·移动】CHANGE_POSITION 到 (新X, 新Y)'); rid += 1

# OnTick ORDER 强化版 = [MODIFY_facing, ADD_r, CHANGE_POS, 32003150 原碰撞链]
add_node(rid, ontick_premium_order, 'TSET_ORDER_EXECUTE', 1, [
    {"Value": modify_facing, "ParamType": 0, "Factor": 0},
    {"Value": add_r_acc, "ParamType": 0, "Factor": 0},
    {"Value": change_pos_ontick, "ParamType": 0, "Factor": 0},
    {"Value": 32003150, "ParamType": 0, "Factor": 0},  # 原强化子弹 OnTick (碰撞+伤害+击退)
], '【强化子弹 AfterBorn 入口】风车 OnTick + 原碰撞伤害链'); rid += 1

# OnTick ORDER 普通版 = [MODIFY_facing, ADD_r, CHANGE_POS, 32003149 原碰撞链]
add_node(rid, ontick_normal_order, 'TSET_ORDER_EXECUTE', 1, [
    {"Value": modify_facing, "ParamType": 0, "Factor": 0},
    {"Value": add_r_acc, "ParamType": 0, "Factor": 0},
    {"Value": change_pos_ontick, "ParamType": 0, "Factor": 0},
    {"Value": 32003149, "ParamType": 0, "Factor": 0},  # 原普通子弹 OnTick
], '【普通子弹 AfterBorn 入口】风车 OnTick + 原碰撞伤害链'); rid += 1

# BeforeBorn: X_spawn / Y_spawn / CHANGE_POS / ORDER 入口
add_node(rid, X_spawn_calc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": cos_facing, "ParamType": 2, "Factor": 0},
    {"Value": 5, "ParamType": 0, "Factor": 0},
    {"Value": sk_initial_radius, "ParamType": 3, "Factor": 0},
    {"Value": 6, "ParamType": 0, "Factor": 0},
    {"Value": 10000, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": get_self_X, "ParamType": 2, "Factor": 0},
], 'X 出生 = cos × initial_radius / 10000 + caster.X (BeforeBorn 用 self.X=caster.X)'); rid += 1
add_node(rid, Y_spawn_calc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": sin_facing, "ParamType": 2, "Factor": 0},
    {"Value": 5, "ParamType": 0, "Factor": 0},
    {"Value": sk_initial_radius, "ParamType": 3, "Factor": 0},
    {"Value": 6, "ParamType": 0, "Factor": 0},
    {"Value": 10000, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": get_self_Y, "ParamType": 2, "Factor": 0},
], 'Y 出生'); rid += 1
add_node(rid, change_pos_before, 'TSET_CHANGE_ENTITY_POSITION', 22, [
    {"Value": 1, "ParamType": 5, "Factor": 0},
    {"Value": X_spawn_calc, "ParamType": 2, "Factor": 0},
    {"Value": Y_spawn_calc, "ParamType": 2, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
], '【BeforeBorn】瞬移到 主角 + initial_radius × dir'); rid += 1
add_node(rid, beforeborn_order, 'TSET_ORDER_EXECUTE', 1, [
    {"Value": change_pos_before, "ParamType": 0, "Factor": 0},
], '【子弹 BeforeBorn 入口】瞬移到出生半径偏移位置'); rid += 1
print('Phase 3b OK: 风车 OnTick + BeforeBorn 节点')

# ============ Phase 4: 新 REPEAT 替换 32002227 ============
# init_radius_bridge: 用来 reset r_acc = initial_radius
add_node(rid, init_radius_bridge, 'TSET_NUM_CALCULATE', 31, [
    {"Value": sk_initial_radius, "ParamType": 3, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
], '桥接 initial_radius → reset_r 用'); rid += 1
# reset_r_acc
add_node(rid, reset_r_acc, 'TSET_MODIFY_SKILL_TAG_VALUE', 46, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": sk_r_acc, "ParamType": 0, "Factor": 0},
    {"Value": init_radius_bridge, "ParamType": 2, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '【OnSkillStart】重置 r_acc = initial_radius'); rid += 1
# reset_counter = 0
add_node(rid, reset_counter, 'TSET_MODIFY_SKILL_TAG_VALUE', 46, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": sk_iter_counter, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '【OnSkillStart】重置 counter = 0'); rid += 1
# ADD counter += 1
add_node(rid, add_counter, 'TSET_ADD_SKILL_TAG_VALUE', 97, [
    {"Value": 4, "ParamType": 5, "Factor": 0},
    {"Value": 41, "ParamType": 5, "Factor": 0},
    {"Value": sk_iter_counter, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '每生成 1 颗 counter += 1'); rid += 1
# angle_step = counter × 360 / N
add_node(rid, angle_step_calc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": get_counter, "ParamType": 2, "Factor": 0},
    {"Value": 5, "ParamType": 0, "Factor": 0},
    {"Value": 360, "ParamType": 0, "Factor": 0},
    {"Value": 6, "ParamType": 0, "Factor": 0},
    {"Value": sk_bullet_count, "ParamType": 3, "Factor": 0},
], 'angle_step = counter × 360 / N'); rid += 1
# dynamic_visual_angle = caster.facing + angle_step - 90 + tip_tilt
add_node(rid, dynamic_visual_calc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": get_caster_facing, "ParamType": 2, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": angle_step_calc, "ParamType": 2, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": -90, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": sk_tip_tilt, "ParamType": 3, "Factor": 0},
], '动态视觉角 = 主角朝向 + counter×(360/N) - 90 + tip_tilt'); rid += 1
# counter_mod_3 = counter % 3 (op=7 MOD)
add_node(rid, counter_mod3_calc, 'TSET_NUM_CALCULATE', 31, [
    {"Value": get_counter, "ParamType": 2, "Factor": 0},
    {"Value": 7, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
], 'counter % 3'); rid += 1
# VALUE_COMPARE: counter_mod_3 == 2 → 第3,6,9... 颗
# 仿 320287 (VALUE_COMPARE) schema：常见 P=[A, op, B]
add_node(rid, counter_eq2_cond, 'TSCT_VALUE_COMPARE', 0, [
    {"Value": counter_mod3_calc, "ParamType": 2, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},  # op 0 = ==
    {"Value": 2, "ParamType": 0, "Factor": 0},
], '判断 counter%3 == 2 (第 3,6,9... 颗)'); rid += 1
# AND: 320358 has_buff 三重碧叶 + counter_eq2_cond
add_node(rid, strong_cond_and, 'TSCT_AND', 0, [
    {"Value": 320358, "ParamType": 0, "Factor": 0},  # 三重碧叶 has buff
    {"Value": counter_eq2_cond, "ParamType": 0, "Factor": 0},
], '强化条件 = 有三重碧叶 buff && counter%3==2'); rid += 1
# CREATE 强化 (新风车强化 BulletConfig)
add_node(rid, create_premium, 'TSET_CREATE_BULLET', 8, [
    {"Value": new_premium_bc_id, "ParamType": 0, "Factor": 0},
    {"Value": dynamic_visual_calc, "ParamType": 2, "Factor": 0},
    {"Value": 59, "ParamType": 1, "Factor": 0},
    {"Value": 60, "ParamType": 1, "Factor": 0},
    {"Value": 1, "ParamType": 5, "Factor": 0},
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
], '生成 1 颗强化叶子（BulletConfig=风车强化）'); rid += 1
# CREATE 普通
add_node(rid, create_normal, 'TSET_CREATE_BULLET', 8, [
    {"Value": new_normal_bc_id, "ParamType": 0, "Factor": 0},
    {"Value": dynamic_visual_calc, "ParamType": 2, "Factor": 0},
    {"Value": 59, "ParamType": 1, "Factor": 0},
    {"Value": 60, "ParamType": 1, "Factor": 0},
    {"Value": 1, "ParamType": 5, "Factor": 0},
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
], '生成 1 颗普通叶子（BulletConfig=风车普通）'); rid += 1
# CONDITION_EXECUTE: 强化 ? 强化 : 普通 (仿 32002232 schema)
add_node(rid, condition_premium, 'TSET_CONDITION_EXECUTE', 0, [
    {"Value": strong_cond_and, "ParamType": 0, "Factor": 0},
    {"Value": create_premium, "ParamType": 0, "Factor": 0},
    {"Value": create_normal, "ParamType": 0, "Factor": 0},
], '强化条件成立 → 强化子弹 / 否则 普通子弹'); rid += 1
# body = [CONDITION_EXECUTE, ADD counter]
add_node(rid, body_order, 'TSET_ORDER_EXECUTE', 1, [
    {"Value": condition_premium, "ParamType": 0, "Factor": 0},
    {"Value": add_counter, "ParamType": 0, "Factor": 0},
], '【REPEAT body】1.生成 1 颗(强化或普通) / 2.counter+=1'); rid += 1
# 新 REPEAT
add_node(rid, new_repeat, 'TSET_REPEAT_EXECUTE', 3, [
    {"Value": 1, "ParamType": 0, "Factor": 0},
    {"Value": sk_bullet_count, "ParamType": 3, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
    {"Value": body_order, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 0, "ParamType": 0, "Factor": 0},
    {"Value": 1, "ParamType": 0, "Factor": 0},
], '【REPEAT】循环 N 次 / 每次生成 1 颗（强化或普通）'); rid += 1
print('Phase 4 OK: REPEAT body + 判断 + 2 个 CREATE')

# ============ Phase 5: 修改 32002225 ORDER P[3] + 加 reset 前置 ============
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == 32002225:
        # 原 Params: [32002975, 13002635, 32002226, 32002227, 32002412, 32002411]
        # 改 P[3] = new_repeat
        # 在最前插入 reset_counter + reset_r
        new_params = [
            {"Value": reset_counter, "ParamType": 0, "Factor": 0},
            {"Value": reset_r_acc, "ParamType": 0, "Factor": 0},
        ] + [p if p['Value'] != 32002227 else {"Value": new_repeat, "ParamType": 0, "Factor": 0}
             for p in cj['Params']]
        cj['Params'] = new_params
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] 32002225 ORDER: P[3] 32002227 → 新 REPEAT {new_repeat} / 加 2 reset 前置')
        break

print('Phase 5 OK')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(data["references"]["RefIds"])} / edges={len(data["edges"])}')
print(f'\n========================')
print(f'新参数 (在 SkillEditor SkillTag 面板调):')
print(f'  {sk_bullet_count} bullet_count = 8')
print(f'  {sk_spin_step} spin_step = -6 (1秒1圈)')
print(f'  {sk_r_step} r_step = 7 (2秒扩800码)')
print(f'  {sk_initial_radius} initial_radius = 200')
print(f'  {sk_position_scale} position_scale = 10000')
print(f'  {sk_tip_tilt} tip_tilt = 30')
print(f'  {sk_iter_counter} iter_counter (运行时)')
print(f'  {sk_r_acc} r_acc (运行时)')
print(f'新 BulletConfig: 强化={new_premium_bc_id} / 普通={new_normal_bc_id}')
print(f'新 REPEAT: {new_repeat}')
