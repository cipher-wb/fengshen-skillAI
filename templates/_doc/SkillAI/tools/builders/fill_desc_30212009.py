#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fill_desc_30212009.py — 给所有节点加合适的 Desc

只覆盖空 Desc，保留人工已写的内容。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC = PROJECT_ROOT / "<<SKILLGRAPH_JSONS_ROOT>>宗门技能/SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json"

# (cls, ID) → 描述
DESC_MAP = {
    # === 入口 / 主流程 ===
    ("TSET_ORDER_EXECUTE", 32001684): "技能主流程入口（顺序执行 7 个分支：动作/法阵/发射爆发/位移/音效/指示器子弹/主发射）",

    # === 前摇动作 ===
    ("TSET_PLAY_ROLE_ANIM", 32002914): "起手动作 anim=636（双脚轻微离地，空中转一圈，双手向前发射）",

    # === 法阵特效（步骤 [1]）===
    ("ModelConfigNode", 3200280): "法阵施法特效模型",

    # === 发射瞬间（步骤 [2]：DELAY 20帧 → ORDER → CREATE_EFFECT + CAMERA_SHAKE）===
    ("TSET_DELAY_EXECUTE", 32002560): "延迟 20 帧后触发发射瞬间表现（爆发特效 + 镜头抖）",
    ("TSET_ORDER_EXECUTE", 32002562): "发射瞬间表现 ORDER（爆发特效 + 镜头抖）",
    ("TSET_CAMERA_SHAKE", 32002563): "发射瞬间镜头抖动（强度 11 / 半径 800）",
    ("TSET_GET_FIXTURE_CENTER_Z", 32002561): "获取施法点 Z 坐标（用于发射爆发特效高度）",
    ("ModelConfigNode", 3200325): "发射瞬间爆发 cast 特效模型",

    # === 位移（步骤 [3]：DELAY 6帧 → 175_0023 位移模板）===
    # 已有 Desc

    # === 音效（步骤 [4]）===
    ("TSET_PLAY_SOUND", 32002356): "发射音效（sound_id 42024）",

    # === 指示器子弹（步骤 [5]：DELAY 8帧 → CREATE_BULLET 320147）===
    ("TSET_DELAY_EXECUTE", 32002520): "延迟 8 帧后创建指示器子弹（视觉提示用）",
    ("TSET_CREATE_BULLET", 32002522): "创建指示器子弹 320147（视觉提示，纯展示无伤害）",
    ("BulletConfigNode", 320147): "指示器子弹（视觉提示用，无 AfterBorn 链）",
    ("TSET_GET_FIXTURE_CENTER_Z", 32002523): "获取指示器子弹位置 Z 坐标",
    ("ModelConfigNode", 3200290): "指示器子弹模型",
    ("SkillTagsConfigNode", 320147): "千叶散华指示器角度（default=45，被 SkillIndicatorParamTagConfigIds 引用）",

    # === 主发射流程（步骤 [6]）===
    ("TSET_DELAY_EXECUTE", 32002513): "延迟 20 帧后触发主发射流程（ORDER 32003421）",

    # === 子弹通用模板调用链 ===
    # 32003471/32003472 子弹通用-碰撞 已有 Desc（直接显示模板路径）
    # 32003469 子弹通用-伤害 已有 Desc
    # 32003468 子弹通用-表现 已有 Desc
    ("TSET_ORDER_EXECUTE", 32003470): "子弹命中执行 ORDER（伤害模板 32003469 + 表现模板 32003468）",
    ("RefConfigBaseNode", 32002761): "占位引用：子弹通用-碰撞模板的命中执行槽位（指向 ORDER 32003470）",

    # === ModelConfig 子弹特效（普通+强化的子弹特效模型）===
    # 3200384 / 3200389 已有 "子弹特效" Desc — 替换为更明确的
    ("ModelConfigNode", 3200384): "普通飞叶 320159 子弹模型",
    ("ModelConfigNode", 3200389): "强化飞叶 320160 子弹模型",
    ("ModelConfigNode", 3200382): "击中特效模型（被子弹通用-表现模板引用）",

    # === BulletConfig 占位引用 ===
    ("RefConfigBaseNode", 320159): "占位引用：BulletConfig 320159（普通飞叶）",
    ("RefConfigBaseNode", 320160): "占位引用：BulletConfig 320160（强化飞叶）",
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    d = json.loads(SRC.read_text(encoding="utf-8"))
    refs = d["references"]["RefIds"]

    overwrite_count = 0
    new_count = 0
    for r in refs:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        cj_str = r["data"].get("ConfigJson", "")
        cj = json.loads(cj_str) if cj_str else {}
        nid = cj.get("ID")
        if nid is None and cls == "RefConfigBaseNode":
            nid = r["data"].get("ManualID")
        if nid is None:
            continue
        key = (cls, nid)
        if key not in DESC_MAP:
            continue
        new_desc = DESC_MAP[key]
        old_desc = r["data"].get("Desc", "")
        if old_desc.strip():
            # 已有人工/自动 Desc，只在我们要"覆盖更明确"的几个 ModelConfig 上覆盖
            if cls == "ModelConfigNode" and old_desc == "子弹特效":
                r["data"]["Desc"] = new_desc
                overwrite_count += 1
                print(f"  覆盖 [{cls} {nid}] '{old_desc}' → '{new_desc}'")
        else:
            r["data"]["Desc"] = new_desc
            new_count += 1
            print(f"  添加 [{cls} {nid}] -> '{new_desc}'")

    print()
    print(f"✓ 新增 Desc: {new_count} 个 / 覆盖 Desc: {overwrite_count} 个")
    SRC.write_text(json.dumps(d, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"✓ 写入 {SRC.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
