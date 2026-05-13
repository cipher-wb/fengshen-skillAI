"""patch_30212017_mvp6a_flip_sign.py — 符号翻转 (-90 → +90)

把所有 CREATE_*  P[1] 视觉偏移从 -90 改成 +90
effective_facing 补偿从 +90 改成 -90

最终:
  CREATE_A NUM_CALC 32900073: cf - 90 → cf + 90
  32900059: cf + 0   → cf + 180
  32900060: cf - 45  → cf + 135
  32900062: cf + 45  → cf + 225
  32900064: cf + 90  → cf + 270
  32900066: cf + 135 → cf + 315
  32900068: cf + 180 → cf + 360 (= cf + 0)
  32900070: cf + 225 → cf + 45

  effective_facing 32900072 末项: +90 → -90
"""
import json
from pathlib import Path

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

# 把所有目标 NUM_CALC 的 P[2] 增加 180 (= -90 → +90, 实际旧值 + 180)
TARGETS = {32900073, 32900059, 32900060, 32900062, 32900064, 32900066, 32900068, 32900070}
EFF = 32900072

for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    nid = cj.get('ID')
    if nid in TARGETS:
        old = cj['Params'][2]['Value']
        new = old + 180
        cj['Params'][2]['Value'] = new
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = r['data'].get('Desc', '').replace(f'+{old}', f'+{new}').replace(f'+-{abs(old)}' if old < 0 else '', f'+{new}')
        print(f'[FIX] NUM_CALC {nid}: cf+{old} → cf+{new}')
    elif nid == EFF:
        # P[4] 末项 +90 → -90
        old = cj['Params'][4]['Value']
        cj['Params'][4]['Value'] = -old
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
        r['data']['Desc'] = f"effective_facing = self.facing + spin_angle + ({-old}) (符号翻转)"
        print(f'[FIX] effective_facing 末项: {old} → {-old}')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved')
