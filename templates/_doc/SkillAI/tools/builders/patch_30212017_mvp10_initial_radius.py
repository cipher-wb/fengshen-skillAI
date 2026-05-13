"""patch_30212017_mvp10_initial_radius.py — 接活 vR_initial SkillTag + 提升默认值

问题:
  之前 MVP-8 试图 reset_vR P[3]={V=320934, PT=3 SkillTag ref}, MODIFY_SKILL_TAG_VALUE
  P[3] 不支持 PT=3 → reset 失效 → 跨次释放速度累加 (用户已发现)

修法:
  加 NUM_CALC `vR_initial_bridge` (320934 SkillTag → PT=2 NodeRef)
  reset_vR P[3] = PT=2 NodeRef → 桥接 NUM_CALC

  同时改 SkillTag 320934 default 5 → 600 (~2m 出生爆发距离 / 子弹第 1 帧跳出)

效果:
  每次释放, reset 将 vR_acc 设为 SkillTag 320934 当前值 (default=600)
  Frame 1 OnTick: position += (cos × ~601) / position_scale (30000) ≈ 200cm = 2m
  视觉: 子弹立刻出现在主角 2m 外 + 继续按 vR_step 累加慢慢外扩
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

V_INITIAL_SKILLTAG = 320934
RESET_VR = 32900052

alloc = IDAllocator()
bridge_id = alloc.get_next('SkillEffectConfig')
print(f'New NUM_CALC bridge = {bridge_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Bridge NUM_CALC: P=[SkillTag 320934 PT=3, ADD, 0] = vR_initial 透传
bridge_node = {
    "rid": next_rid,
    "type": {"class": "TSET_NUM_CALCULATE", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 25,
        "position": {"serializedVersion": "2", "x": 800.0, "y": 2300.0, "width": 240.0, "height": 110.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": bridge_id,
        "Desc": "vR_initial 桥接 (SkillTag 320934 → NodeRef / 给 reset_vR 用)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
        "ConfigJson": json.dumps({
            "ID": bridge_id, "SkillEffectType": 31,
            "Params": [
                {"Value": V_INITIAL_SKILLTAG, "ParamType": 3, "Factor": 0},  # SkillTag value
                {"Value": 3, "ParamType": 0, "Factor": 0},      # ADD
                {"Value": 0, "ParamType": 0, "Factor": 0},      # +0 (identity)
            ],
        }, ensure_ascii=False),
        "Config2ID": f"SkillEffectConfig_{bridge_id}",
        "SkillEffectType": 31,
    }
}
data['references']['RefIds'].append(bridge_node)
data['nodes'].append({"rid": next_rid})
print(f'[ADD] bridge NUM_CALC {bridge_id}')

# Change reset_vR P[3] to PT=2 NodeRef to bridge
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == RESET_VR:
        old = dict(cj['Params'][3])
        cj['Params'][3] = {"Value": bridge_id, "ParamType": 2, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = "OnSkillStart: vR_acc = vR_initial (经桥接 / SkillTag 320934 真实生效)"
        print(f'[FIX] reset_vR P[3]: {old} → bridge NodeRef')
        break

# Bump SkillTag 320934 default value 5 → 600 + update Desc
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') == V_INITIAL_SKILLTAG and r['type']['class'] == 'SkillTagsConfigNode':
        old_default = cj.get('DefaultValue')
        cj['DefaultValue'] = 600
        cj['Desc'] = '出生爆发量 (~=初始半径 cm / 0=贴主角 / 600≈2m / 1500≈5m)'
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = '出生爆发量 ~= 初始半径'
        print(f'[FIX] SkillTag 320934 DefaultValue: {old_default} → 600')
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

# SkillTag 320934 → bridge P[0] (但 PT=3 自动连接，不一定要 edge? 仍然按惯例加)
# bridge → reset_vR P[3]
data['edges'].append(make_edge(bridge_id, RESET_VR, "3"))
print(f'[ADD] 1 edge / total = {len(data["edges"])}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved')
