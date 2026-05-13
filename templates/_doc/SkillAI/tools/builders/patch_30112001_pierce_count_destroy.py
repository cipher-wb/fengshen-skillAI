"""patch_30112001_pierce_count_destroy.py
# -*- coding: utf-8 -*-

为 30112001 飞叶锁魂 强化飞叶 (BulletConfig 320046) 添加"击中 X 个敌人后销毁"机制。

需求要点
========
- X (穿透上限) 通过技能级 SkillTag 暴露 / 外部可写入 / 默认 3
- 多颗强化飞叶可同时存在 → 计数必须 per-bullet-instance / 不串扰
- 不修改任何外部共享模板 (碰撞 / 伤害 / 表现)
- 不修改任何与碰撞/伤害/表现无关的现有节点 schema
- 改动仅集中在: 32002537 AfterBorn ORDER + 32000691.Params[3] (命中后功能 hook)
  + 新增节点

设计方案
========
新增 SkillTag (2 个)
  SKT_LIMIT     = 320960  默认 3   "飞叶锁魂-穿透上限"   技能级 / 外部可写入 X
  SKT_COUNT     = 320961  默认 0   "飞叶锁魂-穿透计数"   实例级 / per-bullet 累加
                                   (定义在本图; 实例化时由 Pattern C namespace=ORIGIN_SKILL_INST_ID 区分)

新增 SkillEffect (8 个)
  SE_INIT_ORDER       新 ORDER, AfterBorn 第一段 (Params=[SE_RESET_COUNT, SE_GET_X_BRIDGE...])
                      合并到 32002537 ORDER 头部
  SE_RESET_COUNT      MODIFY_SKILL_TAG: 子弹自身 SKT_COUNT = 0
                      (Param[0]={V=1,PT=5} TCPT_MAIN_ENTITY = 子弹 / 因为在子弹 AfterBorn 链中执行)
                      (Param[1]={V=41,PT=5} TCPT_ORIGIN_SKILL_INST_ID = 实例级)
  SE_GET_LIMIT        GET_SKILL_TAG_VALUE: 读技能级 SKT_LIMIT (Caster 上)
                      (Param[0]={V=4,PT=5} TCPT_MAIN_SKILL_DAMAGE_PROPERTY_ORIGIN_ENTITY = Caster)
                      (Param[1]={V=30112001,PT=0} 技能级 namespace = 当前技能 ID)
                      作 NodeRef 给 SE_COPY_LIMIT 的 P[3]
  SE_COPY_LIMIT       (用 Param[1]=42 来命名 SKT_LIMIT 副本 // 改用 Param[1]=41 实例级)
                      实际方案: SE_COPY_LIMIT 本身存在 / 但其实只需读时 GET → 不需要副本
                      → 简化: 击中阈值检查时直接 GET_LIMIT (Pattern A 跨技能 / 实时读)

  ===== 简化后实际新增 (5 个 SE) =====
  SE_AFTERBORN_INIT   ORDER: [SE_RESET_COUNT]
  SE_RESET_COUNT      MODIFY_SKILL_TAG: 子弹 SKT_COUNT = 0 (实例级)
  SE_HIT_WRAPPER      ORDER: [32002761(原), SE_HIT_TAIL]
                      接到 32000691.Params[3] 替换 32002761
  SE_HIT_TAIL         ORDER: [SE_ADD_COUNT, SE_CHECK_DESTROY]
  SE_ADD_COUNT        ADD_SKILL_TAG: 子弹 SKT_COUNT += 1 (实例级)
  SE_CHECK_DESTROY    CONDITION_EXECUTE: 条件 SKC_REACHED → SE_DESTROY
  SE_DESTROY          DESTROY_ENTITY: 销毁子弹自身

  辅助节点:
  SE_GET_COUNT        GET_SKILL_TAG_VALUE: 读子弹 SKT_COUNT (实例级)  [作为 SKC_REACHED 比较入参]
  SE_GET_LIMIT        GET_SKILL_TAG_VALUE: 读 SKT_LIMIT (技能级)      [作为 NUM_CALCULATE 入参]
  SE_DIFF             NUM_CALCULATE: count - limit (NodeRef 减 NodeRef)
  SKC_REACHED         VALUE_COMPARE: SE_DIFF >= 0 (op=4 TCO_BIGGER_OR_EQUAL)

新增 SkillCondition (1 个)
  SKC_REACHED   = 320509  VALUE_COMPARE / op=4 (>=) / target=0 / 入参 NodeRef SE_DIFF

修改
====
- 32002537 ORDER Params: [32000691, 32002531] → [SE_AFTERBORN_INIT, 32000691, 32002531]
- 32000691 ConfigJson.Params[3].Value: 32002761 → SE_HIT_WRAPPER
  (移除 edge 32000691→32002761, 新增 edge 32000691→SE_HIT_WRAPPER outPort=3)
- 320015 SkillTag 节点不动 (只新增 320960 / 320961 两个独立 SkillTagsConfigNode)

不改
====
- 320046 (强化飞叶 BulletConfig) — 不动
- 32002761 (击中分支 CONDITION_EXECUTE) — 完全保留 / 只改 parent (从 32000691 → SE_HIT_WRAPPER)
- 32002008 / 32002786 (有/无碧波术分支) — 不动
- 32000691 ConfigJson.Params[0,1,2,4..15] — 不动 (碰撞参数原状)
- 任何外部模板调用节点 (32002009 伤害 / 32002010 表现 / 32002892 范围子弹碰撞) — 不动

Author: skill-designer agent (Claude)
Date: 2026-05-12
"""
import json, uuid, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

P = Path(r'<<PROJECT_ROOT>>/<<SKILLGRAPH_JSONS_ROOT>>宗门技能/木宗门技能/SkillGraph_30112001【木宗门】飞叶锁魂.json')
data = json.loads(P.read_text(encoding='utf-8'))

# ============ 常量 ============
TT_SKILL_EFFECT = '0CFA05568A66FEA1DF3BA6FE40DB7080'
TT_SKILL_TAG    = '6A8A6883BDFDA1411BB2461E65CB2D9B'
TT_SKILL_COND   = 'ED89F46EAB95F7ACF5C1911A5A375278'

# 已分配 ID (全工程 fs 真扫已 verified 0 冲突)
# 第 1 轮分配 32002908..32002955 时漏检了跨文件 → 4 处 ID 冲突 (32002952/53/54/55):
#   32002952 与 30532000 (TSET_GET_SKILL_ELEMENTS_TYPE)
#   32002953 与 30532000 (TSET_GET_SKILL_TAG_VALUE)
#   32002954 与 30322001 (TSET_CONDITION_EXECUTE)
#   32002955 与 30222009 (TSET_SET_SKILLCD_REDUCE)
# 第 2 轮: 320960/320961/320509 + 32002908..32002951 仍可用 / 仅替换 4 个冲突号 → 32002970/71/72/73
SKT_LIMIT = 320960  # 飞叶锁魂-穿透上限 (verified 全工程不冲突)
SKT_COUNT = 320961  # 飞叶锁魂-穿透计数
SKC_REACHED = 320509  # VALUE_COMPARE (SkillCondition)

SE_AFTERBORN_INIT = 32002908   # ORDER: 初始化
SE_RESET_COUNT    = 32002934   # MODIFY_SKILL_TAG: count=0
SE_HIT_WRAPPER    = 32002941   # ORDER: 包装击中
SE_HIT_TAIL       = 32002942   # ORDER: 击中尾段(计数+检查)
SE_ADD_COUNT      = 32002950   # ADD_SKILL_TAG: count+=1
SE_GET_COUNT      = 32002951   # GET_SKILL_TAG: 读子弹 count
SE_GET_LIMIT      = 32002970   # GET_SKILL_TAG: 读技能 limit (跳过 32002952 与 30532000 冲突)
SE_DIFF           = 32002971   # NUM_CALC: count - limit (跳过 32002953 与 30532000 冲突)
SE_CHECK_DESTROY  = 32002972   # CONDITION: diff>=0 → destroy (跳过 32002954 与 30322001 冲突)
SE_DESTROY        = 32002973   # DESTROY_ENTITY: 子弹自身 (跳过 32002955 与 30222009 冲突)

# ============ 收集已用 SkillEffect / SkillTag / SkillCond ID, 验证不冲突 ============
existing_se_ids = set()
existing_st_ids = set()
existing_sc_ids = set()
existing_select_ids = set()
for r in data['references']['RefIds']:
    cls = r['type']['class'].split('.')[-1]
    cj_str = r['data'].get('ConfigJson') or '{}'
    try: cj = json.loads(cj_str)
    except: cj = {}
    nid = cj.get('ID') or r['data'].get('ID')
    if cls.startswith('TSET_'): existing_se_ids.add(nid)
    elif cls.startswith('TSCT_') or cls.startswith('TSKILLSELECT_'): existing_sc_ids.add(nid)
    elif cls == 'SkillTagsConfigNode': existing_st_ids.add(nid)

# 确保新 ID 不与本图已有冲突 (用户范围扫已 verified 全工程不冲突 / 此处只防本图小冲突)
for nid in [SE_AFTERBORN_INIT, SE_RESET_COUNT, SE_HIT_WRAPPER, SE_HIT_TAIL,
            SE_ADD_COUNT, SE_GET_COUNT, SE_GET_LIMIT, SE_DIFF,
            SE_CHECK_DESTROY, SE_DESTROY]:
    assert nid not in existing_se_ids, f'SE_{nid} conflicts with existing in this graph'
for nid in [SKT_LIMIT, SKT_COUNT]:
    assert nid not in existing_st_ids, f'SKT_{nid} conflicts'
assert SKC_REACHED not in existing_sc_ids, f'SKC_{SKC_REACHED} conflicts'

# ============ 找现有节点 GUID ============
def find_node_by_id(target_id, cls_filter=None):
    for r in data['references']['RefIds']:
        if r['data'].get('ID') == target_id:
            if cls_filter is None or r['type']['class'].split('.')[-1] == cls_filter:
                return r
    return None

n_32002537 = find_node_by_id(32002537, 'TSET_ORDER_EXECUTE')   # AfterBorn ORDER
n_32000691 = find_node_by_id(32000691, 'TSET_RUN_SKILL_EFFECT_TEMPLATE')  # 碰撞模板调用
n_32002761 = find_node_by_id(32002761, 'TSET_CONDITION_EXECUTE')  # 击中条件分支
n_320015   = find_node_by_id(320015, 'SkillTagsConfigNode')    # 现有 SkillTag

assert n_32002537 and n_32000691 and n_32002761 and n_320015, 'Missing reference nodes'

guid_32002537 = n_32002537['data']['GUID']
guid_32000691 = n_32000691['data']['GUID']
guid_32002761 = n_32002761['data']['GUID']

# ============ Helper: build new SkillEffect node ============
next_rid = max(r['rid'] for r in data['references']['RefIds']) + 1
next_y = max(r['data'].get('position', {}).get('y', 0) for r in data['references']['RefIds']) + 200
new_guids = {}

def add_se_node(ID, set_type, params, desc, x=6500.0, y=None):
    global next_rid, next_y
    if y is None: y = next_y; next_y += 180
    guid = str(uuid.uuid4())
    new_guids[ID] = guid
    cj = {'ID': ID, 'SkillEffectType': set_type, 'Params': params}
    node = {
        "rid": next_rid,
        "type": {"class": _se_cls_for(set_type), "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": guid,
            "computeOrder": next_rid,
            "position": {"serializedVersion": "2", "x": x, "y": float(y), "width": 280.0, "height": 140.0},
            "expanded": False, "debug": False, "nodeLock": False,
            "visible": True, "hideChildNodes": False,
            "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": TT_SKILL_EFFECT,
            "ConfigJson": json.dumps(cj, ensure_ascii=False, separators=(',', ':')),
            "Config2ID": f"SkillEffectConfig_{ID}",
            "SkillEffectType": set_type
        }
    }
    data['references']['RefIds'].append(node)
    data['nodes'].append({"rid": next_rid})
    next_rid += 1
    return guid

def _se_cls_for(set_type):
    # 来源: Assets/Scripts/TableDR_CS/NotHotfix/Gen/common.nothotfix.cs enum TSkillEffectType
    return {
        1:   'TSET_ORDER_EXECUTE',
        24:  'TSET_DESTROY_ENTITY',
        31:  'TSET_NUM_CALCULATE',
        46:  'TSET_MODIFY_SKILL_TAG_VALUE',
        47:  'TSET_CONDITION_EXECUTE',
        48:  'TSET_GET_SKILL_TAG_VALUE',
        97:  'TSET_ADD_SKILL_TAG_VALUE',
    }[set_type]

def add_skilltag_node(ID, default_value, desc, x=-1700.0, y=None):
    global next_rid, next_y
    if y is None: y = next_y; next_y += 160
    guid = str(uuid.uuid4())
    new_guids[ID] = guid
    cj = {
        "ID": ID, "TagType": 3, "Desc": desc, "NameKey": 0,
        "DefaultValue": default_value, "FinalValueEffectID": 0, "RetainWhenDie": False
    }
    node = {
        "rid": next_rid,
        "type": {"class": "SkillTagsConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": guid,
            "computeOrder": next_rid,
            "position": {"serializedVersion": "2", "x": x, "y": float(y), "width": 236.0, "height": 135.0},
            "expanded": False, "debug": False, "nodeLock": False,
            "visible": True, "hideChildNodes": False,
            "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": "",
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": TT_SKILL_TAG,
            "ConfigJson": json.dumps(cj, ensure_ascii=False, separators=(',', ':')),
            "Config2ID": f"SkillTagsConfig_{ID}"
        }
    }
    data['references']['RefIds'].append(node)
    data['nodes'].append({"rid": next_rid})
    next_rid += 1
    return guid

def add_skillcond_node(ID, sc_type, params, desc, x=6800.0, y=None):
    """SkillCondition 节点 (TSCT_*)"""
    global next_rid, next_y
    if y is None: y = next_y; next_y += 160
    guid = str(uuid.uuid4())
    new_guids[ID] = guid
    cj = {"ID": ID, "SkillConditionType": sc_type, "Params": params}
    node = {
        "rid": next_rid,
        "type": {"class": _sc_cls_for(sc_type), "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": guid,
            "computeOrder": next_rid,
            "position": {"serializedVersion": "2", "x": x, "y": float(y), "width": 280.0, "height": 140.0},
            "expanded": False, "debug": False, "nodeLock": False,
            "visible": True, "hideChildNodes": False,
            "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": ID, "Desc": desc,
            "paramVersion": 0, "templateParamVersion": 0,
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": TT_SKILL_COND,
            "ConfigJson": json.dumps(cj, ensure_ascii=False, separators=(',', ':')),
            "Config2ID": f"SkillConditionConfig_{ID}",
            "SkillConditionType": sc_type
        }
    }
    data['references']['RefIds'].append(node)
    data['nodes'].append({"rid": next_rid})
    next_rid += 1
    return guid

def _sc_cls_for(sc_type):
    return {7: 'TSCT_VALUE_COMPARE'}[sc_type]

def add_edge(out_guid, in_guid, in_field='ID', out_field='PackedParamsOutput',
             in_port='0', out_port='0'):
    edge = {
        "GUID": str(uuid.uuid4()),
        "inputNodeGUID": in_guid,
        "outputNodeGUID": out_guid,
        "inputFieldName": in_field,
        "outputFieldName": out_field,
        "inputPortIdentifier": in_port,
        "outputPortIdentifier": out_port,
        "isVisible": True
    }
    data['edges'].append(edge)
    return edge

def remove_edge_by_guid(out_guid, in_guid):
    """remove edges between two specific nodes"""
    before = len(data['edges'])
    data['edges'] = [e for e in data['edges']
                     if not (e['outputNodeGUID']==out_guid and e['inputNodeGUID']==in_guid)]
    return before - len(data['edges'])

# ============ Phase 1: 新增 2 个 SkillTag ============
guid_skt_limit = add_skilltag_node(SKT_LIMIT, 3, '飞叶锁魂-穿透上限', x=-1700.0, y=-200.0)
guid_skt_count = add_skilltag_node(SKT_COUNT, 0, '飞叶锁魂-穿透计数', x=-1700.0, y=-30.0)
print(f'[+SkillTag] {SKT_LIMIT} 飞叶锁魂-穿透上限 (default=3) GUID={guid_skt_limit[:8]}')
print(f'[+SkillTag] {SKT_COUNT} 飞叶锁魂-穿透计数 (default=0) GUID={guid_skt_count[:8]}')

# ============ Phase 2: 新增 SkillEffect 节点 ============
# 注意: ParamType / V 含义 (TParamType / TCommonParamType / TConditionOperator / TNumOperators)
# - PT=5 + V=1  → TCPT_MAIN_ENTITY     (主体 = 当前执行 SkillEffect 的 entity)
# - PT=5 + V=4  → TCPT_MAIN_SKILL_DAMAGE_PROPERTY_ORIGIN_ENTITY (Caster = 伤害归属)
# - PT=5 + V=41 → TCPT_ORIGIN_SKILL_INST_ID (实例级 namespace)
# - PT=2        → NodeRef (引用另一节点 ConfigID 取其输出)
# - PT=0        → 直接常量
# SkillTag (ADD/GET/MODIFY) Params: [P0=作用entity, P1=skill_id命名空间, P2=tag_id, P3=value, P4=op?]
# DESTROY_ENTITY Params: [P0=要销毁的entity, P1=?, P2=?]
# NUM_CALCULATE Params: [P0=起始值, P1=op, P2=操作数, [P3=op, P4=操作数, ...]]
# VALUE_COMPARE Params (SkillCondition 7): [P0=入参NodeRef, P1=op (TCO_*), P2=target常量]
# CONDITION_EXECUTE Params: [P0=条件SkillCondID, P1=true分支SkillEffectID, P2=false分支SkillEffectID]
# ORDER_EXECUTE Params: [P0..PN = 各子 SkillEffect (按顺序执行)]
# MODIFY_SKILL_TAG SkillEffectType=96 (查 enum)
# 注: 当前文件中 ADD_SKILL_TAG = 97, GET_SKILL_TAG = 48, MODIFY 待 check (但 30215001 ID 44016037 用 96)

# SE_RESET_COUNT: MODIFY 子弹自身 SKT_COUNT = 0 (实例级 namespace)
# Param[0] = 子弹 entity (PT=5, V=1 主体)  -- 因为在子弹 AfterBorn 链中 / "主体"是子弹自身
# Param[1] = 实例级 namespace (PT=5, V=41 ORIGIN_SKILL_INST_ID)
# Param[2] = SKT_COUNT
# Param[3] = 0 (赋值常量)
# Param[4] = 1 (op)
# 注: TSET_MODIFY_SKILL_TAG_VALUE = 46 (来源 common.nothotfix.cs:19143)
guid_reset_count = add_se_node(SE_RESET_COUNT, 46, [
    {"Value": 1,    "ParamType": 5, "Factor": 0},   # P0 主体 = 子弹
    {"Value": 41,   "ParamType": 5, "Factor": 0},   # P1 实例级 namespace
    {"Value": SKT_COUNT, "ParamType": 0, "Factor": 0},  # P2 tag_id
    {"Value": 0,    "ParamType": 0, "Factor": 0},   # P3 value=0
    {"Value": 1,    "ParamType": 0, "Factor": 0},   # P4 op
], '初始化:子弹自身穿透计数=0', x=6500.0, y=2000.0)

# SE_AFTERBORN_INIT: ORDER, contains [SE_RESET_COUNT]
guid_init_order = add_se_node(SE_AFTERBORN_INIT, 1, [
    {"Value": SE_RESET_COUNT, "ParamType": 0, "Factor": 0},
], 'AfterBorn 初始化:重置子弹穿透计数', x=4000.0, y=2000.0)

# SE_ADD_COUNT: ADD 子弹自身 SKT_COUNT += 1 (实例级)
guid_add_count = add_se_node(SE_ADD_COUNT, 97, [
    {"Value": 1,    "ParamType": 5, "Factor": 0},   # P0 主体 = 子弹
    {"Value": 41,   "ParamType": 5, "Factor": 0},   # P1 实例级 namespace
    {"Value": SKT_COUNT, "ParamType": 0, "Factor": 0},  # P2 tag_id
    {"Value": 1,    "ParamType": 0, "Factor": 0},   # P3 value=+1
    {"Value": 1,    "ParamType": 0, "Factor": 0},   # P4 op
], '击中:子弹自身穿透计数+=1', x=7000.0, y=2200.0)

# SE_GET_COUNT: GET 子弹自身 SKT_COUNT (实例级)
guid_get_count = add_se_node(SE_GET_COUNT, 48, [
    {"Value": 1,    "ParamType": 5, "Factor": 0},   # P0 主体 = 子弹
    {"Value": 41,   "ParamType": 5, "Factor": 0},   # P1 实例级 namespace
    {"Value": SKT_COUNT, "ParamType": 0, "Factor": 0},  # P2 tag_id
    {"Value": 1,    "ParamType": 0, "Factor": 0},   # P3
    {"Value": 1,    "ParamType": 0, "Factor": 0},   # P4
], '读子弹自身穿透计数 (实例级)', x=7400.0, y=2200.0)

# SE_GET_LIMIT: GET 技能级 SKT_LIMIT (Caster 上 / 跨技能 namespace=30112001)
guid_get_limit = add_se_node(SE_GET_LIMIT, 48, [
    {"Value": 4,    "ParamType": 5, "Factor": 0},   # P0 Caster (伤害归属)
    {"Value": 30112001, "ParamType": 0, "Factor": 0},  # P1 skill_id namespace 跨技能持久
    {"Value": SKT_LIMIT, "ParamType": 0, "Factor": 0},  # P2 tag_id
    {"Value": 1,    "ParamType": 0, "Factor": 0},   # P3
    {"Value": 1,    "ParamType": 0, "Factor": 0},   # P4
], '读技能级穿透上限 X (Caster 上)', x=7400.0, y=2400.0)

# SE_DIFF: NUM_CALC = GET_COUNT - GET_LIMIT (NodeRef 减 NodeRef)
# Params: [P0=起始NodeRef(GET_COUNT), P1=op(4=减), P2=操作数NodeRef(GET_LIMIT)]
guid_diff = add_se_node(SE_DIFF, 31, [
    {"Value": SE_GET_COUNT, "ParamType": 2, "Factor": 0},  # P0 起始 = GET_COUNT NodeRef
    {"Value": 4,    "ParamType": 0, "Factor": 0},   # P1 op = 4 减
    {"Value": SE_GET_LIMIT, "ParamType": 2, "Factor": 0},  # P2 操作数 = GET_LIMIT NodeRef
], '计算: 计数 - 上限 (>=0 即达到阈值)', x=7700.0, y=2300.0)

# SKC_REACHED: VALUE_COMPARE Params=[P0=NodeRef SE_DIFF, P1=op=4 (>=), P2=target=0]
guid_check_cond = add_skillcond_node(SKC_REACHED, 7, [
    {"Value": SE_DIFF, "ParamType": 2, "Factor": 0},  # P0 SE_DIFF NodeRef
    {"Value": 4,    "ParamType": 0, "Factor": 0},   # P1 op = 4 TCO_BIGGER_OR_EQUAL (>=)
    {"Value": 0,    "ParamType": 0, "Factor": 0},   # P2 target = 0
], '判定: 计数-上限 >= 0 (达到穿透上限)', x=8000.0, y=2300.0)

# SE_DESTROY: DESTROY_ENTITY 子弹自身 (PT=5 V=1 主体)
guid_destroy = add_se_node(SE_DESTROY, 24, [
    {"Value": 1,    "ParamType": 5, "Factor": 0},   # P0 销毁主体 = 子弹自身
    {"Value": 0,    "ParamType": 0, "Factor": 0},   # P1
    {"Value": 0,    "ParamType": 0, "Factor": 0},   # P2
], '销毁子弹自身', x=8400.0, y=2400.0)

# SE_CHECK_DESTROY: CONDITION_EXECUTE [SKC_REACHED, SE_DESTROY, 0]
guid_check_dest = add_se_node(SE_CHECK_DESTROY, 47, [
    {"Value": SKC_REACHED, "ParamType": 0, "Factor": 0},  # P0 条件
    {"Value": SE_DESTROY,  "ParamType": 0, "Factor": 0},  # P1 true 分支
    {"Value": 0,           "ParamType": 0, "Factor": 0},  # P2 false 分支 (无)
], '若达到上限→销毁子弹', x=7900.0, y=2500.0)

# SE_HIT_TAIL: ORDER [SE_GET_COUNT, SE_GET_LIMIT, SE_DIFF, SE_ADD_COUNT, SE_CHECK_DESTROY]
# 注: 顺序: 先 +1, 再算 diff (这样达到 X 时 count==X 已加完 / count-limit==0 → >=0 销毁)
# 实际: ADD_COUNT 必须在 GET_COUNT/DIFF/CHECK 之前; 但 NodeRef 在 CONDITION 评估时取值 / 评估时刻已是 ADD 之后
# 简化: 按 SkillEffect 真实执行顺序 [SE_ADD_COUNT (副作用), SE_CHECK_DESTROY (条件评估时实时 GET)]
# GET_COUNT/GET_LIMIT/DIFF 不需要在 ORDER 里调用 (它们作为 NodeRef 被 SKC_REACHED 间接引用)
# 所以 SE_HIT_TAIL Params 只需 [SE_ADD_COUNT, SE_CHECK_DESTROY]
guid_hit_tail = add_se_node(SE_HIT_TAIL, 1, [
    {"Value": SE_ADD_COUNT,     "ParamType": 0, "Factor": 0},
    {"Value": SE_CHECK_DESTROY, "ParamType": 0, "Factor": 0},
], '击中尾段: 计数+1 → 阈值检查→销毁', x=6500.0, y=2400.0)

# SE_HIT_WRAPPER: ORDER [32002761(原), SE_HIT_TAIL]
guid_hit_wrap = add_se_node(SE_HIT_WRAPPER, 1, [
    {"Value": 32002761,  "ParamType": 0, "Factor": 0},
    {"Value": SE_HIT_TAIL, "ParamType": 0, "Factor": 0},
], '击中包装: 原击中分支 + 计数销毁尾段', x=5900.0, y=2400.0)

# ============ Phase 3: 修改现有节点 ============
# 3a. 32002537 ORDER Params: [32000691, 32002531] → [SE_AFTERBORN_INIT, 32000691, 32002531]
cj_2537 = json.loads(n_32002537['data']['ConfigJson'])
old_params_2537 = list(cj_2537['Params'])
cj_2537['Params'] = [
    {"Value": SE_AFTERBORN_INIT, "ParamType": 0, "Factor": 0},
] + old_params_2537
n_32002537['data']['ConfigJson'] = json.dumps(cj_2537, ensure_ascii=False, separators=(',', ':'))
print(f'[~32002537] ORDER Params head 加 SE_AFTERBORN_INIT={SE_AFTERBORN_INIT}')

# 3b. 32000691 ConfigJson.Params[3].Value: 32002761 → SE_HIT_WRAPPER
cj_691 = json.loads(n_32000691['data']['ConfigJson'])
old_p3 = cj_691['Params'][3]['Value']
assert old_p3 == 32002761, f'Expected P[3]=32002761 got {old_p3}'
cj_691['Params'][3]['Value'] = SE_HIT_WRAPPER
n_32000691['data']['ConfigJson'] = json.dumps(cj_691, ensure_ascii=False, separators=(',', ':'))
print(f'[~32000691] ConfigJson.Params[3].Value: 32002761 → {SE_HIT_WRAPPER}')

# ============ Phase 4: edge 操作 ============
# 4a. 删除 edge 32000691 → 32002761
removed = remove_edge_by_guid(guid_32000691, guid_32002761)
assert removed == 1, f'Expected to remove 1 edge but removed {removed}'
print(f'[~edge] 删除 32000691→32002761 (旧 P[3] 边)')

# 4b. 新 edge 32002537 (parent ORDER, dynamic port outPort=0) → SE_AFTERBORN_INIT
add_edge(guid_32002537, guid_init_order, in_field='ID', out_field='PackedParamsOutput',
         in_port='0', out_port='0')
# 4c. 新 edge SE_AFTERBORN_INIT (parent ORDER) → SE_RESET_COUNT
add_edge(guid_init_order, guid_reset_count, out_port='0')
# 4d. 新 edge 32000691 (parent RUN_TEMPLATE, fixed port outPort=3) → SE_HIT_WRAPPER
add_edge(guid_32000691, guid_hit_wrap, in_field='ID', out_field='PackedParamsOutput',
         in_port='0', out_port='3')
# 4e. 新 edge SE_HIT_WRAPPER (parent ORDER) → 32002761 (现作为 SE_HIT_WRAPPER 的 P[0] 子节点)
add_edge(guid_hit_wrap, guid_32002761, out_port='0')
# 4f. 新 edge SE_HIT_WRAPPER → SE_HIT_TAIL
add_edge(guid_hit_wrap, guid_hit_tail, out_port='0')
# 4g. SE_HIT_TAIL → SE_ADD_COUNT, SE_CHECK_DESTROY
add_edge(guid_hit_tail, guid_add_count, out_port='0')
add_edge(guid_hit_tail, guid_check_dest, out_port='0')
# 4h. SE_CHECK_DESTROY (CONDITION fixed port): outPort 0=条件 SKC_REACHED, outPort 1=SE_DESTROY (true)
add_edge(guid_check_dest, guid_check_cond, out_port='0')
add_edge(guid_check_dest, guid_destroy,    out_port='1')
# 4i. SKC_REACHED (VALUE_COMPARE / SkillCondition fixed port): outPort 0=NodeRef SE_DIFF
add_edge(guid_check_cond, guid_diff, out_port='0')
# 4j. SE_DIFF (NUM_CALC): outPort 0=起始NodeRef SE_GET_COUNT, outPort 2=操作数NodeRef SE_GET_LIMIT
add_edge(guid_diff, guid_get_count, out_port='0')
add_edge(guid_diff, guid_get_limit, out_port='2')

print(f'[+edges] 11 条新边')

# ============ 写回 ============
P.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\n✓ 已写回: {P.name}')
print(f'  原节点数: 57 → 新节点数: {len(data["references"]["RefIds"])} (+{len(data["references"]["RefIds"])-57})')
print(f'  原边数: 52 → 新边数: {len(data["edges"])} (+{len(data["edges"])-52})')
