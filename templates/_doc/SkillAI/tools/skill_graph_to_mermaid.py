#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SkillGraph JSON → Mermaid 蓝图转换器（LR 布局 / 中文名 / 枚举解引用）

用法：
    python skill_graph_to_mermaid.py <SkillGraph_xxx.json> [--out <output.md>] [--simple] [--td]

依赖：仅标准库（json, sys, argparse, pathlib）+ 同目录 skill_editor_enums.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).parent
ENUMS_PATH = TOOL_DIR / "skill_editor_enums.json"

# ====================================================================
# 加载枚举字典（中文名/整数值/枚举名 三向映射）
# ====================================================================
if ENUMS_PATH.exists():
    _enum_data = json.loads(ENUMS_PATH.read_text(encoding="utf-8"))
    ENUMS = _enum_data.get("enums", {})
else:
    print(f"WARNING: 找不到 {ENUMS_PATH}，中文名解引用将失效。请先跑 _extract_enums.py。", file=sys.stderr)
    ENUMS = {}


def enum_int_to_cn(enum_name: str, value) -> str:
    """整数 → 中文。找不到返回空串。"""
    if not isinstance(value, int):
        return ""
    e = ENUMS.get(enum_name)
    if not e:
        return ""
    return e["int_to_cn"].get(str(value), "")


def enum_int_to_enum(enum_name: str, value) -> str:
    """整数 → 枚举名（如 TSET_ORDER_EXECUTE）"""
    if not isinstance(value, int):
        return ""
    e = ENUMS.get(enum_name)
    if not e:
        return ""
    return e["int_to_enum"].get(str(value), "")


# ====================================================================
# 主节点中文名（写死）
# ====================================================================
MAIN_NODE_CN: dict[str, str] = {
    "SkillConfigNode": "技能配置",
    "SkillTagsConfigNode": "技能参数声明",
    "SkillSelectConfigNode": "技能筛选",
    "SkillEffectConfigNode": "技能效果",
    "SkillConditionConfigNode": "技能条件",
    "SkillInterruptConfigNode": "中断配置",
    "RefConfigBaseNode": "引用",
    "ModelConfigNode": "模型配置",
    "BulletConfigNode": "子弹配置",
    "BuffConfigNode": "Buff配置",
    "SkillEventConfigNode": "技能事件配置",
    "BattleAIConfigNode": "战斗AI配置",
    "BehaviorConfigNode": "行为配置",
    "VoiceConfigNode": "语音配置",
    "BattleCustomParamConfigNode": "常用数值参数",
    "BattleCameraShakeConfigNode": "镜头抖动配置",
}


def class_to_cn_name(cls: str, cfg: dict) -> str:
    """根据节点类名 + ConfigJson 解出中文名。"""
    if cls in MAIN_NODE_CN:
        return MAIN_NODE_CN[cls]
    if cls.startswith("TSET_"):
        et = cfg.get("SkillEffectType")
        cn = enum_int_to_cn("TSkillEffectType", et)
        return cn or "未知效果"
    if cls.startswith("TSCT_"):
        ct = cfg.get("SkillConditionType")
        cn = enum_int_to_cn("TSkillConditionType", ct)
        return cn or "未知条件"
    if cls.startswith("TSKILLSELECT_"):
        st = cfg.get("SkillSelectType")
        cn = enum_int_to_cn("TSkillSelectType", st)
        return cn or "未知筛选"
    return cls


# ====================================================================
# 节点参数标签字典（按 TSET 类名）—— 决定 Params[i] 的字段名
# ====================================================================
NODE_PARAM_LABELS: dict[str, list[str]] = {
    # 流程控制
    "TSET_ORDER_EXECUTE":            ["子效果1", "子效果2", "子效果3", "子效果4", "子效果5", "子效果6", "子效果7", "子效果8", "子效果9", "..."],
    "TSET_DELAY_EXECUTE":            ["延迟帧", "子效果", "死亡继续", "筛选ID", "中断ID", "_保留", "急速影响"],
    "TSET_REPEAT_EXECUTE":           ["间隔帧", "次数", "立即执行", "子效果", "筛选ID", "中断ID", "死亡继续", "结束效果", "战斗结束停", "急速影响"],
    "TSET_SWITCH_EXECUTE":           ["Switch值", "Default效果", "Case1值", "Case1效果", "Case2值", "Case2效果", "Case3值", "Case3效果", "Case4值", "Case4效果", "Case5值", "Case5效果", "Case6值", "Case6效果", "Case7值", "Case7效果", "Case8值", "Case8效果", "Case9值", "Case9效果", "Case10值", "Case10效果"],
    "TSET_PROBABILITY_EXECUTE":      ["成功概率(‱)", "成功效果", "失败效果"],
    "TSET_CONDITION_EXECUTE":        ["条件ID", "满足效果", "不满足效果"],
    "TSET_RUN_SKILL_EFFECT_TEMPLATE":["主体单位", "目标筛选", "模板根ID", "模板参数1", "模板参数2", "模板参数3", "模板参数4", "模板参数5", "模板参数6", "模板参数7", "模板参数8", "..."],
    "TSET_TERMINATE_TASK":           ["任务标识"],
    # 事件
    "TSET_REGISTER_SKILL_EVENT":     ["EventID", "绑定效果", "绑定技能", "筛选", "条件", "次数", "目标阵营", "消息技能", "消息子类型", "事件子类型", "子类型值"],
    "TSET_UNREGISTER_SKILL_EVENT":   ["EventID", "对应注册效果", "绑定技能", "事件子类型", "子类型值"],
    "TSET_FIRE_SKILL_EVENT":         ["发送者", "EventID", "参数1", "参数2", "参数3", "参数4", "参数5", "参数6", "参数7", "参数8", "参数9", "参数10", "参数11", "参数12"],
    # 创建
    "TSET_CREATE_BULLET":            ["BulletID", "角度", "位置X", "位置Y", "创建者", "偏移右", "偏移前", "子子弹", "单位组", "射弹类", "初始技能", "自定义模型", "Z高度", "仰角", "急速"],
    "TSET_CREATE_EFFECT":            ["模型ID", "角度", "位置X", "位置Y", "持续帧", "跟随单位", "缩放%", "延迟销毁ms", "偏移X", "速度%", "偏移Y", "单位组", "Z", "特效类型", "_", "出生后效果", "急速"],
    "TSET_SUMMON_ROLE":              ["BattleUnitID", "角度", "位置X", "位置Y", "出生前效果", "出生后效果"],
    "TSET_DESTROY_ENTITY":           ["目标", "走死亡流程"],
    # 状态/属性
    "TSET_MODIFY_ENTITY_STATE":      ["目标", "状态枚举", "目标值"],
    "TSET_ADD_ENTITY_STATE":         ["目标", "状态枚举", "增加值"],
    "TSET_MODIFY_ENTITY_ATTR_VALUE": ["目标", "属性枚举", "值"],
    "TSET_ADD_ENTITY_ATTR_VALUE":    ["目标", "属性枚举", "变化值"],
    "TSET_MODIFY_ENTITY_POS":        ["目标", "X", "Y", "朝向"],
    "TSET_FORCE_PHYSICAL":           ["目标", "外力值", "速度阻尼", "弹力", "角度", "持续ms", "起始高度", "最高高度", "落地ms"],
    # 技能参数读写
    "TSET_GET_SKILL_TAG_VALUE":      ["拥有者", "技能ID", "TagID", "参数类型", "取最终值"],
    "TSET_MODIFY_SKILL_TAG_VALUE":   ["拥有者", "技能ID", "TagID", "值", "参数类型"],
    "TSET_ADD_SKILL_TAG_VALUE":      ["拥有者", "技能ID", "TagID", "增加值", "参数类型"],
    "TSET_GET_AI_PARAM":             ["拥有者", "TagID", "取最终值"],
    "TSET_SET_AI_PARAM":             ["拥有者", "TagID", "值"],
    # Buff
    "TSET_ADD_BUFF":                 ["挂载单位", "来源单位", "BuffID", "持续帧", "间隔帧", "层数", "急速影响"],
    "TSET_REMOVE_BUFF":              ["目标", "移除方式", "ID或类型", "_", "_", "_"],
    "TSET_ADD_ALL_BUFF_LAYER_COUNT": ["目标", "操作类型", "BuffID/类型", "增加方式", "数量/百分比", "Buff来源"],
    # 伤害
    "TSET_DAMAGE_QUICK":             ["伤害值", "五行", "暴击", "禁止显示层"],
    "TSET_DAMAGE_STANDARD":          ["伤害来源", "伤害目标", "伤害值", "五行", "暴击", "禁止显示层"],
    "TSET_HEAL_QUICK":               ["治疗值", "目标", "_", "_"],
    # 视觉
    "TSET_PLAY_ROLE_ANIM":           ["单位", "动作ID", "上半身", "融合ms", "速度%", "移动打断", "急速", "仅指定可见", "帧数", "音效绑定"],
    "TSET_APPLY_ENTITY_EFFECT":      ["目标", "特效枚举", "开启?", "优先级", "覆盖?", "持续帧", "类型参数1", "类型参数2", "类型参数3"],
    "TSET_APPLY_SCREEN_EFFECT":      ["执行单位", "对谁生效", "屏幕特效枚举", "持续帧", "开关类型", "进入结算关闭", "类型参数1", "类型参数2"],
    "TSET_CAMERA_SHAKE":             ["执行单位", "对谁生效", "起效半径", "抖X", "抖Y", "ShakeID", "优先级", "插入方式"],
    "TSET_HIT_FREEZE":               ["攻者", "受者", "施法者", "时长帧", "放慢倍率"],
    "TSET_PLAY_SOUND":               ["VoiceID", "类型", "单位音效配置"],
    # 数值
    "TSET_NUM_CALCULATE":            ["初始值", "运算符1", "数值1", "运算符2", "数值2", "运算符3", "数值3", "运算符4", "数值4", "运算符5", "数值5"],
    "TSET_NUM_RANDOM":               ["min", "max"],
    "TSET_NUM_MAX":                  ["值1", "值2", "值3", "..."],
    "TSET_NUM_MIN":                  ["值1", "值2", "值3", "..."],
    # 释放/CD
    "TSET_USE_SKILL":                ["SkillID", "主体", "技能槽", "等级", "按钮阶段"],
    "TSET_AI_USE_SKILL":             ["技能槽", "目标单位", "距离超出不移动", "施法状态判定"],
    "TSET_ENTER_CD":                 ["技能槽", "CD值"],
    "TSET_REFRESH_CD":               ["技能槽"],
    "TSET_DECREASE_CD":              ["技能槽", "减少帧"],
    "TSET_SET_CD":                   ["技能槽", "CD值"],
    "TSET_INTERRUPT_SKILL":          ["目标", "中断方式", "TagID"],
    # AI
    "TSET_CHANGE_AI":                ["目标", "AI ConfigID"],
    # 工具
    "TSET_DEBUG_LOG":                ["值1", "值2", "值3", "值4"],
    "TSET_GET_MAIN_ENTITY_ID":       [],
    "TSET_GET_TARGET_ENTITY_ID":     [],
    "TSET_GET_PLAYER_MAIN_ENTITY":   ["PlayerIndex"],
    "TSET_FOLLOW_TARGET":            ["主体单位", "跟随单位", "朝向跟随", "位置跟随", "BattleFollowConfig", "初始角度"],
    "TSET_TELEPORT":                 ["方向类型", "偏移角", "距离"],
    "TSET_BATTLE_END":               ["阵营或玩家"],
    "TSET_LAYOUT_SUMMON_BULLET":     ["BulletID", "形状", "数量", "扇形角度", "内径", "速度"],
}

# 哪些 ParamType 引用哪个枚举表（用于反查中文）
PARAM_TYPE_TO_ENUM: dict[int, str] = {
    1: "TBattleNatureEnum",     # 属性
    # 2 函数返回值 → 引用 SkillEffectConfig（不是枚举）
    # 3 技能参数 → 引用 SkillTagsConfig（不是枚举）
    # 5 常用数值参数 → 引用 BattleCustomParamConfig
}


# ====================================================================
# JSON 解析
# ====================================================================
def load_skill_graph(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_config_json(raw: str) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_parse_error": raw[:120]}


def build_node_index(refs: list[dict]) -> dict[str, dict]:
    idx = {}
    for ref in refs:
        data = ref.get("data", {})
        guid = data.get("GUID")
        if not guid:
            continue
        idx[guid] = {
            "rid": ref.get("rid"),
            "class": ref.get("type", {}).get("class", "Unknown"),
            "data": data,
            "config": parse_config_json(data.get("ConfigJson", "")),
        }
    return idx


def build_rid_index(refs: list[dict]) -> dict[int, dict]:
    idx = {}
    for ref in refs:
        data = ref.get("data", {})
        idx[ref.get("rid")] = {
            "rid": ref.get("rid"),
            "class": ref.get("type", {}).get("class", "Unknown"),
            "data": data,
            "config": parse_config_json(data.get("ConfigJson", "")),
        }
    return idx


# ====================================================================
# 节点显示
# ====================================================================
def sanitize_mermaid_text(text) -> str:
    if text is None:
        return ""
    text = str(text).replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = text.replace('"', "'").replace("|", "/")
    text = re.sub(r"\s+", " ", text).strip()
    return text


PT_NAMES = {
    0: "",                      # TPT_NULL — 普通值，不显示后缀
    1: "属性",                  # → TBattleNatureEnum
    2: "→效果",                 # → 另一 SkillEffectConfig 的返回值
    3: "→技能参数",             # → SkillTagsConfig
    4: "模板参数",
    5: "上下文",                # → TCommonParamType（主体/目标/施法者...）
    6: "事件参数",
    7: "技能参数-常用",
}

# PT 整数 → 它的 Value 应该用哪个枚举字典反查
PT_TO_ENUM = {
    1: "TBattleNatureEnum",     # 属性
    5: "TCommonParamType",      # 上下文常量
}


def format_param_value(p: dict) -> str:
    """把 TParam 渲染成 'V (PT[反查中文])' 字符串。"""
    if not isinstance(p, dict):
        return str(p)
    v = p.get("Value", 0)
    pt = p.get("ParamType", 0)
    f = p.get("Factor", 0)
    pt_name = PT_NAMES.get(pt, "")
    extra = ""
    enum_name = PT_TO_ENUM.get(pt)
    if enum_name:
        cn = enum_int_to_cn(enum_name, v)
        if cn:
            extra = f"[{cn}]"
    if pt_name:
        suffix = f"({pt_name}{extra})"
    elif extra:
        suffix = extra
    else:
        suffix = ""
    factor_str = f" F={f}" if f else ""
    return f"{v}{suffix}{factor_str}"


def _is_zero_param(p) -> bool:
    return isinstance(p, dict) and p.get("Value", 0) == 0 and p.get("ParamType", 0) == 0 and p.get("Factor", 0) == 0


def format_params_short(node: dict, max_items: int = 10) -> str:
    """节点框内的简短 Params 摘要"""
    cls = node["class"]
    cfg = node["config"]
    params = cfg.get("Params", [])
    if not params:
        return ""
    labels = NODE_PARAM_LABELS.get(cls, [])
    parts = []
    for i, p in enumerate(params[:max_items]):
        label = labels[i] if i < len(labels) and labels[i] != "..." else f"P{i}"
        if _is_zero_param(p) and i >= 3:
            continue
        parts.append(f"{label}={format_param_value(p)}")
    if len(params) > max_items:
        parts.append("...")
    return "<br/>".join(parts)


def get_node_id(node: dict) -> str:
    return f"N{node['rid']}"


def get_node_brief_label(node: dict) -> str:
    cls = node["class"]
    data = node["data"]
    cfg = node["config"]
    cfg_id = cfg.get("ID") or data.get("ID") or "-"
    cn = class_to_cn_name(cls, cfg)
    desc = data.get("Desc", "") or cfg.get("Desc", "")
    desc = sanitize_mermaid_text(desc)[:30]

    parts = [f"<b>{cn}</b>"]
    parts.append(f"[{cls}] ID={cfg_id}")
    if desc:
        parts.append(f"'{desc}'")

    # 主节点的关键字段
    if cls == "SkillConfigNode":
        cn_name = cfg.get("SkillNameEditor", "") or ""
        cn_name = sanitize_mermaid_text(cn_name)[:20]
        if cn_name:
            parts.append(f"技能名={cn_name}")
        elem = enum_int_to_cn("TElementsType", cfg.get("ElementType"))
        sub = enum_int_to_cn("TBattleSkillSubType", cfg.get("SkillSubType"))
        cdt = enum_int_to_cn("TSkillColdType", cfg.get("CdType"))
        if elem:
            parts.append(f"五行={elem}")
        if sub:
            parts.append(f"子类型={sub}")
        if cdt:
            parts.append(f"CD类型={cdt}")
        if cfg.get("CdTime"):
            parts.append(f"CD={cfg['CdTime']}帧")
        if cfg.get("SkillRange"):
            parts.append(f"范围={cfg['SkillRange']}")
    elif cls == "SkillTagsConfigNode":
        if cfg.get("DefaultValue"):
            parts.append(f"Default={cfg['DefaultValue']}")
    elif cls == "ModelConfigNode":
        mp = cfg.get("ModelPath", "")
        if mp:
            parts.append(f"Path={sanitize_mermaid_text(mp)[:30]}")

    short = format_params_short(node, max_items=10)
    if short:
        parts.append(short)

    # 模板路径
    tdata = data.get("TemplateData") or {}
    tpath = tdata.get("TemplatePath", "")
    if tpath:
        tname = Path(tpath).stem.replace("SkillGraph_", "")
        parts.append(f"模板={sanitize_mermaid_text(tname)[:40]}")

    return "<br/>".join(parts)


def get_node_shape(cls: str) -> tuple[str, str]:
    if cls in {
        "TSET_ORDER_EXECUTE", "TSET_DELAY_EXECUTE", "TSET_REPEAT_EXECUTE",
        "TSET_RUN_SKILL_EFFECT_TEMPLATE",
    }:
        return "((", "))"
    if cls in {"TSET_SWITCH_EXECUTE", "TSET_PROBABILITY_EXECUTE", "TSET_CONDITION_EXECUTE"}:
        return "{{", "}}"
    if cls == "RefConfigBaseNode":
        return "[/", "/]"
    return "[", "]"


def render_node_box(node: dict) -> str:
    nid = get_node_id(node)
    label = get_node_brief_label(node)
    open_, close_ = get_node_shape(node["class"])
    return f'  {nid}{open_}"{label}"{close_}'


# ====================================================================
# 边推导（基于 ConfigJson Params + SkillConfig 结构化字段）
# ====================================================================
def build_id_to_rid_map(rid_idx: dict[int, dict]) -> dict[int, list[int]]:
    mapping: dict[int, list[int]] = {}
    for rid, n in rid_idx.items():
        cfg = n.get("config", {})
        cfg_id = cfg.get("ID")
        if cfg_id is None:
            cfg_id = n["data"].get("ID")
        if cfg_id:
            mapping.setdefault(int(cfg_id), []).append(rid)
    return mapping


def derive_edges_from_params(rid_idx: dict[int, dict], id_to_rid: dict[int, list[int]]) -> list[tuple[int, int, str]]:
    edges: list[tuple[int, int, str]] = []

    def best_target_rid(target_id: int) -> int | None:
        rids = id_to_rid.get(target_id, [])
        if not rids:
            return None
        for r in rids:
            if rid_idx[r]["class"] != "RefConfigBaseNode":
                return r
        return rids[0]

    for rid, n in rid_idx.items():
        cls = n["class"]
        cfg = n["config"]

        if cls == "SkillConfigNode":
            structural_refs = [
                ("入口效果", cfg.get("SkillEffectExecuteInfo", {}).get("SkillEffectConfigID")),
                ("入口筛选", cfg.get("SkillEffectExecuteInfo", {}).get("SelectConfigID")),
                ("被动入口", cfg.get("SkillEffectPassiveExecuteInfo", {}).get("SkillEffectConfigID")),
                ("卸下时", cfg.get("SkillEffectOnUnEquip")),
                ("打断时", cfg.get("SkillEffectOnSkillCastInterrupt")),
                ("释放条件", cfg.get("Condition")),
                ("AI释放条件", cfg.get("AICastCondition")),
            ]
            for label, target_id in structural_refs:
                if target_id and isinstance(target_id, int) and target_id != 0:
                    tr = best_target_rid(target_id)
                    if tr is not None:
                        edges.append((rid, tr, label))
            for tag_entry in cfg.get("SkillTagsList") or []:
                tid = tag_entry.get("SkillTagConfigID", 0)
                if tid:
                    tr = best_target_rid(tid)
                    if tr is not None:
                        edges.append((rid, tr, f"参数={tid}"))
            continue

        if cls == "SkillTagsConfigNode":
            fid = cfg.get("FinalValueEffectID", 0)
            if fid:
                tr = best_target_rid(fid)
                if tr is not None:
                    edges.append((rid, tr, "最终值效果"))
            continue

        if cls in {"RefConfigBaseNode", "ModelConfigNode"}:
            continue

        params = cfg.get("Params", [])
        if not params:
            continue
        labels = NODE_PARAM_LABELS.get(cls, [])
        for i, p in enumerate(params):
            if not isinstance(p, dict):
                continue
            v = p.get("Value", 0)
            pt = p.get("ParamType", 0)
            if not isinstance(v, int) or v == 0:
                continue
            # PT=1 (属性) / PT=5 (常用数值) / PT=3 (技能参数) 不指向图内节点
            if pt in (1, 5, 6):
                continue
            tr = best_target_rid(v)
            if tr is None or tr == rid:
                continue
            label_text = labels[i] if i < len(labels) and labels[i] != "..." else f"P{i}"
            edges.append((rid, tr, f"P{i}={label_text}"))

    return edges


def render_mermaid(graph: dict, node_idx: dict[str, dict], rid_idx: dict[int, dict], lr: bool = True) -> str:
    refs = graph.get("references", {}).get("RefIds", [])
    direction = "LR" if lr else "TD"
    lines = ["```mermaid", f"flowchart {direction}"]

    for ref in refs:
        guid = ref["data"].get("GUID")
        if not guid or guid not in node_idx:
            continue
        n = node_idx[guid]
        lines.append(render_node_box(n))

    id_to_rid = build_id_to_rid_map(rid_idx)
    derived_edges = derive_edges_from_params(rid_idx, id_to_rid)

    for parent_rid, child_rid, label in derived_edges:
        sid = f"N{parent_rid}"
        did = f"N{child_rid}"
        if label:
            lines.append(f"  {sid} -->|{label}| {did}")
        else:
            lines.append(f"  {sid} --> {did}")

    lines.append("```")
    return "\n".join(lines)


# ====================================================================
# 详细参数表
# ====================================================================
def format_param_full(p: dict, label: str) -> str:
    if not isinstance(p, dict):
        return f"{label}={p}"
    return f"{label}={format_param_value(p)}"


def render_node_detail_table(node_idx: dict[str, dict], refs: list[dict]) -> str:
    lines = ["## 节点详细参数表", ""]
    lines.append("| rid | 中文名 | 类名 | ID | Desc | 关键字段 / Params |")
    lines.append("|-----|--------|------|----|------|--------------------|")

    for ref in refs:
        guid = ref["data"].get("GUID")
        if not guid or guid not in node_idx:
            continue
        n = node_idx[guid]
        cls = n["class"]
        data = n["data"]
        cfg = n["config"]

        cfg_id = cfg.get("ID") or data.get("ID") or "-"
        desc = (data.get("Desc", "") or cfg.get("Desc", "")).replace("|", "/").replace("\n", " ").strip()[:40]
        cn = class_to_cn_name(cls, cfg)

        details: list[str] = []
        if cls == "SkillConfigNode":
            kv = [
                ("五行", enum_int_to_cn("TElementsType", cfg.get("ElementType"))),
                ("主类型", enum_int_to_cn("TBattleSkillMainType", cfg.get("SkillMainType"))),
                ("子类型", enum_int_to_cn("TBattleSkillSubType", cfg.get("SkillSubType"))),
                ("CD类型", enum_int_to_cn("TSkillColdType", cfg.get("CdType"))),
                ("CD", cfg.get("CdTime")),
                ("范围", cfg.get("SkillRange")),
                ("AI范围", cfg.get("AISkillRange")),
            ]
            for k, v in kv:
                if v not in (None, "", 0):
                    details.append(f"{k}={v}")
            sei = cfg.get("SkillEffectExecuteInfo") or {}
            if sei.get("SkillEffectConfigID"):
                details.append(f"入口效果ID={sei['SkillEffectConfigID']}")
            if sei.get("SelectConfigID"):
                details.append(f"入口筛选ID={sei['SelectConfigID']}")
        elif cls == "SkillTagsConfigNode":
            details.append(f"Default={cfg.get('DefaultValue', 0)}")
            details.append(f"RetainWhenDie={cfg.get('RetainWhenDie', False)}")
            tt = enum_int_to_cn("TSkillTagsType", cfg.get("TagType"))
            if tt:
                details.append(f"TagType={tt}")
        elif cls == "RefConfigBaseNode":
            details.append(f"引用 {data.get('TableManagerName', '')} ID={data.get('ID', '-')}")
        elif cls == "ModelConfigNode":
            details.append(f"ModelPath={cfg.get('ModelPath', '-')}")
        else:
            params = cfg.get("Params", [])
            labels = NODE_PARAM_LABELS.get(cls, [])
            for i, p in enumerate(params):
                lab = labels[i] if i < len(labels) and labels[i] != "..." else f"P{i}"
                details.append(format_param_full(p, lab))

        tdata = data.get("TemplateData") or {}
        if tdata.get("TemplatePath"):
            details.append(f"模板={Path(tdata['TemplatePath']).name}")

        lines.append(f"| {n['rid']} | **{cn}** | {cls} | {cfg_id} | {desc} | {('<br/>'.join(details)) or '-'} |")

    return "\n".join(lines)


# ====================================================================
# 技能基本信息
# ====================================================================
def render_skill_summary(node_idx: dict[str, dict]) -> str:
    skill = None
    for n in node_idx.values():
        if n["class"] == "SkillConfigNode":
            skill = n
            break
    if not skill:
        return "## 技能信息\n\n（未找到 SkillConfigNode）\n"

    cfg = skill["config"]
    lines = ["## 技能基本信息", ""]

    rows = [
        ("技能 ID", cfg.get("ID")),
        ("中文名", cfg.get("SkillNameEditor")),
        ("描述", cfg.get("SkillDescEditor")),
        ("五行", enum_int_to_cn("TElementsType", cfg.get("ElementType"))),
        ("主类型", enum_int_to_cn("TBattleSkillMainType", cfg.get("SkillMainType"))),
        ("子类型", enum_int_to_cn("TBattleSkillSubType", cfg.get("SkillSubType"))),
        ("CD 类型", enum_int_to_cn("TSkillColdType", cfg.get("CdType"))),
        ("CD 帧", cfg.get("CdTime")),
        ("施法范围", cfg.get("SkillRange")),
        ("AI 范围", cfg.get("AISkillRange")),
        ("前摇帧", cfg.get("SkillCastFrame")),
        ("缓冲区起始帧", cfg.get("SkillBufferStartFrame")),
        ("缓冲区时长", cfg.get("SkillBufferFrame")),
        ("基础时长", cfg.get("SkillBaseDuration")),
        ("MP 消耗", cfg.get("MPCost")),
        ("魂力消耗", cfg.get("HunLiValue")),
        ("心法能量", cfg.get("SectXinfaEnergyValue")),
        ("品质", cfg.get("SkillQuality")),
        ("Icon", cfg.get("Icon")),
    ]
    lines.append("| 字段 | 值 |")
    lines.append("|------|----|")
    for k, v in rows:
        if v in (None, "", 0, []):
            continue
        lines.append(f"| {k} | {v} |")

    info = cfg.get("SkillEffectExecuteInfo") or {}
    if info.get("SkillEffectConfigID"):
        lines.append(f"| **主动入口 SkillEffectConfigID** | **{info['SkillEffectConfigID']}** |")
    if info.get("SelectConfigID"):
        lines.append(f"| 主动入口 SelectConfigID | {info['SelectConfigID']} |")
    info2 = cfg.get("SkillEffectPassiveExecuteInfo") or {}
    if info2.get("SkillEffectConfigID"):
        lines.append(f"| 被动入口 SkillEffectConfigID | {info2['SkillEffectConfigID']} |")

    combo = cfg.get("ComboCdList") or []
    if combo:
        cs = ", ".join(
            f"({c.get('CDTime',0)}帧, BaseDur={c.get('BaseDuration',0)}, Buffer={c.get('BufferFrame',0)})"
            for c in combo
        )
        lines.append(f"| 连招 CD 列表 | {cs} |")
    tags = cfg.get("SkillTagsList") or []
    if tags:
        ts = ", ".join(f"Tag {t.get('SkillTagConfigID')}={t.get('Value')}" for t in tags)
        lines.append(f"| SkillTagsList | {ts} |")

    return "\n".join(lines)


# ====================================================================
# 主程序
# ====================================================================
def main():
    parser = argparse.ArgumentParser(description="将 SkillGraph JSON 转为 Mermaid 蓝图 + 参数表")
    parser.add_argument("input", help="输入 SkillGraph_*.json 路径")
    parser.add_argument("--out", "-o", help="输出 .md 路径（默认 stdout）")
    parser.add_argument("--simple", action="store_true", help="只输出 mermaid 图，不出参数表")
    parser.add_argument("--td", action="store_true", help="使用从上到下布局（默认 LR 左到右）")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"错误：文件不存在 {in_path}", file=sys.stderr)
        sys.exit(1)

    graph = load_skill_graph(in_path)
    refs = graph.get("references", {}).get("RefIds", [])
    node_idx = build_node_index(refs)
    rid_idx = build_rid_index(refs)

    out_lines = [f"# 技能蓝图：{in_path.stem}", ""]
    out_lines.append(render_skill_summary(node_idx))
    out_lines.append("")
    out_lines.append("## Mermaid 蓝图")
    out_lines.append("")
    out_lines.append(render_mermaid(graph, node_idx, rid_idx, lr=not args.td))

    if not args.simple:
        out_lines.append("")
        out_lines.append(render_node_detail_table(node_idx, refs))

    output = "\n".join(out_lines)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"已输出到 {args.out}", file=sys.stderr)
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
        print(output)


if __name__ == "__main__":
    main()
