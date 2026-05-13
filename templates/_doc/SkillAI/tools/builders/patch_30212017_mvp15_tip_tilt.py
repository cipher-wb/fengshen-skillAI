"""patch_30212017_mvp15_tip_tilt.py — 加 tip_tilt SkillTag (叶尖朝外掰)

用户反馈: 风车模型 OK 但叶尖切向太纯，要往外掰一点

数学:
  当前 self.facing init = caster.facing + offset_const (offset_const 各弹不同)
       effective_facing  = self.facing + 90 (用于 cos/sin 算位置)

  加 tilt 后:
       self.facing init = caster.facing + offset_const + tilt  (视觉 tip 朝外掰 tilt 度)
       effective_facing = self.facing + 90 - tilt              (抵消 tilt / 保持飞行方向)

  净效果: 视觉旋转 tilt 度, 飞行方向不变

新增:
  SkillTag 320939 `tip_tilt` default 30°
  NUM_CALC neg_tilt (新 ID): [tilt × -1] (用于 effective_facing 抵消)

修改:
  8 个视觉 NUM_CALC (32900073/059/060/062/064/066/068/070): 3项 → 5项 [old, ADD, tilt PT=3]
  effective_facing 32900072: 3项 → 5项 [old, ADD, neg_tilt PT=2]
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

alloc = IDAllocator()
tip_tilt_tag_id = alloc.get_next('SkillTagsConfig')
neg_tilt_id     = alloc.get_next('SkillEffectConfig')
print(f'New: tip_tilt SkillTag = {tip_tilt_tag_id} / neg_tilt NUM_CALC = {neg_tilt_id}')

# 验证没跟其他文件冲突
existing_st_ids = set()
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if r['type']['class'] == 'SkillTagsConfigNode':
        existing_st_ids.add(cj.get('ID'))
while tip_tilt_tag_id in existing_st_ids:
    tip_tilt_tag_id = alloc.get_next('SkillTagsConfig')
print(f'  (final tip_tilt SkillTag ID = {tip_tilt_tag_id})')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# ===== Phase 1: 加 SkillTag tip_tilt =====
tilt_tag_node = {
    "rid": next_rid,
    "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 16,
        "position": {"serializedVersion": "2", "x": 500.0, "y": 2700.0, "width": 237.0, "height": 135.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": tip_tilt_tag_id,
        "Desc": "叶尖外掰角度（° / 30=适度外掰 / 0=纯切向 / 90=纯径向外）/ 仅视觉/不影响飞行轨迹",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
        "ConfigJson": json.dumps({
            "ID": tip_tilt_tag_id, "TagType": 0,
            "Desc": "叶尖外掰角度",
            "NameKey": 0, "DefaultValue": 30,
            "FinalValueEffectID": 0, "RetainWhenDie": False,
        }, ensure_ascii=False),
        "Config2ID": f"SkillTagsConfig_{tip_tilt_tag_id}",
    }
}
data['references']['RefIds'].append(tilt_tag_node)
data['nodes'].append({"rid": next_rid})

# ===== Phase 2: 加 neg_tilt NUM_CALC (tilt × -1) =====
neg_tilt_node = {
    "rid": next_rid + 1,
    "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 27,
        "position": {"serializedVersion": "2", "x": 800.0, "y": 2700.0, "width": 240.0, "height": 110.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": neg_tilt_id,
        "Desc": "neg_tilt = -tip_tilt（抵消 effective_facing 用 / 保飞行方向不变）",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": neg_tilt_id, "SkillEffectType": 31,
            "Params": [
                {"Value": tip_tilt_tag_id, "ParamType": 3, "Factor": 0},
                {"Value": 5, "ParamType": 0, "Factor": 0},  # MUL
                {"Value": -1, "ParamType": 0, "Factor": 0},
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{neg_tilt_id}",
        "SkillEffectType": 31,
    }
}
data['references']['RefIds'].append(neg_tilt_node)
data['nodes'].append({"rid": next_rid + 1})
print('[ADD] tip_tilt SkillTag + neg_tilt NUM_CALC')

# ===== Phase 3: 修改 8 个视觉 NUM_CALC 从 3项 → 5项 (加 ADD + tilt_tag) =====
VISUAL_IDS = [32900073, 32900059, 32900060, 32900062, 32900064, 32900066, 32900068, 32900070]
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') in VISUAL_IDS:
        old_params = cj['Params']
        if len(old_params) == 3:  # 防御性: 只对当前 3 项的扩展
            cj['Params'] = old_params + [
                {"Value": 3, "ParamType": 0, "Factor": 0},   # ADD
                {"Value": tip_tilt_tag_id, "ParamType": 3, "Factor": 0},  # tip_tilt SkillTag
            ]
            r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
            print(f'[FIX] {cj["ID"]}: 3项 → 5项 (尾加 tip_tilt 偏移)')

# ===== Phase 4: 修改 effective_facing 32900072 从 3项 → 5项 (加 ADD + neg_tilt) =====
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == 32900072:
        old_params = cj['Params']
        cj['Params'] = old_params + [
            {"Value": 3, "ParamType": 0, "Factor": 0},
            {"Value": neg_tilt_id, "ParamType": 2, "Factor": 0},
        ]
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] effective_facing 32900072: 3项 → 5项 (尾加 -tilt 抵消)')
        break

# ===== Phase 5: edges =====
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

# neg_tilt → effective_facing P[4]
data['edges'].append(make_edge(neg_tilt_id, 32900072, "4"))
print(f'[ADD] 1 edge (neg_tilt → effective_facing P[4])')

# ===== Phase 6: 更新 sticky note 加 tip_tilt 参数说明 =====
for n in data.get('stickyNotes', []):
    if '风车' in n.get('title', ''):
        content = n['content']
        # 在「自旋」段后追加「叶尖朝向」段
        insert_pos = content.find('▌径向扩散')
        if insert_pos > 0:
            new_section = f"""▌叶尖朝向
  {tip_tilt_tag_id}「tip_tilt」= 30 默认
    叶尖往外掰角度（° / 0=纯切向 / 30=适度外掰 / 90=纯径向外）
    仅视觉效果 / 不影响飞行轨迹

"""
            content = content[:insert_pos] + new_section + content[insert_pos:]
            # 在速查段加一行
            speed_query = '【速查：想要什么效果 → 改哪个】'
            qpos = content.find(speed_query)
            if qpos > 0:
                qline = '【速查：想要什么效果 → 改哪个】\n  叶尖更朝外 → 调大 ' + str(tip_tilt_tag_id) + '（90=纯径向外 / -30=往里掰）'
                content = content.replace(speed_query, qline)
            n['content'] = content
            print('[FIX] sticky note 加 tip_tilt 段 + 速查')
        break

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / RefIds={len(data["references"]["RefIds"])} / edges={len(data["edges"])}')
