"""patch_30212017_mvp12_decouple_radius_speed.py — 彻底分离初始半径 vs 扩散速度

问题:
  vR_initial 既影响初始位置（Frame 1 跳跃 = 初始半径）又影响后续速度
  → 无法独立调

修法:
  用 BulletConfig.BeforeBornSkillEffectExecuteInfo 钩子, 子弹 born 后立即 CHANGE_POSITION
  到 (caster.pos + initial_radius × 飞行方向) → 视觉上"出生在偏移位置"
  OnTick vR 重新独立调（无累加贡献到初始半径）

新加节点:
  1. SkillTag 320936 `initial_radius` default=200
  2. NUM_CALC X_spawn: ((cos × initial_radius) / 10000) + self.X (复用 cos 32900056, self.X 32900042)
  3. NUM_CALC Y_spawn: ((sin × initial_radius) / 10000) + self.Y (复用 sin 32900057, self.Y 32900048)
  4. CHANGE_ENTITY_POSITION (self, X_spawn, Y_spawn)
  5. BeforeBorn ORDER 入口

修改 BulletConfig 320258:
  BeforeBornSkillEffectExecuteInfo.SkillEffectConfigID = BeforeBorn ORDER

参数推荐（用户目标: 200 码初始 / 1 圈/秒 / 2秒 800码扩散）:
  initial_radius = 200
  spin_step = -6 (60°/帧 × 60FPS = 360°/秒 = 1 圈)
  vR_step = 0 (匀速)
  vR_initial = 20 (匀速 → 每帧 6.7 码 → 60 帧 1 秒 400 码 / 2 秒 800 码)
  position_scale = 30000 (默认)
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

COS_ID = 32900056
SIN_ID = 32900057
SELF_X_ID = 32900042
SELF_Y_ID = 32900048
BULLET_CONFIG_ID = 320258

# === Phase 1: 调用户期望的推荐 default 值 ===
RECOMMENDED_DEFAULTS = {
    # SkillTag : (new_default, new_desc)
    320932: (-6,    '每帧旋转角度（°/帧 / 负=顺时针 / -6 → 60FPS 下 360°/秒 = 1 圈/秒）'),
    320933: (0,     '每帧速度累加（0=匀速 / 负=减速 / 越大加速越快）'),
    320934: (20,    '初始扩散速度（OnTick 起步 vR / 不再控制初始半径！）'),
    320935: (30000, '位移分母（越大飞越慢 / 默认 30000）'),
}

alloc = IDAllocator()
initial_radius_tag_id = alloc.get_next('SkillTagsConfig')
x_spawn_id            = alloc.get_next('SkillEffectConfig')
y_spawn_id            = alloc.get_next('SkillEffectConfig')
change_pos_id         = alloc.get_next('SkillEffectConfig')
before_born_id        = alloc.get_next('SkillEffectConfig')
print(f'New SkillTag: initial_radius = {initial_radius_tag_id}')
print(f'New nodes: X_spawn={x_spawn_id} / Y_spawn={y_spawn_id} / CHANGE_POS={change_pos_id} / BeforeBorn={before_born_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# === Phase 2: 加新 SkillTag initial_radius ===
initial_radius_node = {
    "rid": next_rid,
    "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 15,
        "position": {"serializedVersion": "2", "x": 500.0, "y": 2500.0, "width": 237.0, "height": 135.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": initial_radius_tag_id,
        "Desc": '出生半径偏移（码 / 子弹 born 后立即瞬移到 caster + 此距离 × 飞行方向）',
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
        "ConfigJson": json.dumps({
            "ID": initial_radius_tag_id, "TagType": 0,
            "Desc": "出生半径偏移（码）",
            "NameKey": 0, "DefaultValue": 200,
            "FinalValueEffectID": 0, "RetainWhenDie": False,
        }, ensure_ascii=False),
        "Config2ID": f"SkillTagsConfig_{initial_radius_tag_id}",
    }
}

# === Phase 3: 加 4 个 SkillEffect 节点 ===
def make_num_calc(rid, ID, desc, params, pos):
    return {
        "rid": rid,
        "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 50,
            "position": {"serializedVersion": "2", "x": float(pos[0]), "y": float(pos[1]), "width": 280.0, "height": 200.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps({
                "ID": ID, "SkillEffectType": 31, "Params": params,
            }, ensure_ascii=False),
            "Config2ID": f"SkillEffectConfig_{ID}",
            "SkillEffectType": 31,
        }
    }

# X_spawn: ((cos × initial_radius) / 10000) + self.X (7 项左结合)
x_spawn_params = [
    {"Value": COS_ID, "ParamType": 2, "Factor": 0},
    {"Value": 5, "ParamType": 0, "Factor": 0},        # MUL
    {"Value": initial_radius_tag_id, "ParamType": 3, "Factor": 0},
    {"Value": 6, "ParamType": 0, "Factor": 0},        # DIV
    {"Value": 10000, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},        # ADD
    {"Value": SELF_X_ID, "ParamType": 2, "Factor": 0},
]
x_spawn_node = make_num_calc(next_rid+1, x_spawn_id,
    'X 出生点 = ((cos × initial_radius) / 10000) + caster.X', x_spawn_params, (3800, -1100))

y_spawn_params = [
    {"Value": SIN_ID, "ParamType": 2, "Factor": 0},
    {"Value": 5, "ParamType": 0, "Factor": 0},
    {"Value": initial_radius_tag_id, "ParamType": 3, "Factor": 0},
    {"Value": 6, "ParamType": 0, "Factor": 0},
    {"Value": 10000, "ParamType": 0, "Factor": 0},
    {"Value": 3, "ParamType": 0, "Factor": 0},
    {"Value": SELF_Y_ID, "ParamType": 2, "Factor": 0},
]
y_spawn_node = make_num_calc(next_rid+2, y_spawn_id,
    'Y 出生点 = ((sin × initial_radius) / 10000) + caster.Y', y_spawn_params, (3800, -850))

# CHANGE_ENTITY_POSITION (self, X_spawn, Y_spawn)
change_pos_node = {
    "rid": next_rid+3,
    "type": {"class": "TSET_CHANGE_ENTITY_POSITION", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 60,
        "position": {"serializedVersion": "2", "x": 4200.0, "y": -950.0, "width": 280.0, "height": 200.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": change_pos_id,
        "Desc": '【BeforeBorn】把子弹瞬移到 出生半径偏移 位置（caster + R × 飞行方向）',
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": change_pos_id, "SkillEffectType": 22,
            "Params": [
                {"Value": 1, "ParamType": 5, "Factor": 0},          # self
                {"Value": x_spawn_id, "ParamType": 2, "Factor": 0}, # X
                {"Value": y_spawn_id, "ParamType": 2, "Factor": 0}, # Y
                {"Value": 0, "ParamType": 0, "Factor": 0},          # Z (0)
                {"Value": 0, "ParamType": 0, "Factor": 0},
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{change_pos_id}",
        "SkillEffectType": 22,
    }
}

# BeforeBorn ORDER (入口)
before_born_node = {
    "rid": next_rid+4,
    "type": {"class": "TSET_ORDER_EXECUTE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 5,
        "position": {"serializedVersion": "2", "x": 4500.0, "y": -700.0, "width": 280.0, "height": 200.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": before_born_id,
        "Desc": '【BulletConfig BeforeBorn 入口】1.瞬移到出生半径偏移位置',
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": before_born_id, "SkillEffectType": 1,
            "Params": [
                {"Value": change_pos_id, "ParamType": 0, "Factor": 0},
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{before_born_id}",
        "SkillEffectType": 1,
    }
}

data['references']['RefIds'].extend([initial_radius_node, x_spawn_node, y_spawn_node, change_pos_node, before_born_node])
data['nodes'].extend([{"rid": initial_radius_node['rid']}, {"rid": x_spawn_node['rid']},
                      {"rid": y_spawn_node['rid']}, {"rid": change_pos_node['rid']}, {"rid": before_born_node['rid']}])
print('[ADD] 5 nodes (initial_radius SkillTag + 4 SkillEffect)')

# === Phase 4: 更新 BulletConfig 320258 BeforeBornSkillEffectExecuteInfo ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == BULLET_CONFIG_ID and r['type']['class'] == 'BulletConfigNode':
        cj['BeforeBornSkillEffectExecuteInfo'] = {'SelectConfigID': 0, 'SkillEffectConfigID': before_born_id}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] BulletConfig 320258 BeforeBornSkillEffectExecuteInfo = {before_born_id}')
        break

# === Phase 5: 更新 4 个老 SkillTag default + Desc 到推荐值 ===
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    nid = cj.get('ID')
    if nid in RECOMMENDED_DEFAULTS and r['type']['class'] == 'SkillTagsConfigNode':
        new_default, new_desc = RECOMMENDED_DEFAULTS[nid]
        old_default = cj.get('DefaultValue')
        cj['DefaultValue'] = new_default
        cj['Desc'] = new_desc
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = new_desc
        print(f'[FIX] SkillTag {nid}: default {old_default} → {new_default}')

# === Phase 6: Edges ===
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

# X_spawn edges
data['edges'].append(make_edge(COS_ID, x_spawn_id, "0"))
data['edges'].append(make_edge(SELF_X_ID, x_spawn_id, "6"))
# Y_spawn edges
data['edges'].append(make_edge(SIN_ID, y_spawn_id, "0"))
data['edges'].append(make_edge(SELF_Y_ID, y_spawn_id, "6"))
# CHANGE_POS edges
data['edges'].append(make_edge(x_spawn_id, change_pos_id, "1"))
data['edges'].append(make_edge(y_spawn_id, change_pos_id, "2"))
# BeforeBorn → CHANGE_POS
data['edges'].append(make_edge(change_pos_id, before_born_id, "0"))
print(f'[ADD] 7 edges / total = {len(data["edges"])}')

# === Phase 7: 更新 sticky note 反映新机制 + 参数推荐 ===
new_sticky = """【作用】
PoC 木宗门技能。8 颗叶子从主角周围一定距离爆发出现，绕主角自旋 + 缓慢外扩。

【流程】
1. 释放 → 锁定主角位置 + 朝向作为基准
2. OnSkillStart → 重置自旋累加器 + 重置初速度 + 生成 8 颗子弹
   - 8 颗子弹在主角周围 8 个方向（每隔 45°）位置 spawn
   - 每颗朝向 = 主角朝向 + 自身偏移
3. 每颗子弹 BeforeBorn → 立即瞬移到 主角 + 出生半径偏移 × 飞行方向 位置
4. 每帧 OnTick：
   - 子弹朝向 += 旋转步长（视觉同步旋转）
   - 速度 += 速度累加（默认 0 = 匀速）
   - 沿当前朝向移动 = (cos × 速度) / 位移分母
5. 60 帧后（1 秒）→ 子弹生命到期消失

【特殊条件】
- 每颗子弹的自旋累加 + 速度累加 都独立（per-bullet SkillTag 槽位）
- 出生半径 vs 后续速度 已彻底解耦（BeforeBorn CHANGE_POSITION 单独负责出生位置）

【参数】
出生半径：SkillTag 320936「initial_radius」/ 默认 200（码 / 决定爆发出现的远近）
旋转速度：SkillTag 320932「spin_step」/ 默认 -6（°/帧 / 60FPS 下 1 圈/秒）
扩散速度：SkillTag 320934「vR_initial」/ 默认 20（每帧 cos×20/30000 ≈ 6.67 码/帧 / 60 帧 400 码 / 2 秒 800 码）
速度累加：SkillTag 320933「vR_step」/ 默认 0（匀速 / 调正数 = 越扩越快 / 调负数 = 越扩越慢）
位移分母：SkillTag 320935「position_scale」/ 默认 30000（调大整体飞慢）
子弹数：8（结构性）
朝向分布：每隔 45°（结构性）

【联动】
—（PoC / 后续移植到 30212010 真实技能）"""

if 'stickyNotes' in data and data['stickyNotes']:
    data['stickyNotes'][0]['content'] = new_sticky
    print('[FIX] sticky note 更新（含完美参数推荐）')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(data["references"]["RefIds"])} / edges={len(data["edges"])}')
