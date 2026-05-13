#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
patch_30212009_anchor_bullet.py

加锚点空子弹，把"发射位置"锁定在 cast 瞬间 caster 的位置。

设计：
  1. 新建 BulletConfig 320149 锚点空子弹 (Speed=0, Model=0, LastTime=60)
     - AfterBornSkillEffectExecuteInfo.SkillEffectConfigID = 32002513 (已有 DELAY 20 帧)
  2. 新建 CREATE_BULLET 32200005，在 entry ORDER [6] 位置 (cast 瞬间) 创建 320149
  3. 修改 entry ORDER 32001684 Params[6]: V=32002513 -> V=32200005
     - 这样 cast 瞬间立刻生成 anchor bullet（位置=caster 当前位置）
     - anchor 的 AfterBorn 链接 DELAY 20 → ORDER 32003421 → CONDITION → RUN_TEMPLATE
     - RUN_TEMPLATE 在 anchor 的 AfterBorn 上下文中，主体=anchor bullet（位置=cast 时刻位置）
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC = PROJECT_ROOT / "<<SKILLGRAPH_JSONS_ROOT>>宗门技能/SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json"

NEW_BULLET_ID = 320149      # 锚点 BulletConfig
NEW_CREATE_EID = 32200005   # CREATE_BULLET 锚点
EXISTING_DELAY_EID = 32002513  # 已有 DELAY 20 帧（保留，作为 anchor.AfterBorn 目标）
ENTRY_ORDER_ID = 32001684

SET_CREATE_BULLET = 8  # TSET_CREATE_BULLET 的 SkillEffectType（已经核对 enum，30212009 现有 32002522 也是 8）


def make_param(value, pt=0, factor=0):
    return {"Value": value, "ParamType": pt, "Factor": factor}


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    d = json.loads(SRC.read_text(encoding="utf-8"))
    refs = d["references"]["RefIds"]

    # ========== 1. 新建 BulletConfigNode 320149 锚点空子弹 ==========
    # 复用现有 BulletConfig 的字段集合作为基础（参考 320147 指示器子弹）
    # 关键修改：Speed=0 / Model=0 / AfterBorn → 32002513
    base_bullet_config = {
        "ID": NEW_BULLET_ID,
        "Name": "千叶散华锚点空子弹",
        "Desc": "记录 cast 瞬间位置的空子弹（不可见、静止），子弹发射上下文挂在它的 AfterBorn",
        "Model": 0,                     # 不可见
        "Speed": 0,                      # 静止
        "MaxDistance": 0,
        "LastTime": 60,                  # 60 帧 (~2 秒) 够用
        "AccelerSpeed": 0,
        "RotSpeed": 0,
        "TraceTargetType": 0,
        "AngleAdjustType": 0,
        "ShakeOffsetSpeed": 0,
        "ShakeOffsetMaxRange": 0,
        "FlyType": 0,
        "FlyRotSpeed": 0,
        "TracePathType": 0,
        "TracePathParams": [],
        "MoveStateMaxNum": 0,
        "RebornCount": 0,
        "BeforeBornSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "AfterBornSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": EXISTING_DELAY_EID},
        "DieSkillEffectExecuteInfo": {"SelectConfigID": 0, "SkillEffectConfigID": 0},
        "LifeFlag": 1,
        "BulletEffectModelExtraInfo": {},
        "ResetSkillTagsList": [],
        "SkillTagsList": [],
    }
    new_bullet_node = {
        "rid": 0,
        "type": {"class": "BulletConfigNode", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": 5500.0, "y": 1500.0,
                         "width": 320.0, "height": 280.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": NEW_BULLET_ID,
            "Desc": "千叶散华锚点空子弹（不可见、静止，捕捉 cast 瞬间位置）",
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps(base_bullet_config, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"BulletConfig_{NEW_BULLET_ID}",
        },
    }
    refs.append(new_bullet_node)
    print(f"新增 BulletConfigNode {NEW_BULLET_ID} 锚点空子弹 (AfterBorn → {EXISTING_DELAY_EID})")

    # ========== 2. 新建 CREATE_BULLET 32200005 ==========
    # 参考现有 32002522 (创建指示器子弹) 的 Params 结构
    create_bullet_cj = {
        "ID": NEW_CREATE_EID,
        "SkillEffectType": SET_CREATE_BULLET,
        "Params": [
            make_param(NEW_BULLET_ID, pt=0),       # [0] BulletConfig = 320149
            make_param(91, pt=1),                  # [1] 面向 = caster.face_dir
            make_param(59, pt=1),                  # [2] 位置X = caster.位置X
            make_param(60, pt=1),                  # [3] 位置Y = caster.位置Y
            make_param(1, pt=5),                   # [4] 主体 = caster
            make_param(0, pt=0),                   # [5]
            make_param(0, pt=0),                   # [6] 向前偏移 = 0
            make_param(0, pt=0),                   # [7]
            make_param(101, pt=0),                 # [8] 单位组 = 101
            make_param(0, pt=0),                   # [9]
            make_param(41, pt=5),                  # [10] 初始技能实例
            make_param(0, pt=0),                   # [11]
            make_param(0, pt=0),                   # [12] CREATE 完成 callback = 无
            make_param(0, pt=0),                   # [13]
            make_param(1, pt=0),                   # [14] 急速影响 = 1
        ],
    }
    new_create_node = {
        "rid": 0,
        "type": {"class": "TSET_CREATE_BULLET", "ns": "NodeEditor", "asm": "NodeEditor"},
        "data": {
            "GUID": str(uuid.uuid4()),
            "computeOrder": 0,
            "position": {"serializedVersion": "2", "x": 5500.0, "y": 1100.0,
                         "width": 320.0, "height": 250.0},
            "expanded": False, "debug": False, "nodeLock": False, "visible": True,
            "hideChildNodes": False, "hidePos": {"x": 0.0, "y": 0.0}, "hideCounter": 0,
            "ID": NEW_CREATE_EID,
            "Desc": "cast 瞬间创建锚点空子弹（捕捉发射点位置，不会跟随主角后撤）",
            "IsTemplate": False, "TemplateFlags": 0,
            "TemplateParams": [], "TemplateParamsDesc": [], "TemplateParamsCustomAdd": False,
            "TableTash": "0CFA05568A66FEA1DF3BA6FE40DB7080",
            "ConfigJson": json.dumps(create_bullet_cj, ensure_ascii=False, separators=(",", ":")),
            "Config2ID": f"SkillEffectConfig_{NEW_CREATE_EID}",
            "SkillEffectType": SET_CREATE_BULLET,
        },
    }
    refs.append(new_create_node)
    print(f"新增 CREATE_BULLET {NEW_CREATE_EID}（位置=caster.attr:位置X/Y, 子弹={NEW_BULLET_ID}）")

    # ========== 3. 修改 entry ORDER Params[6] ==========
    for r in refs:
        cj_str = r["data"].get("ConfigJson", "")
        if not cj_str:
            continue
        try:
            cjr = json.loads(cj_str)
        except Exception:
            continue
        if cjr.get("ID") == ENTRY_ORDER_ID:
            old = cjr["Params"][6].get("Value")
            cjr["Params"][6] = make_param(NEW_CREATE_EID, pt=0)
            r["data"]["ConfigJson"] = json.dumps(cjr, ensure_ascii=False, separators=(",", ":"))
            print(f"修改 entry ORDER {ENTRY_ORDER_ID} Params[6]: V={old} -> V={NEW_CREATE_EID}")
            break

    # ========== 4. 重排 rid ==========
    for i, r in enumerate(refs):
        r["rid"] = 1000 + i
        r["data"]["computeOrder"] = i
    d["nodes"] = [{"rid": 1000 + i} for i in range(len(refs))]

    # ========== 5. 重新 derive edges ==========
    sys.path.insert(0, str(Path(__file__).parent))
    from rewrite_30212009_v2 import derive_edges
    d["edges"] = derive_edges(refs)
    print(f"新边数: {len(d['edges'])}")

    SRC.write_text(json.dumps(d, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"\n✓ 写入 {SRC.relative_to(PROJECT_ROOT)}")
    print(f"  最终节点: {len(refs)}")


if __name__ == "__main__":
    main()
