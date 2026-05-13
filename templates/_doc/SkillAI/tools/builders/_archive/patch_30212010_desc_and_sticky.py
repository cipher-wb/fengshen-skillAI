"""
patch_30212010_desc_and_sticky.py — 一次性 patch 脚本

任务：
1. 修复 rid=1041 / rid=1055 两 CREATE_BULLET 节点 Desc 错配（互换"普通子弹"<->"强化子弹"）
2. 给所有空 Desc 节点按 cls + group 智能填充
3. 添加 1 个 Sticky Note v3 模板（5 段：作用/流程/特殊条件/参数/联动）

不改任何 ID、节点结构、Buff/SkillInterrupt 的 DIRECT 定义。纯文本+元数据。
"""
import json
import uuid
from pathlib import Path

TARGET = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212010【木宗门】奇术_人阶_叶散风行.json')

# ─── Desc 生成策略 ─────────────────────────────────────
# 按 cls 给"骨架描述"，加上 group title 形成业务可读 Desc
CLS_DESC = {
    'TSET_ORDER_EXECUTE':           '顺序执行',
    'TSET_DELAY_EXECUTE':           '延迟触发',
    'TSET_REPEAT_EXECUTE':          '重复执行',
    'TSET_CONDITION_EXECUTE':       '条件分支',
    'TSET_SELECT_EXECUTE':          '选择执行',
    'TSET_NUM_CALCULATE':           '数值计算',
    'TSET_MATH_COS':                '余弦计算',
    'TSET_MATH_SIN':                '正弦计算',
    'TSET_GET_FIXTURE_CENTER_Z':    '取实体中心Z',
    'TSET_GET_ANGLE_BETWEEN_POINT': '两点夹角',
    'TSET_GET_SKILL_TAG_VALUE':     '查 SkillTag 值',
    'TSET_MODIFY_ENTITY_ATTR_VALUE':'改实体属性',
    'TSET_PLAY_SOUND':              '播放音效',
    'TSET_CREATE_BULLET':           '创建子弹',
    'TSET_ADD_BUFF':                '挂 Buff',
    'TSCT_NOT':                     '条件取反',
    'TSCT_VALUE_COMPARE':           '数值比较',
    'TSCT_NOT_SAME_CAMP':           '判敌方阵营',
    'TSCT_IS_TARGET_ENTITY_EXIST':  '目标存在判定',
    'TSKILLSELECT_CIRCLE':          '圆形目标筛选',
    'TSKILLSELECT_RANDOM_ENTITY':   '随机目标抽取',
    'RefConfigBaseNode':            '引用外部配置',
    'ModelConfigNode':              '模型配置',
    'SkillTagsConfigNode':          'SkillTag 声明',
    'BuffConfigNode':               'Buff 配置',
    'SkillConfigNode':              '技能根',
}

# 特殊覆写（rid -> 强制 Desc）
DESC_OVERRIDE = {
    1041: '强化子弹（创建强化飞叶 320110）',  # 原 Desc "普通子弹"误标
    1055: '普通子弹（创建普通飞叶 320112）',  # 原 Desc "强化子弹"误标
}

# ─── Sticky Note v3 内容 ─────────────────────────────
STICKY_TITLE = '叶散风行 30212010  木宗门·人阶·奇术'
STICKY_CONTENT = '''【作用】
木宗门人阶奇术，发射飞叶弹幕配合追踪+模拟轨迹的复合远程技能。

【流程】
1. 抬手 → 播放角色动作 + 释放音效
2. 释放 → 默认创建普通飞叶子弹
3. 飞叶飞行 → 模拟轨迹，目标进入追踪范围则改飞追踪逻辑
4. 击中 → 触发模拟击中（含真伤属性载体子弹）
5. 命中目标 → 挂免控 buff，单位不存在则停止模拟

【特殊条件】
- 满足强化条件 → 切换发射强化飞叶子弹（替代普通飞叶）
- 单位不存在 → SkillInterrupt 660009 停止整段模拟

【参数】
范围：800（圆形指示器）
节奏：抬手 0｜CD 900ms｜BD 30
子弹：4 类（普通飞叶 320112 / 强化飞叶 320110 / 追踪 320118 / 伤害属性载体 320117）
SkillTag：320098/320110/320127/320160（叶散风行 4 个内部计数 Tag，可调参）

【联动】
- 与 30212011 三重碧叶共享 SkillTag 320100（叶散风行触发记录到三重碧叶上的计数）
- 通用免控 Buff 320053
'''

def main():
    data = json.loads(TARGET.read_text(encoding='utf-8'))
    refids = data['references']['RefIds']
    rid_map = {r['rid']: r for r in refids}
    guid_to_rid = {r['data'].get('GUID'): r['rid'] for r in refids if r['data'].get('GUID')}

    # group title lookup by GUID
    guid_to_group = {}
    for g in data.get('groups', []):
        title = g.get('title', '')
        for guid in g.get('innerNodeGUIDs', []):
            guid_to_group[guid] = title

    fixed_count = 0
    overridden_count = 0
    unhandled_cls = set()

    for r in refids:
        rid = r['rid']
        cls = r['type']['class']
        d = r['data']
        cur_desc = d.get('Desc', '')

        # 1) Override 优先
        if rid in DESC_OVERRIDE:
            d['Desc'] = DESC_OVERRIDE[rid]
            overridden_count += 1
            continue

        # 2) 已有 Desc 不动
        if cur_desc.strip():
            continue

        # 3) 按 cls + group 生成
        skeleton = CLS_DESC.get(cls)
        if skeleton is None:
            unhandled_cls.add(cls)
            continue

        guid = d.get('GUID', '')
        group = guid_to_group.get(guid, '')

        if cls == 'RefConfigBaseNode':
            ref_id = d.get('ID', '?')
            new_desc = f'引用 [配置 {ref_id}]'
        elif cls in ('SkillTagsConfigNode', 'ModelConfigNode', 'BuffConfigNode', 'SkillConfigNode'):
            new_desc = skeleton
        else:
            if group:
                new_desc = f'{group}-{skeleton}'
            else:
                new_desc = skeleton

        d['Desc'] = new_desc
        fixed_count += 1

    # 4) 添加 Sticky Note v3（追加，不替换）
    new_sticky = {
        'GUID': str(uuid.uuid4()),
        'position': {
            'serializedVersion': '2',
            'x': -8000.0,
            'y': -300.0,
            'width': 460.0,
            'height': 540.0,
        },
        'title': STICKY_TITLE,
        'content': STICKY_CONTENT,
    }
    data.setdefault('stickyNotes', []).append(new_sticky)

    # Write back (ensure_ascii=False keeps Chinese, 4-space indent matches original style)
    out = json.dumps(data, ensure_ascii=False, indent=4)
    TARGET.write_text(out, encoding='utf-8')

    print(f'[OK] {fixed_count} empty Desc filled / {overridden_count} overrides applied / 1 sticky note added')
    if unhandled_cls:
        print(f'[WARN] Unhandled cls (kept empty Desc): {sorted(unhandled_cls)}')

if __name__ == '__main__':
    main()
