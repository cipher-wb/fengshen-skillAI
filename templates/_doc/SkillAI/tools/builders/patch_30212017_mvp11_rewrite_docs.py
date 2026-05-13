"""patch_30212017_mvp11_rewrite_docs.py — 重写 sticky note + 关键节点 Desc

用户反馈: 现在描述太抽象，看不懂。

修法:
  - sticky note 按团队 v3 模板（作用/流程/特殊条件/参数/联动）重写
  - 关键节点 Desc 改成"做什么 + 为什么"通俗版
"""
import json
from pathlib import Path

P = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30212017【MVP1】单弹直线右移.json')
data = json.loads(P.read_text(encoding='utf-8'))

# ============ 1. Sticky Note 重写 ============
sticky_title = "30212017 旋转扩张子弹圈 PoC / 木宗门 · 人阶 · 奇术"
sticky_content = """【作用】
PoC 测试用技能。释放后 8 颗叶子绕主角散开 + 自旋 + 外扩。验证「旋转扩张子弹圈」机制可行性，为后续真实技能（如 30212010 叶散风行）做底版。

【流程】
1. 释放 → 锁定主角当前位置 + 朝向作为基准
2. OnSkillStart → 重置 vR_acc 为「出生爆发量」+ 同时生成 8 颗子弹
   - 8 颗各朝主角周围 8 个方向（每隔 45°）
   - 每颗朝向 = 主角朝向 + 自身偏移（0/45/90/.../315°）
3. 每帧 OnTick（每颗子弹独立执行）
   - 当前朝向 += 旋转步长（视觉跟飞行同步转）
   - vR_acc += 加速步长（速度累加）
   - 沿当前朝向移动（按 vR_acc / 位移分母 计算）
4. 子弹生命 60 帧（约 1 秒）→ 自动消失

【特殊条件】
- 每颗子弹的角度累加器独立（per-bullet SkillTag 槽位 / MVP-5a 已验证）
- 视觉旋转通过 MODIFY entity.faceDir 驱动 / 不是 SkillTag 累加器（MVP-6a-final 已验证）
- 暂未接入命中伤害（MVP-7 模板崩溃跳过 / 待后续手拖配）

【参数】
旋转速度：SkillTag 320932「spin_step」每帧角度 / 默认 -8（≈480°/秒 / 负=顺时针）
速度累加：SkillTag 320933「vR_step」每帧速度增量 / 默认 1（0=匀速 / 负=减速）
初始半径：SkillTag 320934「vR_initial」出生爆发量 / 默认 600（≈2m / 0=贴主角 / 1500≈5m）
飞行快慢：SkillTag 320935「position_scale」位移分母 / 默认 30000（越大越慢 / 原值 10000）
子弹数：8（结构性，不可调）
朝向分布：0/45/90/...315°（结构性，不可调）

【联动】
—（PoC 不接技能链 / 后续转 30212010 时考虑）"""

if 'stickyNotes' in data and len(data['stickyNotes']) > 0:
    data['stickyNotes'][0]['title'] = sticky_title
    data['stickyNotes'][0]['content'] = sticky_content
    print('[FIX] sticky note 已重写 (v3 五段)')

# ============ 2. 节点 Desc 重写 ============
DESC_MAP = {
    # SkillTag 暴露参数
    320932: ('SkillTagsConfigNode',
             '每帧旋转角度（°/帧 / 负=顺时针 / 越大转越快 / 0=不自旋）',
             '每帧旋转角度（°/帧 / 负=顺时针）'),
    320933: ('SkillTagsConfigNode',
             '每帧速度累加（0=匀速 / 负=减速 / 越大加速越快）',
             '每帧速度累加'),
    320934: ('SkillTagsConfigNode',
             '出生爆发量（cm / 0=贴主角 / 600≈2m / 1500≈5m）',
             '出生爆发量 ≈ 初始半径'),
    320935: ('SkillTagsConfigNode',
             '位移分母（越大飞越慢 / 默认 30000 / 原值 10000）',
             '位移分母 / 越大越慢'),
    # ROOT_ORDER (OnSkillStart)
    32900053: (None, None, '【OnSkillStart 总入口】1.重置角度 / 2.重置速度 / 3-10.生成 8 颗子弹'),
    32900051: (None, None, '重置自旋累加器 = 0（防跨次释放累加）'),
    32900052: (None, None, '重置速度 vR_acc = 出生爆发量（SkillTag 320934）'),
    32900076: (None, None, '桥接节点：把 SkillTag 320934 当 value 喂给 reset_vR'),
    # OnSkillStart: GET caster facing
    32900058: (None, None, '读主角当前朝向（attr=91）'),
    # CREATE_A NUM_CALC
    32900073: (None, None, '弹A 视觉旋转 = 主角朝向 + 90°（90 = 模型局部轴补偿）'),
    # 8 NUM_CALCs (视觉角度，含 +90 补偿)
    32900059: (None, None, '弹B 视觉旋转 = 主角朝向 + 180°（飞行方向 = 主角朝向 + 90°）'),
    32900060: (None, None, '弹C 视觉旋转 = 主角朝向 + 135°（飞行方向 = 主角朝向 + 45°）'),
    32900062: (None, None, '弹D 视觉旋转 = 主角朝向 + 225°（飞行方向 = 主角朝向 + 135°）'),
    32900064: (None, None, '弹E 视觉旋转 = 主角朝向 + 270°（飞行方向 = 主角朝向 + 180°）'),
    32900066: (None, None, '弹F 视觉旋转 = 主角朝向 + 315°（飞行方向 = 主角朝向 + 225°）'),
    32900068: (None, None, '弹G 视觉旋转 = 主角朝向 + 360°（飞行方向 = 主角朝向 + 270°）'),
    32900070: (None, None, '弹H 视觉旋转 = 主角朝向 + 405°（飞行方向 = 主角朝向 + 315°）'),
    # CREATE_BULLET (8 个)
    32900045: (None, None, '生成 弹A（飞向主角正前 / 0°）'),
    32900054: (None, None, '生成 弹B（左前 / 主角朝向 + 90°）'),
    32900061: (None, None, '生成 弹C（前左 / 主角朝向 + 45°）'),
    32900063: (None, None, '生成 弹D（左后 / 主角朝向 + 135°）'),
    32900065: (None, None, '生成 弹E（正后 / 主角朝向 + 180°）'),
    32900067: (None, None, '生成 弹F（右后 / 主角朝向 + 225°）'),
    32900069: (None, None, '生成 弹G（右 / 主角朝向 + 270°）'),
    32900071: (None, None, '生成 弹H（右前 / 主角朝向 + 315°）'),
    # OnTick chain
    32900044: (None, None, '【BulletConfig AfterBorn 入口】每帧执行 OnTick 链'),
    32900043: (None, None, '【OnTick REPEAT】每帧触发 1 次 / 共 60 帧 (=1 秒生命)'),
    32900046: (None, None, '【OnTick body】每帧 ORDER 顺序：1.旋转 / 2.加速 / 3.移动'),
    32900075: (None, None, '每帧旋转：self.facing += spin_step（同步驱动视觉 + 飞行）'),
    32900074: (None, None, '计算下一帧 facing = 当前 facing + spin_step（SkillTag 320932）'),
    32900055: (None, None, '读子弹自身朝向（attr=91）'),
    32900040: (None, None, '每帧加速：vR_acc += vR_step（SkillTag 320933）'),
    32900041: (None, None, '读 vR_acc 当前值'),
    32900049: (None, None, '应用新位置（瞬移到 newX, newY）'),
    32900047: (None, None, 'newX = (cos(飞行角) × vR_acc) / 位移分母 + 原 X'),
    32900050: (None, None, 'newY = (sin(飞行角) × vR_acc) / 位移分母 + 原 Y'),
    32900042: (None, None, '读子弹当前 X 坐标（attr=59）'),
    32900048: (None, None, '读子弹当前 Y 坐标（attr=60）'),
    32900056: (None, None, 'cos(飞行角)'),
    32900057: (None, None, 'sin(飞行角)'),
    32900072: (None, None, '飞行角 = self.facing - 90（-90 = 抵消视觉补偿 → 真实飞行方向）'),
    # 旧角度累加器（已废弃 / 但还在 OnTick 中？让我标"废弃"）
    32900035: (None, None, '（旧/已撤离 OnTick）SkillTag 320198 += 5 / MVP-2b 振荡时期遗留'),
    32900036: (None, None, '（旧）读 320198 / 已不参与计算'),
    32900037: (None, None, '（旧）COS(320198) / 已不参与计算'),
    # SkillTags 内部存储
    320198: ('SkillTagsConfigNode', None, '（运行时存储槽 / 旧 angle_acc / 已废弃）'),
    320199: ('SkillTagsConfigNode', None, '（运行时存储槽 / vR_acc 每帧累加值）'),
    320931: ('SkillTagsConfigNode', None, '（旧 birth offset / MVP-5b 时期 / 已撤离主链路）'),
}

count = 0
for r in data['references']['RefIds']:
    cj_str = r['data'].get('ConfigJson', '') or '{}'
    cj = json.loads(cj_str)
    nid = cj.get('ID')
    if nid not in DESC_MAP:
        continue
    cls_filter, st_desc, node_desc = DESC_MAP[nid]
    if cls_filter and r['type']['class'] != cls_filter:
        continue
    if node_desc:
        r['data']['Desc'] = node_desc
        count += 1
    if st_desc and r['type']['class'] == 'SkillTagsConfigNode':
        cj['Desc'] = st_desc
        r['data']['ConfigJson'] = json.dumps(cj, ensure_ascii=False)

print(f'[FIX] 重写 {count} 个节点 Desc')

P.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
print(f'\n[OK] saved')
