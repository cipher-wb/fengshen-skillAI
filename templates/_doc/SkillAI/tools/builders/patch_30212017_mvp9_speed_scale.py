"""patch_30212017_mvp9_speed_scale.py — 加 position_scale SkillTag (减速旋钮)

newX/newY 公式当前: ((cos/sin × vR_acc) / 10000) + X / Y

10000 是 cos/sin 的定点放大倍率 / 越大 = 每帧位移越小 = 飞得越慢

提取为 SkillTag position_scale (default=30000 / 3x 比原来慢):
  策划可在 SkillEditor SkillTag 面板直接调
  10000 = 原速度 / 30000 = 3x 慢 / 50000 = 5x 慢

改造:
  newX (32900047) P[4]: {V=10000, PT=0} → {V=position_scale_id, PT=3}
  newY (32900050) P[4]: 同上
"""
import json, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from id_allocator import IDAllocator

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

alloc = IDAllocator()
pos_scale_id = alloc.get_next('SkillTagsConfig')
print(f'New SkillTag position_scale = {pos_scale_id}')

next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1

# Add SkillTagsConfig position_scale (default=30000)
node = {
    "rid": next_rid,
    "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
    "data": {
        "GUID": str(uuid.uuid4()), "computeOrder": 14,
        "position": {"serializedVersion": "2", "x": 500.0, "y": 2300.0, "width": 237.0, "height": 135.0},
        "expanded": False, "debug": False, "nodeLock": False, "visible": True,
        "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
        "ID": pos_scale_id, "Desc": "每帧位移分母 (越大越慢 / default=30000 / 原 10000)",
        "paramVersion": 0, "templateParamVersion": 0,
        "IsTemplate": False, "TemplateFlags": 0, "TemplateParams": [],
        "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
        "TableTash": "6A8A6883BDFDA1411BB2461E65CB2D9B",
        "ConfigJson": json.dumps({
            "ID": pos_scale_id, "TagType": 0,
            "Desc": "每帧位移分母 / 越大越慢",
            "NameKey": 0, "DefaultValue": 30000,
            "FinalValueEffectID": 0, "RetainWhenDie": False,
        }, ensure_ascii=False),
        "Config2ID": f"SkillTagsConfig_{pos_scale_id}",
    }
}
data['references']['RefIds'].append(node)
data['nodes'].append({"rid": next_rid})
print(f'[ADD] SkillTag {pos_scale_id} (default=30000)')

# Modify newX (32900047) and newY (32900050) P[4]
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    if cj.get('ID') in (32900047, 32900050):
        old = dict(cj['Params'][4])
        cj['Params'][4] = {"Value": pos_scale_id, "ParamType": 3, "Factor": 0}
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        print(f'[FIX] {cj["ID"]} P[4]: {old} → SkillTag {pos_scale_id} PT=3')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved')
