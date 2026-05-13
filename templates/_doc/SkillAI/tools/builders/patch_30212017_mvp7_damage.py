"""patch_30212017_mvp7_damage.py — MVP-7: 加碰撞检测 + 伤害

用引擎标准模板:
  190016404 子弹通用逻辑-碰撞 (圆形检测, 敌军, 每帧检测, 10 帧命中冷却)
  190016485 子弹通用逻辑-伤害 (木属性 P[6]=2, 标签号 16)

参照真实 30212010 (32003083 + 32003085) 的参数填法。

OnTick 32900046 ORDER 改造 (4 items):
  [MODIFY_facing, ADD_vR, CHANGE_POS, 碰撞]
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

ORDER_ID = 32900046

alloc = IDAllocator()
damage_id  = alloc.get_next('SkillEffectConfig')
collide_id = alloc.get_next('SkillEffectConfig')
print(f'New: 伤害={damage_id} / 碰撞={collide_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Node 1: 伤害模板调用 (RUN_SKILL_EFFECT_TEMPLATE 190016485)
damage_node = {
    "rid": next_rid,
    "type": {"class": "TSET_RUN_SKILL_EFFECT_TEMPLATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 80,
        "position": {"serializedVersion": "2", "x": 3450.0, "y": -500.0, "width": 320.0, "height": 360.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": damage_id, "Desc": "伤害模板调用 (木属性 / 标签号 16)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": damage_id, "SkillEffectType": 5,  # RUN_SKILL_EFFECT_TEMPLATE
            "Params": [
                {"Value": 1, "ParamType": 5, "Factor": 0},        # P[0] caster (MAIN_ENTITY)
                {"Value": 2, "ParamType": 5, "Factor": 0},        # P[1] target (hit-target slot)
                {"Value": 190016485, "ParamType": 0, "Factor": 0}, # P[2] template ID
                {"Value": 1, "ParamType": 0, "Factor": 0},        # P[3] 子弹序号 (填5即可，这里 1 仿 30212010)
                {"Value": 6, "ParamType": 5, "Factor": 0},        # P[4] 伤害来源 commonparam
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[5] 伤害类型 0=用技能
                {"Value": 2, "ParamType": 0, "Factor": 0},        # P[6] 伤害属性 = 2 (木)
                {"Value": 16, "ParamType": 0, "Factor": 0},       # P[7] 伤害标签号 16
                {"Value": -1, "ParamType": 0, "Factor": 0},       # P[8] 自定义增益系数 -1
                {"Value": -1, "ParamType": 0, "Factor": 0},       # P[9] 自定义增益伤害 -1
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[10] 比例增益-技能数据
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[11] 比例增益-方式
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[12] 比例增益-值
                {"Value": 1, "ParamType": 0, "Factor": 0},        # P[13] 命中后是否结束 = 1
                {"Value": -1, "ParamType": 0, "Factor": 0},       # P[14] 护盾免疫忽略量
                {"Value": -1, "ParamType": 0, "Factor": 0},       # P[15] 暴击千分值
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{damage_id}",
        "SkillEffectType": 5,
    }
}

# Node 2: 碰撞模板调用 (RUN_SKILL_EFFECT_TEMPLATE 190016404)
collide_node = {
    "rid": next_rid + 1,
    "type": {"class": "TSET_RUN_SKILL_EFFECT_TEMPLATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 81,
        "position": {"serializedVersion": "2", "x": 3450.0, "y": -900.0, "width": 320.0, "height": 360.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": collide_id, "Desc": "碰撞检测 (圆形半径 80 / 敌军 / 检测间隔 1 帧)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": collide_id, "SkillEffectType": 5,
            "Params": [
                {"Value": 1, "ParamType": 5, "Factor": 0},        # P[0] caster
                {"Value": 2, "ParamType": 5, "Factor": 0},        # P[1] target
                {"Value": 190016404, "ParamType": 0, "Factor": 0}, # P[2] template ID
                {"Value": damage_id, "ParamType": 0, "Factor": 0}, # P[3] 命中函数 = 伤害节点
                {"Value": 1, "ParamType": 0, "Factor": 0},        # P[4] 碰撞范围类型 = 1 (圆形)
                {"Value": 80, "ParamType": 0, "Factor": 0},       # P[5] 半径 80
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[6] 圆形无用
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[7] 圆形无用
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[8] 位置偏移_右
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[9] 位置偏移_前
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[10] 目标单位类型 = 0 (敌军)
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[11] 自定义条件
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[12] 反馈创建者
                {"Value": 1, "ParamType": 0, "Factor": 0},        # P[13] 检测间隔 1 帧
                {"Value": 10, "ParamType": 0, "Factor": 0},       # P[14] 命中冷却 10 帧
                {"Value": 0, "ParamType": 0, "Factor": 0},        # P[15] 击中数 0 (跟生命一致)
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{collide_id}",
        "SkillEffectType": 5,
    }
}

data['references']['RefIds'].extend([damage_node, collide_node])
data['nodes'].extend([{"rid": next_rid}, {"rid": next_rid + 1}])
print(f'[ADD] 2 nodes (伤害 + 碰撞)')

# Append 碰撞 to OnTick ORDER 32900046 Params
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == ORDER_ID:
        old_count = len(cj['Params'])
        cj['Params'].append({"Value": collide_id, "ParamType": 0, "Factor": 0})
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "[OnTick] 4 项: MODIFY_facing / ADD_vR / CHANGE_POS / 碰撞"
        print(f'[FIX] ORDER 32900046 Params: {old_count} → {len(cj["Params"])} items')
        break

# Build guid map + edges
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

# 伤害 → 碰撞 P[3] (命中函数)
data['edges'].append(make_edge(damage_id, collide_id, "3"))
# 碰撞 → ORDER (dynamic port='0')
data['edges'].append(make_edge(collide_id, ORDER_ID, "0"))
print(f'[ADD] 2 edges / total = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved / total RefIds = {len(data["references"]["RefIds"])} / edges = {len(data["edges"])}')
