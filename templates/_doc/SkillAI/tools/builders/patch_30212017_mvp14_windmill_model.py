"""patch_30212017_mvp14_windmill_model.py — 风车模型重写 + 废弃清理

用户选 Option C：8 叶整体作为风车旋转 + 半径线性扩大。

物理模型转换:
  旧（增量式）: pos += dir(self.facing - 90) × vR / scale  → vR 加速 + 朝向旋转 = 旋转外扩
  新（绝对式 / 风车）: pos = caster.pos + r × dir(θ)
    θ = self.facing - 90 (复用 effective_facing / 每帧由 MODIFY_facing += spin_step 推动)
    r = SkillTag r_acc (复用 320937 vR_acc 槽位 / 每帧 r_acc += r_step)
    出生 r = initial_radius (320938 default 200)
  特点: r 单调增长 → 半径只扩不缩 / θ 累加 → 整体绕 caster 转 → 风车

废弃清理:
  删 SkillEffect: 32900035 ADD_angle / 32900036 GET_angle / 32900037 COS_angle / 32900051 reset_angle
  删 SkillTag:    320931 (旧 birth offset) / 320936 (旧 angle_acc) / 320934 (vR_initial) / 320935 (position_scale)
  ROOT_ORDER 32900053 移除 reset_angle 引用

新增:
  GET caster.X (新 SkillEffect)
  GET caster.Y (新 SkillEffect)

修改:
  newX 32900047 Params: [cos, MUL, r_acc(=320937), DIV, 10000, ADD, caster.X]
  newY 32900050 Params: [sin, MUL, r_acc, DIV, 10000, ADD, caster.Y]
  effective_facing 32900072 Params: [self.facing, ADD, -90] (清理残留 NodeRef 32900036)
  桥接 32900076 Params: [320938 PT=3, ADD, 0] (reset_vR 改读 initial_radius)
  SkillTag 320933 default 0 → 7 (推荐 r_step / 2 秒到 1000 码)
  BulletConfig 320258 LastTime 60 → 120 (2 秒生命)
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

# ====== Phase 0: 分配新 ID ======
alloc = IDAllocator()
caster_x_id = alloc.get_next('SkillEffectConfig')
caster_y_id = alloc.get_next('SkillEffectConfig')
print(f'New: GET caster.X = {caster_x_id} / GET caster.Y = {caster_y_id}')

# ====== Phase 1: 加 GET caster.X / GET caster.Y ======
next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

def make_get_attr(rid, ID, desc, attr, pos):
    return {
        "rid": rid,
        "type": {"class": "TSET_GET_ENTITY_ATTR_VALUE", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()), "computeOrder": 30,
            "position": {"serializedVersion": "2", "x": float(pos[0]), "y": float(pos[1]), "width": 280.0, "height": 140.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
            "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps({
                "ID": ID, "SkillEffectType": 32,
                "Params": [
                    {"Value": 4, "ParamType": 5, "Factor": 0},
                    {"Value": attr, "ParamType": 0, "Factor": 0},
                ],
            }, ensure_ascii=False),
            "Config2ID": f"SkillEffectConfig_{ID}",
            "SkillEffectType": 32,
        }
    }
data['references']['RefIds'].append(make_get_attr(next_rid,   caster_x_id, '读「主角 X 坐标」/ 风车中心', 59, (4500, -1300)))
data['references']['RefIds'].append(make_get_attr(next_rid+1, caster_y_id, '读「主角 Y 坐标」/ 风车中心', 60, (4500, -1100)))
data['nodes'].extend([{"rid": next_rid}, {"rid": next_rid+1}])
print('[ADD] GET caster.X, GET caster.Y')

# ====== Phase 2: 修改节点 Params ======
PARAM_UPDATES = {
    # newX = (cos × r_acc) / 10000 + caster.X
    32900047: [
        {"Value": 32900056, "ParamType": 2, "Factor": 0},   # cos
        {"Value": 5, "ParamType": 0, "Factor": 0},          # MUL
        {"Value": 32900041, "ParamType": 2, "Factor": 0},   # r_acc (GET vR_acc / SkillTag 320937)
        {"Value": 6, "ParamType": 0, "Factor": 0},          # DIV
        {"Value": 10000, "ParamType": 0, "Factor": 0},      # 固定 cos/sin 缩放
        {"Value": 3, "ParamType": 0, "Factor": 0},          # ADD
        {"Value": caster_x_id, "ParamType": 2, "Factor": 0}, # caster.X
    ],
    # newY = (sin × r_acc) / 10000 + caster.Y
    32900050: [
        {"Value": 32900057, "ParamType": 2, "Factor": 0},
        {"Value": 5, "ParamType": 0, "Factor": 0},
        {"Value": 32900041, "ParamType": 2, "Factor": 0},
        {"Value": 6, "ParamType": 0, "Factor": 0},
        {"Value": 10000, "ParamType": 0, "Factor": 0},
        {"Value": 3, "ParamType": 0, "Factor": 0},
        {"Value": caster_y_id, "ParamType": 2, "Factor": 0},
    ],
    # effective_facing = self.facing - 90 (清理残留 32900036)
    32900072: [
        {"Value": 32900055, "ParamType": 2, "Factor": 0},
        {"Value": 3, "ParamType": 0, "Factor": 0},
        {"Value": -90, "ParamType": 0, "Factor": 0},
    ],
    # 桥接节点改读 initial_radius (320938) 而不是 vR_initial (320934)
    32900076: [
        {"Value": 320938, "ParamType": 3, "Factor": 0},     # initial_radius PT=3
        {"Value": 3, "ParamType": 0, "Factor": 0},
        {"Value": 0, "ParamType": 0, "Factor": 0},
    ],
}

for nid, new_params in PARAM_UPDATES.items():
    for r in data['references']['RefIds']:
        cj_str = r['data'].get('ConfigJson', '') or '{}'
        cj = json.loads(cj_str)
        if cj.get('ID') == nid:
            cj['Params'] = new_params
            r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
            print(f'[FIX] {nid} Params')
            break

# ====== Phase 3: 调整 SkillTag default ======
SKILLTAG_DEFAULTS = {
    320933: 7,    # r_step (推荐: 2 秒扩 800 码 = 7/帧)
}
for nid, new_default in SKILLTAG_DEFAULTS.items():
    for r in data['references']['RefIds']:
        cj_str = r['data'].get('ConfigJson', '') or '{}'
        cj = json.loads(cj_str)
        if cj.get('ID') == nid and r['type']['class'] == 'SkillTagsConfigNode':
            cj['DefaultValue'] = new_default
            r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
            print(f'[FIX] SkillTag {nid} default → {new_default}')
            break

# ====== Phase 4: BulletConfig LastTime 60 → 120 ======
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == 320258 and r['type']['class'] == 'BulletConfigNode':
        cj['LastTime'] = 120
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print('[FIX] BulletConfig 320258 LastTime 60 → 120 (2 秒)')
        break

# ====== Phase 5: 从 ROOT_ORDER 移除 reset_angle (32900051) 引用 ======
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == 32900053:  # ROOT_ORDER
        old_len = len(cj['Params'])
        cj['Params'] = [p for p in cj['Params'] if p['Value'] != 32900051]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] ROOT_ORDER 32900053 Params: {old_len} → {len(cj["Params"])} (移除 reset_angle)')
        break

# ====== Phase 6: 删除废弃节点 ======
OBSOLETE_NODES = {32900035, 32900036, 32900037, 32900051}
OBSOLETE_TAGS = {320931, 320936, 320934, 320935}
ALL_DEL = OBSOLETE_NODES | OBSOLETE_TAGS

# 找到要删除的 GUIDs
del_guids = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') in ALL_DEL:
        del_guids.add(r['data']['GUID'])

# 删 RefIds + nodes
old_count = len(data['references']['RefIds'])
data['references']['RefIds'] = [r for r in data['references']['RefIds']
                                  if r['data']['GUID'] not in del_guids]
del_rids = {r['rid'] for r in data['references']['RefIds']}
# Actually we want to remove rids that are NOT in remaining refs
remaining_rids = set(r['rid'] for r in data['references']['RefIds'])
data['nodes'] = [n for n in data['nodes'] if n['rid'] in remaining_rids]
print(f'[DEL] {old_count - len(data["references"]["RefIds"])} obsolete nodes')

# 删 edges referencing del_guids
old_edges = len(data['edges'])
data['edges'] = [e for e in data['edges']
                  if e['inputNodeGUID'] not in del_guids and e['outputNodeGUID'] not in del_guids]
print(f'[DEL] {old_edges - len(data["edges"])} edges (refs to deleted nodes)')

# ====== Phase 7: 重建 newX/newY edges (新 caster.X/Y 接入) + effective_facing edges ======
guid_by_id = {json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID'): r['data']['GUID']
               for r in data['references']['RefIds']
               if json.loads(r['data'].get('ConfigJson', '') or '{}').get('ID') is not None}

# 删 newX P[6] 旧 edge (self.X → newX) 和 newY P[6] (self.Y → newY)
old_edges = len(data['edges'])
data['edges'] = [e for e in data['edges'] if not (
    (e['inputNodeGUID'] == guid_by_id.get(32900042) and e['outputNodeGUID'] == guid_by_id[32900047] and e['inputPortIdentifier'] == '6') or
    (e['inputNodeGUID'] == guid_by_id.get(32900048) and e['outputNodeGUID'] == guid_by_id[32900050] and e['inputPortIdentifier'] == '6')
)]
print(f'[DEL] {old_edges - len(data["edges"])} 旧 self.X/Y → newX/Y edges')

def make_edge(target_id, owner_id, outport='0'):
    return {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": guid_by_id[target_id],
        "outputNodeGUID": guid_by_id[owner_id],
        "inputFieldName": "ID", "outputFieldName": "PackedParamsOutput",
        "inputPortIdentifier": "0", "outputPortIdentifier": outport, "isVisible": True,
    }

# 加 caster.X → newX P[6], caster.Y → newY P[6]
data['edges'].append(make_edge(caster_x_id, 32900047, "6"))
data['edges'].append(make_edge(caster_y_id, 32900050, "6"))
print('[ADD] caster.X → newX P[6], caster.Y → newY P[6]')

# ====== Phase 8: 描述重写 + sticky note ======
SKILLTAG_DESC = {
    320932: '自旋速度（°/帧 = 整组风车每帧转多少）/ -6=1秒1圈 / 0=不转 / 负=顺时针',
    320933: '半径扩大速度（每帧 r 加多少）/ 7=2秒800码扩散 / 0=不扩散',
    320937: '【运行时存储 不要改】半径累加器 r / 由 ADD 节点自动累加',
    320938: '出生半径（叶子在主角周围多远爆发出现）/ 200=主角周围 200 码 / 0=贴脸',
}
for nid, desc in SKILLTAG_DESC.items():
    for r in data['references']['RefIds']:
        cj_str = r['data'].get('ConfigJson', '') or '{}'
        cj = json.loads(cj_str)
        if cj.get('ID') == nid and r['type']['class'] == 'SkillTagsConfigNode':
            cj['Desc'] = desc
            r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
            r['data']['Desc'] = desc
            break

NODE_DESC = {
    32900040: '【每帧步骤 2·半径扩大】r 半径 += SkillTag 320933 r_step',
    32900041: '读「半径累加值 r」',
    32900047: '计算「新 X」= 主角.X + 半径 × cos(θ) / 10000（绝对式：风车中心 + 半径方向）',
    32900050: '计算「新 Y」= 主角.Y + 半径 × sin(θ) / 10000',
    32900042: '【BeforeBorn 用】读「叶子当前 X 坐标」/ OnTick 用 caster.X 替代',
    32900048: '【BeforeBorn 用】读「叶子当前 Y 坐标」/ OnTick 用 caster.Y 替代',
    32900049: '【每帧步骤 3·瞬移到新位置】CHANGE_POSITION → (新 X, 新 Y)',
    32900052: '重置「半径累加 r 320937」= initial_radius（来自 SkillTag 320938，经桥接 32900076）',
    32900072: 'θ = 叶子朝向 - 90°（-90 抵消模型局部轴偏移）/ 给 cos/sin 用',
    32900075: '【每帧步骤 1·风车转动】叶子朝向 += spin_step（同时驱动视觉旋转 + θ 累加）',
    32900076: '【桥接节点】把 SkillTag 320938「initial_radius」当数值传给 reset_r',
}
for nid, desc in NODE_DESC.items():
    for r in data['references']['RefIds']:
        cj_str = r['data'].get('ConfigJson', '') or '{}'
        cj = json.loads(cj_str)
        if cj.get('ID') == nid:
            r['data']['Desc'] = desc
            break

# ====== Phase 9: 重写 sticky note (风车版) ======
sticky_title = "30212017 风车扩张子弹圈 PoC / 木宗门 · 人阶 · 奇术"
sticky_content = """【作用】
PoC 测试用技能。释放后 8 颗叶子在主角周围一圈爆发出现，整组作为风车绕主角同步旋转，半径同步线性扩大，最终飞到屏幕外消失。
模型：极坐标 (r, θ) 双累加（半径 + 角度独立）/ 物理上保证只向外扩张永不收缩。

【流程】
1. 释放 → 锁定主角位置作风车中心
2. 8 颗叶子同时生成，朝向各偏 45°
3. 每颗叶子出生瞬间 → 半径 r 重置为「出生半径」（200 码）
4. 每帧：
   - 整组角度 θ 转一点点（风车转动 / 视觉跟着转）
   - 每颗叶子的半径 r 增加一点（外扩）
   - 实际位置 = 主角位置 + r × (cos θ, sin θ)
5. 2 秒后（120 帧）叶子自动消失

【特殊条件】
- 每颗叶子独立累加 r 和 θ（旋转/扩散不互相影响）
- 物理上 r 单调增长 → 永远不会缩圈
- 旋转幅度无上限（叶子可以转好几圈）/ 因为位置由 r 决定，跟 θ 无累加关系

【参数】

▌出生位置
  320938「initial_radius」= 200 默认
    叶子离主角多远生成 / 0=贴脸 / 500=远离

▌自旋
  320932「spin_step」= -6 默认
    每帧整组转多少度 / -6=1秒1圈 / -12=1秒2圈 / 0=不转 / 负=顺时针

▌径向扩散
  320933「r_step」= 7 默认（推荐：2 秒扩散 800 码到 1000 码外）
    每帧半径增加多少 / 7=2秒扩800码 / 0=不扩散 / 大=越扩越远

▌运行时存储（不要改！）
  320937 r 累加器（半径运行时值）

【速查：想要什么效果 → 改哪个】
  叶子离主角更远生成 → 调大 320938（如 500）
  整组风车转得更快 → 320932 调更负（如 -12 / 1 秒 2 圈）
  扩散得更快 → 320933 调大（如 15 / 2 秒扩 1800 码）
  不要旋转（直线辐射）→ 320932 = 0
  不要扩散（原地风车转）→ 320933 = 0

【联动】
—（PoC / 后续移植到 30212010）"""

if 'stickyNotes' in data and data['stickyNotes']:
    data['stickyNotes'][0]['title'] = sticky_title
    data['stickyNotes'][0]['content'] = sticky_content
    print('[FIX] sticky note (风车模型版)')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(data["references"]["RefIds"])} / edges={len(data["edges"])}')
