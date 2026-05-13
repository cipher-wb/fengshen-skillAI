"""
patch_30212017_mvp1_fix_repeat_and_modify.py
============================================

修 MVP1 30212017 两个 OnTick bug（用户实测：子弹生成 + 销毁 OK / 不动）：

Bug 1: REPEAT 302120174 P[0] 写成了 NodeRef ({V=302120175, PT=2})
       → 应是 interval 整数 ({V=1, PT=0})；body 的 NodeRef 在 P[3]
       证据：grep 30212010 真实 work 样本 32002810
             ConfigJson Params=[{V=1,PT=0}, {V=-1,PT=0}, {V=0,PT=0},
                                 {V=32002821,PT=0 body}, ...]

Bug 2: 用 ADD_ENTITY_ATTR_VALUE Type=71 改 PosX，30212010 全样本 0 实证
       → 改用 30212010 真实 work 模式：
         GET (Type=32) → NUM_CALC (Type=31) → MODIFY (Type=12)
         MODIFY P[2] 必须 PT=2 NodeRef 指向 NUM_CALC 节点
       证据：
         - 30212010 66001753 MODIFY P=[{V=1,PT=5}, {V=59,PT=0}, {V=66001754,PT=2}]
         - 30212002 32000654 GET   P=[{V=6,PT=5}, {V=91,PT=0}]
         - 30212010 32002241 NUM_CALC P=[{V=NodeRef,PT=2}, {V=4,PT=0}, {V=20,PT=0}]
         - 30212002 32000651 NUM_CALC P=[{V=NodeRef,PT=2}, {V=3,PT=0}, {V=NodeRef,PT=2}]
         - TableDR.TNumOperators: TNO_ADD = 3

策略：原地修补 references.RefIds 数组：
  - 修 1004 (REPEAT 302120174) ConfigJson
  - 修 1003 (ORDER body 302120175) ConfigJson 加 GET/CALC/MODIFY 三个 ID
  - 改 1002 类型 ADD_ENTITY_ATTR_VALUE → GET_ENTITY_ATTR_VALUE  (302120176 = GET)
  - 新增两个 RefIds (rid=1008/1009)：NUM_CALC 302120177 / MODIFY 302120178
  - 不动 nodes 列表 / edges (UI 边可不补 / 编辑器读 references 即可)
  - 不动 BulletConfig / CREATE_BULLET / 顶层 SkillConfig

不写 .meta。

(AI 新增/修改)
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
TARGET = os.path.join(
    ROOT,
    "Assets", "Thirds", "NodeEditor", "SkillEditor", "Saves", "Jsons",
    "宗门技能", "木宗门技能",
    "SkillGraph_30212017【MVP1】单弹直线右移.json",
)


def make_param(v: int, pt: int = 0, factor: int = 0):
    return {"Value": v, "ParamType": pt, "Factor": factor}


def cfg_json(d: dict) -> str:
    # 与原文件一致：紧凑 / 不空格 / 不转义中文
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False)


def find_ref(refs, rid):
    for r in refs:
        if r["rid"] == rid:
            return r
    return None


def main():
    print(f"[load] {TARGET}")
    with open(TARGET, "r", encoding="utf-8") as f:
        graph = json.load(f)

    refs = graph["references"]["RefIds"]

    # ---------- Bug 1 fix: rid=1004 REPEAT 302120174 ----------
    rep = find_ref(refs, 1004)
    assert rep is not None and rep["data"]["ID"] == 302120174
    new_repeat_cfg = {
        "ID": 302120174,
        "SkillEffectType": 3,  # TSET_REPEAT_EXECUTE
        "Params": [
            make_param(1, 0),            # P[0] interval = 1 frame  ⭐ Bug 1 修
            make_param(60, 0),           # P[1] count = 60
            make_param(0, 0),             # P[2]
            make_param(302120175, 0),    # P[3] body = ORDER 302120175 (PT=0!)
            make_param(0, 0),
            make_param(0, 0),
            make_param(0, 0),
            make_param(0, 0),
            make_param(0, 0),
            make_param(0, 0),
        ],
    }
    rep["data"]["ConfigJson"] = cfg_json(new_repeat_cfg)
    rep["data"]["Desc"] = (
        "[OnTick REPEAT] interval=1 / count=60\n"
        "P[0]=1 PT=0 interval / P[1]=60 PT=0 count / P[3]=302120175 PT=0 body\n"
        "✓ v2 修：原 P[0] 错写 NodeRef PT=2"
    )

    # ---------- Bug 2 fix Part A: rid=1003 ORDER body 302120175 ----------
    order = find_ref(refs, 1003)
    assert order is not None and order["data"]["ID"] == 302120175
    new_order_cfg = {
        "ID": 302120175,
        "SkillEffectType": 1,  # TSET_ORDER_EXECUTE
        "Params": [
            make_param(302120176, 0),  # GET
            make_param(302120177, 0),  # NUM_CALC
            make_param(302120178, 0),  # MODIFY
        ],
    }
    order["data"]["ConfigJson"] = cfg_json(new_order_cfg)
    order["data"]["Desc"] = (
        "[每帧 ORDER body] 顺序：\n"
        "  GET 302120176 (取子弹自身 PosX)\n"
        "  → NUM_CALC 302120177 (PosX + 5)\n"
        "  → MODIFY 302120178 (写回子弹自身 PosX)"
    )

    # ---------- Bug 2 fix Part B: rid=1002 改成 GET (302120176) ----------
    get_node = find_ref(refs, 1002)
    assert get_node is not None and get_node["data"]["ID"] == 302120176
    get_node["type"]["class"] = "TSET_GET_ENTITY_ATTR_VALUE"
    get_get_cfg = {
        "ID": 302120176,
        "SkillEffectType": 32,  # TSET_GET_ENTITY_ATTR_VALUE
        "Params": [
            make_param(1, 5),    # P[0] 单位 = caster (在子弹 OnTick = 子弹自身)
            make_param(59, 0),    # P[1] 属性 = TBN_POS_X (59)
        ],
    }
    get_node["data"]["ConfigJson"] = cfg_json(get_get_cfg)
    get_node["data"]["SkillEffectType"] = 32
    get_node["data"]["Desc"] = (
        "[每帧 step1] 取子弹自身 PosX\n"
        "P[0]=1 PT=5 (caster in bullet ctx = 子弹自身)\n"
        "P[1]=59 PT=0 (TBN_POS_X 位置X)"
    )

    # ---------- Bug 2 fix Part C: 新增 rid=1008 NUM_CALC (302120177) ----------
    num_calc_cfg = {
        "ID": 302120177,
        "SkillEffectType": 31,  # TSET_NUM_CALCULATE
        "Params": [
            make_param(302120176, 2),  # P[0] NodeRef → GET 输出
            make_param(3, 0),           # P[1] 运算符 = TNO_ADD (3)
            make_param(5, 0),           # P[2] 常数 = 5
        ],
    }
    num_calc_node = {
        "rid": 1008,
        "type": {
            "class": "TSET_NUM_CALCULATE",
            "ns": "NodeEditor",
            "asm": "NodeEditor",
        },
        "data": {
            "GUID": "f8b40c20-1024-4d20-a5b0-30212017aaaa",
            "computeOrder": 8,
            "position": {
                "serializedVersion": "2",
                "x": 2400.0,
                "y": 800.0,
                "width": 320.0,
                "height": 200.0,
            },
            "expanded": False,
            "debug": False,
            "nodeLock": False,
            "visible": True,
            "hideChildNodes": False,
            "hidePos": {"x": 0.0, "y": 0.0},
            "hideCounter": 0,
            "ID": 302120177,
            "Desc": (
                "[每帧 step2] newPosX = currentPosX + 5\n"
                "P[0]={V=302120176,PT=2} NodeRef → GET 结果\n"
                "P[1]={V=3,PT=0} TNumOperators.TNO_ADD\n"
                "P[2]={V=5,PT=0} delta = 5"
            ),
            "paramVersion": 0,
            "templateParamVersion": 0,
            "IsTemplate": False,
            "TemplateFlags": 0,
            "TemplateParams": [],
            "TemplateParamsDesc": [],
            "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": cfg_json(num_calc_cfg),
            "Config2ID": "SkillEffectConfig_302120177",
            "SkillEffectType": 31,
        },
    }
    refs.append(num_calc_node)

    # ---------- Bug 2 fix Part D: 新增 rid=1009 MODIFY (302120178) ----------
    modify_cfg = {
        "ID": 302120178,
        "SkillEffectType": 12,  # TSET_MODIFY_ENTITY_ATTR_VALUE
        "Params": [
            make_param(1, 5),           # P[0] 单位 = 子弹自身
            make_param(59, 0),           # P[1] 属性 = PosX
            make_param(302120177, 2),   # P[2] NodeRef → NUM_CALC 结果
        ],
    }
    modify_node = {
        "rid": 1009,
        "type": {
            "class": "TSET_MODIFY_ENTITY_ATTR_VALUE",
            "ns": "NodeEditor",
            "asm": "NodeEditor",
        },
        "data": {
            "GUID": "f8b40c20-1024-4d20-a5b0-30212017bbbb",
            "computeOrder": 9,
            "position": {
                "serializedVersion": "2",
                "x": 2800.0,
                "y": 600.0,
                "width": 320.0,
                "height": 200.0,
            },
            "expanded": False,
            "debug": False,
            "nodeLock": False,
            "visible": True,
            "hideChildNodes": False,
            "hidePos": {"x": 0.0, "y": 0.0},
            "hideCounter": 0,
            "ID": 302120178,
            "Desc": (
                "[每帧 step3] 写回子弹自身 PosX = NUM_CALC 结果\n"
                "P[0]={V=1,PT=5} 子弹自身\n"
                "P[1]={V=59,PT=0} PosX\n"
                "P[2]={V=302120177,PT=2} NodeRef → NUM_CALC"
            ),
            "paramVersion": 0,
            "templateParamVersion": 0,
            "IsTemplate": False,
            "TemplateFlags": 0,
            "TemplateParams": [],
            "TemplateParamsDesc": [],
            "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": cfg_json(modify_cfg),
            "Config2ID": "SkillEffectConfig_302120178",
            "SkillEffectType": 12,
        },
    }
    refs.append(modify_node)

    # ---------- 同步 nodes 列表 ----------
    graph["nodes"].append({"rid": 1008})
    graph["nodes"].append({"rid": 1009})

    # ---------- 写出 ----------
    with open(TARGET, "w", encoding="utf-8") as f:
        # 与原文件一致：4 空格缩进 / 不转义中文
        json.dump(graph, f, ensure_ascii=False, indent=4)
    print(f"[save] {TARGET}")
    print(f"[ok] now {len(refs)} RefIds total, {len(graph['nodes'])} nodes")


if __name__ == "__main__":
    main()
