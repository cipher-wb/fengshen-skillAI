"""
patch_30212016_fix_repeat.py — 修 PostMortem #026 灾难组合

OnTick REPEAT 32390067 当前 Params[1]=-1 (count) / Params[2]=0 (interval)
→ C++ 引擎 iExecuteCount=2147483646 / iIntervalTime=0 → Crash

修复：Params[1] = 60 (count, lifetime 帧) / Params[2] = 1 (interval, 每帧)
"""
import json
from pathlib import Path

TARGET = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212016【木宗门】奇术_人阶_PoC_旋转扩张圈.json')

def main():
    data = json.loads(TARGET.read_text(encoding='utf-8'))
    fixed = 0
    for r in data['references']['RefIds']:
        if r['data'].get('ID') == 32390067 and r['type']['class'] == 'TSET_REPEAT_EXECUTE':
            cj = json.loads(r['data']['ConfigJson'])
            old_count = cj['Params'][1]['Value']
            old_interval = cj['Params'][2]['Value']
            cj['Params'][1]['Value'] = 60   # count = 60 frames (lifetime)
            cj['Params'][2]['Value'] = 1    # interval = 1 frame (per-frame tick)
            r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)
            print(f'[FIX] 32390067 OnTick REPEAT: count {old_count}->60 / interval {old_interval}->1')
            fixed += 1
            break

    if fixed == 0:
        print('[ERROR] 32390067 not found / no fix applied')
        return

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

    # grep self-verify
    data2 = json.loads(TARGET.read_text(encoding='utf-8'))
    for r in data2['references']['RefIds']:
        if r['data'].get('ID') == 32390067:
            cj = json.loads(r['data']['ConfigJson'])
            print(f'[VERIFY] 32390067 after write: count={cj["Params"][1]["Value"]} interval={cj["Params"][2]["Value"]}')
            assert cj['Params'][1]['Value'] == 60, 'count not 60'
            assert cj['Params'][2]['Value'] == 1, 'interval not 1'
            print('[OK] verified')

if __name__ == '__main__':
    main()
