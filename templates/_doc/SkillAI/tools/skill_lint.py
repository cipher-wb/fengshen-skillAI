#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SkillGraph JSON Lint 验证器 (PoC v0.1)

镜像 Unity SkillEditor OnSaveCheck 的核心规则。

用法:
    python skill_lint.py <file.json>                # 单文件
    python skill_lint.py <pattern> --recursive      # 批量
    python skill_lint.py <file.json> --strict       # warning 也视为失败

退出码:
    0 = 全部通过
    1 = 有 ERROR
    2 = strict 模式 + 有 WARN

PoC 实现的检查项（详见 PRD §6.2-6.3）：
  E001 JSON Schema 不合法
  E002 references.version != 2
  E003 缺少 SkillConfigNode
  E004 GUID 重复
  E005 rid 重复
  E006 edges 引用不存在的 GUID
  E007 节点 ConfigJson 解析失败
  E008 TSET_REPEAT_EXECUTE 间隔=0 且次数>100
  E009 CdType=连招但最后段 BaseDuration ≠ 0
  E012 招式 SkillSubType=招式 + CD=0
  E013 时序约束: CastFrame > BufferStartFrame
  E014 SkillEffectExecuteInfo.SkillEffectConfigID 引用不存在的节点
  E016 TParam.ParamType 取值非法（不在 0~7）
  E020 动态端口节点出边 outputPortIdentifier 必须为 "0"
        （TSET_ORDER_EXECUTE / TSET_NUM_MAX / TSET_NUM_MIN 等）
        — 否则编辑器加载 edges 时丢边 → 视觉悬空（PostMortem #022）
  E022 BulletConfigNode 字段端口一致性：当 ConfigJson 写非零 Model/AfterBorn/
        BeforeBorn/Die SkillEffectConfigID 时，必须有对应 PackedMembersOutput
        字段端口边连入 — v0.5 1860216 风格自包含模板的关键约定（PostMortem #024）

  W001 节点 Desc 为空
  W002 SkillTagsConfig.Desc 仍含 "_[ID]" 后缀
  W003 创建子弹/特效 急速影响=0
  W006 节点完全孤立（默认关闭，子模板"外部连线引用"模式会大量误报；
        仅在 builder 新建模板时显式调用 check_w006_isolated_node）
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Issue:
    code: str          # E001 / W001 ...
    severity: str      # ERROR / WARN / INFO
    location: str
    message: str
    fix_hint: str = ""

    def __str__(self):
        return f"[{self.code} {self.severity}] {self.location}: {self.message}" + (
            f"\n  → {self.fix_hint}" if self.fix_hint else ""
        )


@dataclass
class LintReport:
    file: str
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    infos: list[Issue] = field(default_factory=list)

    def add(self, issue: Issue):
        if issue.severity == "ERROR":
            self.errors.append(issue)
        elif issue.severity == "WARN":
            self.warnings.append(issue)
        else:
            self.infos.append(issue)

    def passed(self, strict: bool = False) -> bool:
        if self.errors:
            return False
        if strict and self.warnings:
            return False
        return True

    def summary(self) -> str:
        return f"E={len(self.errors)} W={len(self.warnings)} I={len(self.infos)}"


# ------------------------------------------------------------
# 单条规则实现
# ------------------------------------------------------------
def check_e001_top_level(graph: dict, report: LintReport):
    if "references" not in graph:
        report.add(Issue("E001", "ERROR", "/", "缺少 references 字段"))
    if "edges" not in graph:
        report.add(Issue("E001", "ERROR", "/", "缺少 edges 字段"))
    if "nodes" not in graph:
        report.add(Issue("E001", "ERROR", "/", "缺少 nodes 字段"))


def check_e002_refs_version(graph: dict, report: LintReport):
    refs = graph.get("references", {})
    if refs.get("version") != 2:
        report.add(Issue(
            "E002", "ERROR",
            "references.version",
            f"references.version 应为 2，实际为 {refs.get('version')}",
            "Unity 2021+ 要求 RefIds 格式 v2",
        ))


def check_e003_skill_config_node(refs_data: list[dict], report: LintReport):
    # 模板（任意节点 IsTemplate=true）可以没有 SkillConfigNode；普通技能必须有且仅一个
    is_template_graph = any(r.get("data", {}).get("IsTemplate") for r in refs_data)
    skill_configs = [r for r in refs_data
                     if r.get("type", {}).get("class") == "SkillConfigNode"]
    if is_template_graph:
        if len(skill_configs) > 1:
            report.add(Issue("E003", "ERROR", "/",
                             f"模板内 SkillConfigNode 数量 {len(skill_configs)}，最多 1 个"))
        return
    if len(skill_configs) == 0:
        report.add(Issue("E003", "ERROR", "/",
                         "缺少 SkillConfigNode（普通技能图必须有且仅一个技能根节点）"))
    elif len(skill_configs) > 1:
        report.add(Issue("E003", "ERROR", "/",
                         f"SkillConfigNode 数量 {len(skill_configs)}，必须为 1"))


def check_e004_guid_unique(refs_data: list[dict], report: LintReport):
    seen: dict[str, int] = {}
    for r in refs_data:
        guid = r.get("data", {}).get("GUID")
        if not guid:
            continue
        if guid in seen:
            report.add(Issue(
                "E004", "ERROR",
                f"rid={r.get('rid')}",
                f"GUID {guid[:8]}... 重复（与 rid={seen[guid]} 冲突）",
                "GUID 必须全图唯一，编译器应使用 uuid4 生成",
            ))
        else:
            seen[guid] = r.get("rid")


def check_e005_rid_unique(refs_data: list[dict], report: LintReport):
    seen = set()
    for r in refs_data:
        rid = r.get("rid")
        if rid in seen:
            report.add(Issue("E005", "ERROR", f"rid={rid}", "rid 重复"))
        else:
            seen.add(rid)


def check_e006_edges_guid(graph: dict, refs_data: list[dict], report: LintReport):
    valid_guids = {r["data"].get("GUID") for r in refs_data if "data" in r}
    for i, e in enumerate(graph.get("edges", [])):
        for field in ["inputNodeGUID", "outputNodeGUID"]:
            g = e.get(field)
            if g and g not in valid_guids:
                report.add(Issue(
                    "E006", "ERROR",
                    f"edges[{i}].{field}",
                    f"引用不存在的节点 GUID {g[:8]}...",
                    "edges 必须指向 references.RefIds 中存在的节点",
                ))


def check_e007_config_json(refs_data: list[dict], report: LintReport):
    for r in refs_data:
        data = r.get("data", {})
        cj = data.get("ConfigJson")
        if cj is None:
            cls = r.get("type", {}).get("class", "")
            if cls in {"RefConfigBaseNode"}:
                continue  # Ref 节点没有 ConfigJson
            report.add(Issue("E007", "ERROR", f"rid={r.get('rid')}", "节点缺少 ConfigJson"))
            continue
        try:
            json.loads(cj)
        except json.JSONDecodeError as e:
            report.add(Issue("E007", "ERROR", f"rid={r.get('rid')}",
                             f"ConfigJson 解析失败: {e}"))


def check_e008_repeat_execute(refs_data: list[dict], report: LintReport):
    """E008（v0.7 增强 / PostMortem #026）：TSET_REPEAT_EXECUTE 间隔=0 时次数上限校验。

    背景：项目 C++ 引擎 BattleEffectFactory.cpp:1800 对 iIntervalTime=0（同帧齐发）
    的 RepeatExecute 有硬上限保护。实测 200 已触发引擎报错 "Execute Count Too Big"，
    100 推测是分界（保守 ≤ 50 安全）。

    判定（仅当 iIntervalTime == 0 字面量；间隔由变量决定时跳过）：
      1. iExecuteCount.ParamType=0（字面量）
         - Value > 100 → ERROR
      2. iExecuteCount.ParamType=4（EXT_PARAM 引用）
         - 追溯模板根 TemplateParams[Value-1].DefalutParamJson.Value
         - 默认值 > 100 → ERROR（默认就超界）
         - 默认值 ≤ 100 → WARN（用户填超界时不会被 lint 挡，提示加 Desc 警告）

    PT=4 默认值无法解析（缺 TemplateParams / 解析失败）→ 静默跳过。
    """
    # 收集所有 IsTemplate 节点的 TemplateParams
    template_params_by_root: list[list[dict]] = []
    for r in refs_data:
        d = r.get("data") or {}
        if d.get("IsTemplate"):
            tp = d.get("TemplateParams") or []
            if tp:
                template_params_by_root.append(tp)

    def _resolve_ext_param_default(slot_value: int) -> int | None:
        """读 EXT_PARAM[slot]（1-based）的 DefalutParamJson.Value。多模板根取首个匹配。"""
        if slot_value <= 0:
            return None
        for tparams in template_params_by_root:
            if slot_value > len(tparams):
                continue
            tp = tparams[slot_value - 1]
            try:
                dpj = json.loads(tp.get("DefalutParamJson") or "{}")
            except (json.JSONDecodeError, TypeError):
                continue
            v = dpj.get("Value")
            if isinstance(v, int):
                return v
        return None

    for r in refs_data:
        data = r.get("data", {})
        cls = r.get("type", {}).get("class", "")
        if cls != "TSET_REPEAT_EXECUTE":
            continue
        try:
            cfg = json.loads(data.get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        params = cfg.get("Params", [])
        if len(params) < 2:
            continue
        interval_p = params[0]
        times_p = params[1]
        # 仅当 interval 为字面量 0 时检查（变量间隔运行时可能非 0，跳过避免误报）
        if interval_p.get("ParamType", 0) != 0 or interval_p.get("Value", 0) != 0:
            continue
        times_pt = times_p.get("ParamType", 0)
        times_v = times_p.get("Value", 0)
        if times_pt == 0:
            # 字面量
            if times_v > 100:
                report.add(Issue(
                    "E008", "ERROR", f"rid={r.get('rid')}",
                    f"TSET_REPEAT_EXECUTE 间隔=0 且次数={times_v}（C++ 引擎硬上限保护，"
                    f"实测 200 已触发 \"Execute Count Too Big\" 报错）",
                    "间隔=0 时次数 ≤ 100；安全范围 ≤ 50（PostMortem #026）",
                ))
        elif times_pt == 4:
            # EXT_PARAM 引用 → 追溯 TPARAMS 默认值
            default_v = _resolve_ext_param_default(times_v)
            if default_v is None:
                continue  # 无法解析，跳过
            if default_v > 100:
                report.add(Issue(
                    "E008", "ERROR", f"rid={r.get('rid')}",
                    f"TSET_REPEAT_EXECUTE 间隔=0 且次数=EXT_PARAM[{times_v}]，"
                    f"该槽位默认值={default_v} 超界（C++ 引擎单帧 RepeatExecute 硬上限）",
                    "默认值 ≤ 100；建议 ≤ 50（PostMortem #026）",
                ))
            else:
                report.add(Issue(
                    "E008", "WARN", f"rid={r.get('rid')}",
                    f"TSET_REPEAT_EXECUTE 间隔=0 且次数=EXT_PARAM[{times_v}]，"
                    f"默认值={default_v} 安全，但调用方填值不受 lint 拦截",
                    f"在 TemplateParams[{times_v}].DefaultValueDesc 写明 \"⚠️ N ≤ 50 安全；"
                    f"超过 100 触发引擎保护\"（PostMortem #026）",
                ))


def check_w009_combo_last_duration(refs_data: list[dict], report: LintReport):
    """注意：编辑器 OnSaveCheck 实际为 自动修正 + WARN，不是阻断。降级为 W009。"""
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls != "SkillConfigNode":
            continue
        try:
            cfg = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        if cfg.get("CdType") != 4:  # 4=连招
            continue
        combos = cfg.get("ComboCdList", [])
        if combos and combos[-1].get("BaseDuration", 0) != 0:
            report.add(Issue(
                "W009", "WARN", f"rid={r.get('rid')}",
                f"CdType=连招 时最后段 BaseDuration={combos[-1].get('BaseDuration')} 推荐为 0",
                "若不需要技能结束 CD 衔接逻辑，最后段 BaseDuration 应当 0",
            ))


def check_e012_zhaoshi_cd(refs_data: list[dict], report: LintReport):
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls != "SkillConfigNode":
            continue
        try:
            cfg = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        # 招式 = TBSST_ZHAO_SHI = 101 (按 TBattleSkillSubType 中文 招式 → 整数)
        # 通过检查 SubType + CdTime
        sub_type = cfg.get("SkillSubType", 0)
        cd_time = cfg.get("CdTime", 0)
        # 假设 招式 子类型整数 = 101，通过枚举字典反查
        # 这里硬编码 101（在 30122001 中观察到）
        if sub_type == 101 and cd_time == 0:
            report.add(Issue(
                "E012", "ERROR", f"rid={r.get('rid')}",
                "招式（TBSST_ZHAO_SHI）禁止 CD=0",
                "招式必须有 CD（哪怕 1 帧）",
            ))


def check_e013_timing(refs_data: list[dict], report: LintReport):
    """技能时长规则（详见 docs/易错点速查.md §13）：
      1) cast ≤ base_duration       —— 出手帧不能超出基础时长
      2) cast ≤ buffer_start + buffer_frame —— 出手帧必须在缓冲区结束前（仅当 buffer_frame > 0）
      3) buf_start ≤ base           —— 缓冲起始不能超出基础时长
      4) base ≤ cd                  —— 基础时长不能超过 CD

    历史修正：
      - 早期版本只检查 cast vs buf_start，漏报真实违规
      - 2026-05-08-004 补加规则 2（cast vs buffer_end），用户实测发现遗漏
    """
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls != "SkillConfigNode":
            continue
        try:
            cfg = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        cast = cfg.get("SkillCastFrame", 0)
        buf_start = cfg.get("SkillBufferStartFrame", 0)
        buf = cfg.get("SkillBufferFrame", 0)
        base = cfg.get("SkillBaseDuration", 0)
        cd = cfg.get("CdTime", 0)
        # 1) cast ≤ base
        if cast > base and base > 0:
            report.add(Issue(
                "E013", "ERROR", f"rid={r.get('rid')}",
                f"出手帧 SkillCastFrame({cast}) > SkillBaseDuration({base})",
                "时序约束：cast ≤ base ≤ cd（出手帧不能超出基础时长）",
            ))
        # 2) cast ≤ buf_start + buf （仅当 buf > 0，避免误报 buf=0 的连招技能）
        if buf > 0 and cast > buf_start + buf:
            report.add(Issue(
                "E013", "ERROR", f"rid={r.get('rid')}",
                f"出手帧 SkillCastFrame({cast}) > 缓冲区结束帧({buf_start}+{buf}={buf_start+buf})",
                "时序约束：cast ≤ buffer_start + buffer_frame（出手必须在缓冲区结束前）",
            ))
        # 3) buf_start ≤ base
        if buf_start > 0 and buf_start > base:
            report.add(Issue(
                "E013", "ERROR", f"rid={r.get('rid')}",
                f"缓冲起始 BufferStartFrame({buf_start}) > BaseDuration({base})",
            ))
        # 4) base ≤ cd
        if base > cd and cd > 0:
            report.add(Issue(
                "E013", "ERROR", f"rid={r.get('rid')}",
                f"基础时长 SkillBaseDuration({base}) > CdTime({cd})",
            ))


def check_e014_entry_ref(refs_data: list[dict], report: LintReport):
    """SkillEffectExecuteInfo.SkillEffectConfigID 必须指向存在的节点"""
    # 收集所有 SkillEffectConfig 的 ID
    effect_ids = set()
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls.startswith("TSET_") or cls == "RefConfigBaseNode":
            data = r.get("data", {})
            try:
                cfg = json.loads(data.get("ConfigJson", "{}")) if data.get("ConfigJson") else {}
                cid = cfg.get("ID") or data.get("ID")
                if cid:
                    effect_ids.add(int(cid))
            except json.JSONDecodeError:
                pass

    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls != "SkillConfigNode":
            continue
        try:
            cfg = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        sei = cfg.get("SkillEffectExecuteInfo", {})
        eid = sei.get("SkillEffectConfigID", 0)
        if eid and int(eid) not in effect_ids:
            report.add(Issue(
                "E014", "ERROR", f"rid={r.get('rid')}",
                f"主动入口 SkillEffectConfigID={eid} 在图内未找到对应节点",
                "应当指向某个 TSET_* 节点的 ConfigJson.ID",
            ))


def check_e016_param_type(refs_data: list[dict], report: LintReport):
    valid_pts = {0, 1, 2, 3, 4, 5, 6, 7}
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if not (cls.startswith("TSET_") or cls.startswith("TSCT_") or cls.startswith("TSKILLSELECT_")):
            continue
        try:
            cfg = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        for i, p in enumerate(cfg.get("Params", []) or []):
            if not isinstance(p, dict):
                continue
            pt = p.get("ParamType", 0)
            if pt not in valid_pts:
                report.add(Issue(
                    "E016", "ERROR", f"rid={r.get('rid')}.Params[{i}]",
                    f"ParamType={pt} 非法（合法值 0~7）",
                    "见 TParamType 枚举",
                ))


# ------------------------------------------------------------
# WARN 级
# ------------------------------------------------------------
def check_w001_empty_desc(refs_data: list[dict], report: LintReport):
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls in {"RefConfigBaseNode", "ModelConfigNode", "SkillConfigNode"}:
            continue
        if cls.startswith("TSET_") or cls.startswith("TSCT_") or cls.startswith("TSKILLSELECT_"):
            desc = r.get("data", {}).get("Desc", "")
            if not desc.strip():
                report.add(Issue(
                    "W001", "WARN", f"rid={r.get('rid')}",
                    f"{cls} 节点 Desc 为空",
                    "建议补充以利后续维护",
                ))


def check_w002_tag_desc_suffix(refs_data: list[dict], report: LintReport):
    import re
    pat = re.compile(r"_\[\d+\]$")
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls != "SkillTagsConfigNode":
            continue
        try:
            cfg = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        desc = cfg.get("Desc", "")
        if pat.search(desc):
            report.add(Issue(
                "W002", "WARN", f"rid={r.get('rid')}",
                f"SkillTagsConfig.Desc 含 '_[ID]' 后缀: {desc}",
                "节点拷贝后请清理后缀，否则编辑器拒绝保存",
            ))


def check_w003_rapid_affect(refs_data: list[dict], report: LintReport):
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls not in {"TSET_CREATE_BULLET", "TSET_CREATE_EFFECT"}:
            continue
        try:
            cfg = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        params = cfg.get("Params", [])
        # CREATE_BULLET 急速影响在 Params[14]
        # CREATE_EFFECT 急速影响在 Params[16]
        idx = 14 if cls == "TSET_CREATE_BULLET" else 16
        if idx < len(params):
            v = params[idx].get("Value", 0)
            if v == 0:
                report.add(Issue(
                    "W003", "WARN", f"rid={r.get('rid')}",
                    f"{cls} 急速影响=0（多数情况建议=1）",
                    "若刻意关闭可忽略",
                ))


# ------------------------------------------------------------
# v2.4 新增规则（基于 PostMortem #017 #018 #019 沉淀）
# ------------------------------------------------------------
INT32_MAX = 2_147_483_647


def check_e018_int32_overflow(refs_data: list[dict], report: LintReport):
    """E018：所有 ConfigJson Params 的 Value 必须 ≤ int32 max。

    依据：PostMortem #018 — Newtonsoft.Json 把 3014200301 解为 -1280766995 → 整节点反序列化失败。
    """
    for r in refs_data:
        try:
            cfg = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        # 节点自身 ID
        nid = cfg.get("ID")
        if isinstance(nid, int) and (nid > INT32_MAX or nid < -INT32_MAX - 1):
            report.add(Issue(
                "E018", "ERROR", f"rid={r.get('rid')}",
                f"节点 ID={nid} 溢出 int32（max={INT32_MAX}）",
                "Newtonsoft.Json 会解析为负数导致反序列化失败；改 ID < 2.1 亿",
            ))
        # Params Value
        for i, p in enumerate(cfg.get("Params", []) or []):
            if not isinstance(p, dict):
                continue
            v = p.get("Value", 0)
            if isinstance(v, int) and (v > INT32_MAX or v < -INT32_MAX - 1):
                report.add(Issue(
                    "E018", "ERROR", f"rid={r.get('rid')} Params[{i}]",
                    f"Value={v} 溢出 int32",
                    "节点反序列化会全炸；改 ID 命名约定（如 skill_id*10 而非 *100）",
                ))


def check_e019_undeclared_skill_tag(refs_data: list[dict], report: LintReport):
    """E019/W006：MODIFY/GET_SKILL_TAG_VALUE 引用 tag_id 的合法性检查。

    v2.4.1（PostMortem #020）：从粗暴 ERROR 改为 GET/MODIFY 区分判定 + Pattern C（临时 tag）合法化。
    v2.5.0（B-001 D-3）：声明源从 1 个扩到 3 个 — 之前只检 SkillTagsConfigNode（flow 内），
        漏检 SkillConfig.SkillTagsList / SkillDamageTagsList（顶层数组）。
        4/5 B-001 样本因此误报，本次修复消除该 false positive。

    判定逻辑：
      (a) Pattern A 技能级（V=41/PT=5）+ 该 tag 在本 JSON 有 MODIFY 写过
          → Pattern C 临时计算用法，合法（如 30212009 用 tag 1001~1005 做循环计数）
      (b) Pattern A 技能级 + 该 tag 在本 JSON 有 **3 个声明源中任一** 声明
          → Pattern A 私有持久，合法
            源 1：SkillTagsConfigNode（flow 内）
            源 2：SkillConfig.SkillTagsList（顶层数组）
            源 3：SkillConfig.SkillDamageTagsList（顶层数组）
      (c) Pattern A 技能级 + 既无声明又无 MODIFY，仅有 GET
          → 真"读引用不存在的 tag"问题 → ERROR（保留 E019）
      (d) Pattern B 实体级（V=0/PT=0）→ 跨技能透明读取，不强制声明
      (e) 跨技能（V=<other_skill_id>/PT=0）→ 应在源技能里声明，不在本 JSON

    待办：源 4 = 全局 SkillTagsConfig.xlsx（可能有项目级公共 tag），暂未检；
        若仍出现 false positive 再扩容。
    """
    declared_tags: set[int] = set()
    modified_tags: set[int] = set()  # v2.4.1：本 JSON 写过的 tag（视为合法的临时/私有）
    get_only_refs: list[tuple[dict, int]] = []  # 仅读未写的 tag 引用 → 后续报错

    for r in refs_data:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        # 源 1：SkillTagsConfigNode（flow 内声明）
        if cls == "SkillTagsConfigNode":
            try:
                cj = json.loads(r["data"].get("ConfigJson", "{}"))
                if cj.get("ID"):
                    declared_tags.add(cj["ID"])
            except json.JSONDecodeError:
                pass
        # 源 2 + 源 3：SkillConfigNode 顶层 SkillTagsList / SkillDamageTagsList（B-001 D-3 修复）
        elif cls == "SkillConfigNode":
            try:
                cj = json.loads(r["data"].get("ConfigJson", "{}"))
                for list_key in ("SkillTagsList", "SkillDamageTagsList"):
                    for entry in cj.get(list_key, []) or []:
                        tag_id = entry.get("SkillTagConfigID") if isinstance(entry, dict) else None
                        if tag_id:
                            declared_tags.add(tag_id)
            except json.JSONDecodeError:
                pass

    # 第一遍：扫所有 MODIFY 收集 modified_tags
    for r in refs_data:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        if cls != "TSET_MODIFY_SKILL_TAG_VALUE":
            continue
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        params = cj.get("Params", [])
        if len(params) < 3:
            continue
        tag_id = params[2].get("Value", 0)
        if tag_id:
            modified_tags.add(tag_id)

    # 第二遍：检查 GET / MODIFY 的合法性
    for r in refs_data:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        if cls not in ("TSET_MODIFY_SKILL_TAG_VALUE", "TSET_GET_SKILL_TAG_VALUE"):
            continue
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        params = cj.get("Params", [])
        if len(params) < 3:
            continue
        tag_id = params[2].get("Value", 0)
        skill_scope = params[1].get("Value", 0) if len(params) > 1 else 0
        skill_pt = params[1].get("ParamType", 0) if len(params) > 1 else 0
        if tag_id == 0:
            continue
        # (d) 实体级
        if skill_pt == 0 and skill_scope == 0:
            continue
        # (e) 跨技能
        if skill_pt == 0 and skill_scope != 0:
            continue
        # 进入 Pattern A 路径
        if cls == "TSET_MODIFY_SKILL_TAG_VALUE":
            # 写操作 → 默认合法（Pattern A 或 Pattern C 都通）
            # 但若混合 Pattern A + B（W005 已覆盖），不在此处再报
            continue
        # cls == TSET_GET_SKILL_TAG_VALUE 且 Pattern A
        if tag_id in declared_tags or tag_id in modified_tags:
            # (a) 临时计算 / (b) 私有持久 — 合法
            continue
        # (c) 真问题：读了既未声明又未写过的 tag → 必为 0 默认值
        report.add(Issue(
            "E019", "ERROR", f"rid={r.get('rid')}",
            f"GET_SKILL_TAG_VALUE 读 tag_id={tag_id}（技能级 Pattern A），"
            f"但本 JSON 既未声明也未写过它 — 一定读出 0 默认值",
            "三种修法：(a) 加 SkillTagsConfigNode 声明；(b) 改用实体级 Param[1]=0/PT=0；(c) 改用跨技能 Param[1]=源技能ID",
        ))


def check_w004_cross_skill_pt3(refs_data: list[dict], report: LintReport):
    """W004：MODIFY/GET_SKILL_TAG_VALUE 用 PT=3（SKILL_PARAM）作为 tag 引用 → 隐式当前技能。
    跨技能场景应该用 PT=0 + 显式 skill_id 或实体级 (Pattern B Param[1]=0/PT=0)。

    依据：PostMortem #019 — Pattern B (实体级) 是跨技能首选。
    """
    # 此 lint 只对 Param 中出现 PT=3 引用 tag 的情况告警 — 这种情况一般是 IR 写错
    for r in refs_data:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        if cls not in ("TSET_RUN_SKILL_EFFECT_TEMPLATE",):
            continue
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        for i, p in enumerate(cj.get("Params", []) or []):
            if not isinstance(p, dict):
                continue
            if p.get("ParamType") == 3 and p.get("Value", 0) > 1000:
                # PT=3 的 SKILL_PARAM 引用是有效的，但配合大 tag id 通常意味着策划想读 SkillTag
                # 应该改用 GET_SKILL_TAG_VALUE 显式调用
                report.add(Issue(
                    "W004", "WARN", f"rid={r.get('rid')} Params[{i}]",
                    f"PT=3 引用 Value={p['Value']} — 如果想读 SkillTag 跨技能，建议改用 "
                    f"TSET_GET_SKILL_TAG_VALUE 显式调用（实体级 Param[1]=0/PT=0 或技能级 Param[1]=源技能ID/PT=0）",
                    "见 PostMortem #019",
                ))


def check_w005_skill_tag_pattern(refs_data: list[dict], report: LintReport):
    """W005：MODIFY_SKILL_TAG_VALUE 的 Param[1] 用 V=41/PT=5（技能级）但有跨技能读取需求时建议改实体级。

    实践上很难自动判断意图；只在用户写了 Param[1]=41/PT=5（技能级）时给一个 INFO 级提示。
    """
    # 暂不强制告警 — Pattern A vs B 选用是设计决策
    # 仅在多个 MODIFY 用混合 Pattern 时提示一致性
    seen_patterns: dict[int, str] = {}  # tag_id → pattern
    for r in refs_data:
        cls = r.get("type", {}).get("class", "").split(".")[-1]
        if cls != "TSET_MODIFY_SKILL_TAG_VALUE":
            continue
        try:
            cj = json.loads(r["data"].get("ConfigJson", "{}"))
        except json.JSONDecodeError:
            continue
        params = cj.get("Params", [])
        if len(params) < 3:
            continue
        scope_v = params[1].get("Value", 0)
        scope_pt = params[1].get("ParamType", 0)
        tag_id = params[2].get("Value", 0)
        if tag_id == 0:
            continue
        pat = "B" if (scope_v == 0 and scope_pt == 0) else "A"
        if tag_id in seen_patterns and seen_patterns[tag_id] != pat:
            report.add(Issue(
                "W005", "WARN", f"rid={r.get('rid')}",
                f"tag {tag_id} 在多处 MODIFY 用混合模式（Pattern A 技能级 + Pattern B 实体级），可能导致读不到",
                "统一用 Pattern B 实体级（Param[1]=0/PT=0），见 PostMortem #019",
            ))
        else:
            seen_patterns[tag_id] = pat


# ------------------------------------------------------------
# v2.5 新增规则（PostMortem #022 — dynamic port 出边自检）
# ------------------------------------------------------------
# 与 skill_compiler.DYNAMIC_PORT_NODES 名单保持同步
# REPEAT 不在内：它有固定 schema，子效果在 Params[3]，出边用 outputPortIdentifier="3"
# （已用 1415 个真实样本统计 3337 条 REPEAT 出边全是 Params 索引值，证实）
DYNAMIC_PORT_NODES_LINT = {
    "TSET_ORDER_EXECUTE",
    "TSET_NUM_MAX",
    "TSET_NUM_MIN",
}


def check_e020_dynamic_port_edge(graph: dict, refs_data: list[dict], report: LintReport):
    """E020：动态端口节点出边的 outputPortIdentifier 必须为 "0"。

    依据：编辑器对动态端口节点（如 TSET_ORDER_EXECUTE 的"子效果1/2/3..."）只暴露
    一个锚点端口 "0"，所有 Params 共用。如果出边写成 "1"/"2"/...，编辑器加载时
    匹配不到端口实例 → 直接丢弃这条边 → 节点在画布上看起来悬空（数据保存正常，
    Lint 也能通过），但视觉读图全乱。

    参考真实样本 30212010、30122001 等：49+ 条 ORDER 出边全是 "0"。
    """
    guid_to_cls = {r["data"]["GUID"]: r.get("type", {}).get("class", "")
                   for r in refs_data if "data" in r and r["data"].get("GUID")}
    for i, e in enumerate(graph.get("edges", [])):
        src_cls = guid_to_cls.get(e.get("outputNodeGUID"), "")
        if src_cls in DYNAMIC_PORT_NODES_LINT and e.get("outputPortIdentifier") != "0":
            report.add(Issue(
                "E020", "ERROR", f"edges[{i}]",
                f"动态端口 {src_cls} 出边 outputPortIdentifier="
                f"{e.get('outputPortIdentifier')!r}，必须为 \"0\"",
                "动态端口节点（ORDER/NUM_MAX/NUM_MIN）所有 Params 出边共用 \"0\" 锚点；"
                "REPEAT/DELAY/CONDITION/SWITCH 等不在此名单（用 Params 索引正确）",
            ))


def check_e021_template_param_unused(refs_data: list[dict], report: LintReport):
    """E021/W007：模板根节点（IsTemplate=true）声明的 TemplateParams 中存在未被消费的槽位。

    依据：模板根的 TemplateParams 数组定义了 N 个外部参数（EXT_PARAM）。运行时
    调用方在 SkillConfigNode 的 TemplateData.TemplateParams 中按下标传值。模板
    内部应当存在至少一个节点的 ConfigJson.Params 用 ParamType=4 (PT_EXTRA_PARAM)
    + Value=i (1-based 槽位索引) 来读取。

    若声明了第 i 项 TemplateParam 但模板内部没有任何节点用 PT=4/Value=i 的写法
    引用，这个槽位就是"暴露未消费"——调用方面板上能填值但运行时没人读，
    任何修改都不会影响行为。这是 v0.3 之前迭代踩过的坑（用户报"参数无效"，
    根因：op 错配 + 部分槽位声明了但根本没读）。

    实现：
    1. 扫所有 IsTemplate=true 节点，收集 TemplateParams 列表 → 槽数 N
    2. 扫所有非引用类节点的 ConfigJson.Params，统计 ParamType==4 时 Value 出现次数
    3. 对 1..N 中每个槽位，未出现在统计里的 → 报警

    ⚠️ 默认未注册到 lint_file，因为真实模板里大量"暴露但未消费"是合法用法
    （为外部脚本/AI 子模板预留扩展点 / 跨文件 effect ID 引用 / 历史保留）。
    在 118 个真实模板上测试假阳性率 31%（37 文件 / 118）。

    启用方式：在 builder 自检时手动调用：
        from skill_lint import check_e021_template_param_unused
        report = LintReport(file=path)
        check_e021_template_param_unused(refs, report)
    """
    PT_EXTRA_PARAM = 4
    REF_CLS_SKIP = {"SkillTagsConfigNode", "BulletConfigNode", "ModelConfigNode",
                    "BuffConfigNode", "RefConfigBaseNode"}

    # 1) 先找所有 IsTemplate 节点
    template_roots = []
    for r in refs_data:
        d = r.get("data") or {}
        if d.get("IsTemplate"):
            tp = d.get("TemplateParams") or []
            if tp:
                template_roots.append((d.get("ID"), tp))

    if not template_roots:
        return  # 普通技能，不检查

    # 2) 统计所有 PT=4 的 Value
    used_indices: dict[int, list[tuple]] = {}
    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls in REF_CLS_SKIP:
            continue
        d = r.get("data") or {}
        try:
            cfg = json.loads(d.get("ConfigJson") or "{}")
        except Exception:
            continue
        params = cfg.get("Params", [])
        for pi, p in enumerate(params):
            if not isinstance(p, dict):
                continue
            if p.get("ParamType") == PT_EXTRA_PARAM:
                v = p.get("Value", 0)
                if isinstance(v, int) and v > 0:
                    used_indices.setdefault(v, []).append(
                        (d.get("ID"), cls, pi)
                    )

    # 3) 对每个模板根，比对槽位是否被消费
    for tpl_id, tparams in template_roots:
        for i in range(1, len(tparams) + 1):
            if i not in used_indices:
                name = tparams[i - 1].get("Name", f"<#{i}>") if i - 1 < len(tparams) else f"<#{i}>"
                report.add(Issue(
                    "E021", "ERROR", f"template ID={tpl_id}",
                    f"TemplateParam[{i}] '{name}' 声明了但模板内部无节点用 "
                    f"ParamType=4/Value={i} 消费 → 运行时调用方填值无效",
                    "暴露槽位必须有至少一处 PT=4/Value=i 引用；删除冗余声明 OR 把消费补全",
                ))


def check_e022_bullet_field_port_consistency(graph: dict, refs_data: list[dict], report: LintReport):
    """E022（v0.5+）：模板内置 BulletConfigNode 字段端口一致性 — 严格版。

    依据（PostMortem #024）：1860216 风格自包含模板（如 v0.5 旋转扩张子弹圈）的
    关键约定是 BulletConfig 关键字段（Model、AfterBorn 等）通过 PackedMembersOutput
    字段端口边连入"模板内同图存在"的 ID 提供者节点。

    重要：项目内大量真实样本（千叶散华以外的卡牌/普通技能）的 BulletConfig.Model
    字段直接写 ID 死值（如 30008/30129 等），而**不**用字段端口边——这是合法用法
    （ConfigJson 字段是 single source of truth；字段端口边只是 SkillEditor UI
    提示）。Model=4 是空子弹专属，更不需要 ModelConfigNode。

    所以 E022 严格判定：
    1. 仅当 BulletConfig.Model 字段值在**同图内有同 ID 的 ModelConfigNode 节点**时，
       才要求有 PackedMembersOutput.Model 字段端口边。
       （即用户已经声明了"模板内置的 ID 提供者"，那字段端口边必须连上）
    2. 同理 AfterBorn / BeforeBorn / Die SkillEffectConfigID 仅当对应 effect ID
       是同图内某节点的 ID 时才要求字段端口边。
    3. 排除 Model=4 空子弹（私有约定，不需要 ModelConfigNode）。
    4. 字段值=0 不强求（默认/未配置）。

    这条 E022 仅捕获 v0.5 自包含模板"内置 BulletConfig + 内置 ID 提供者节点 +
    缺字段端口边"的退化场景，不会误报普通技能的"BulletConfig 跨图引用 Model 表 ID"
    场景（因为同图内没有同 ID 节点）。
    """
    # 同图所有节点 ID → cls 索引
    id_to_cls: dict[int, str] = {}
    for r in refs_data:
        d = r.get("data") or {}
        nid = d.get("ID")
        if isinstance(nid, int):
            id_to_cls[nid] = r.get("type", {}).get("class", "")

    # 收集每个节点的入边（按 outputPortIdentifier 索引）
    in_edges_by_node: dict[str, dict[str, list[int]]] = {}
    for i, e in enumerate(graph.get("edges", [])):
        if e.get("outputFieldName") != "PackedMembersOutput":
            continue
        out_g = e.get("outputNodeGUID", "")
        port_id = e.get("outputPortIdentifier", "")
        in_edges_by_node.setdefault(out_g, {}).setdefault(port_id, []).append(i)

    # 对每个 BulletConfigNode 查 ConfigJson 字段
    # (字段路径, 显示名, 期望同图节点 cls)
    BULLET_FIELDS_TO_CHECK = [
        ("Model", "BulletConfig.Model", "ModelConfigNode"),
        ("AfterBornSkillEffectExecuteInfo.SkillEffectConfigID", "AfterBorn 出生效果", "TSET_"),
        ("BeforeBornSkillEffectExecuteInfo.SkillEffectConfigID", "BeforeBorn 出生前效果", "TSET_"),
        ("DieSkillEffectExecuteInfo.SkillEffectConfigID", "Die 死亡效果", "TSET_"),
    ]
    EMPTY_BULLET_MODEL_ID = 4  # 空子弹专属（PostMortem 私有约定，memory/reference_empty_bullet_model.md）

    for r in refs_data:
        cls = r.get("type", {}).get("class", "")
        if cls != "BulletConfigNode":
            continue
        d = r.get("data") or {}
        guid = d.get("GUID", "")
        bullet_id = d.get("ID", 0)
        try:
            cfg = json.loads(d.get("ConfigJson") or "{}")
        except Exception:
            continue

        node_in = in_edges_by_node.get(guid, {})

        for path, label, expected_cls_prefix in BULLET_FIELDS_TO_CHECK:
            # 分解嵌套路径
            parts = path.split(".")
            cur = cfg
            for part in parts:
                if not isinstance(cur, dict):
                    cur = None; break
                cur = cur.get(part)
            value = cur if isinstance(cur, int) else 0

            if value == 0:
                continue  # 默认值，不检查
            if path == "Model" and value == EMPTY_BULLET_MODEL_ID:
                continue  # 空子弹 Model=4 私有约定，不需要 ModelConfigNode

            # 严格版：仅当同图内有同 ID 节点（且类型匹配预期）才要求字段端口边
            target_cls = id_to_cls.get(value)
            if target_cls is None:
                continue  # 跨图引用，本规则不管
            if expected_cls_prefix == "ModelConfigNode" and target_cls != "ModelConfigNode":
                continue  # 同 ID 节点不是 ModelConfigNode（罕见冲突），不强求
            if expected_cls_prefix == "TSET_" and not target_cls.startswith("TSET_"):
                continue

            # 已确认同图内存在 ID 提供者节点 → 字段端口边必须存在
            if path not in node_in:
                report.add(Issue(
                    "E022", "ERROR", f"BulletConfig ID={bullet_id} GUID={guid[:8]}",
                    f"{label} 字段写值={value} 且同图内有 {target_cls} ID={value} 节点，"
                    f"但缺少 PackedMembersOutput 字段端口边 (outputPortIdentifier={path!r})",
                    "v0.5 1860216 风格自包含模板的硬约定：内置 ID 提供者节点必须用 "
                    f"PackedMembersOutput.{path} 字段端口边连入 BulletConfig",
                ))


def check_w006_isolated_node(graph: dict, refs_data: list[dict], report: LintReport):
    """W006：完全孤立节点（无入边 + 无出边，且不是合法的 leaf/root）。

    依据：用户报告"很多节点没连线"时第一反应是这个。但判定要排除：
      - SkillTagsConfigNode：定义节点，没有 in/out 边是常态（被引用 = 入边）
      - RefConfigBaseNode / ModelConfigNode：引用占位节点
      - 模板根（IsTemplate=true）：定义上是出边的源头，无入边正常
      - SkillConfigNode：技能根，无入边正常
      - 工具子图根（如 32300101 OnTick init）：用户用 IsTemplate 或 desc 标记 — 难以
        全自动识别，因此本规则只在节点**完全无 in 也无 out** 时报警

    若是双根模板，把另一个根的节点 desc 加上"根/Root"等关键字可豁免。
    """
    in_e: dict[str, int] = {}
    out_e: dict[str, int] = {}
    for e in graph.get("edges", []):
        in_e[e.get("inputNodeGUID", "")] = in_e.get(e.get("inputNodeGUID", ""), 0) + 1
        out_e[e.get("outputNodeGUID", "")] = out_e.get(e.get("outputNodeGUID", ""), 0) + 1

    EXEMPT_CLS = {
        "SkillTagsConfigNode", "RefConfigBaseNode", "ModelConfigNode",
        "SkillConfigNode", "BulletConfigNode", "SkillInterruptConfigNode",
    }
    for r in refs_data:
        d = r.get("data") or {}
        g_ = d.get("GUID")
        cls = r.get("type", {}).get("class", "")
        if not g_ or cls in EXEMPT_CLS:
            continue
        if d.get("IsTemplate"):
            continue  # 模板根
        if in_e.get(g_, 0) == 0 and out_e.get(g_, 0) == 0:
            report.add(Issue(
                "W006", "WARN", f"rid={r.get('rid')}",
                f"{cls} 节点 ID={d.get('ID')} 完全孤立（无入边无出边）"
                + (f" Desc={d.get('Desc', '')[:30]!r}" if d.get("Desc") else ""),
                "若为工具子图根（用户手动外接），把节点 IsTemplate 设 true 可豁免；"
                "否则可能漏写 Params 引用 → 编译器没建出边",
            ))


# ------------------------------------------------------------
# 主验证流程
# ------------------------------------------------------------
ALL_CHECKS = [
    check_e001_top_level,
    check_e002_refs_version,
    # 下面这批接收 refs_data
]

REFS_CHECKS = [
    check_e003_skill_config_node,
    check_e004_guid_unique,
    check_e005_rid_unique,
    check_e007_config_json,
    check_e008_repeat_execute,
    check_w009_combo_last_duration,
    check_e012_zhaoshi_cd,
    check_e013_timing,
    check_e014_entry_ref,
    check_e016_param_type,
    check_w001_empty_desc,
    check_w002_tag_desc_suffix,
    check_w003_rapid_affect,
    # v2.4 新增（PostMortem #017 #018 #019 沉淀）
    check_e018_int32_overflow,
    check_e019_undeclared_skill_tag,
    check_w004_cross_skill_pt3,
    check_w005_skill_tag_pattern,
    # 注：v2.6 PostMortem #023 的 check_e021_template_param_unused 默认不启用
    # （真实模板假阳性 31%）。仅在 builder 自检时手动调用，避免污染默认管线。
]


def lint_file(path: Path) -> LintReport:
    report = LintReport(file=str(path))
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report.add(Issue("E001", "ERROR", "/", f"JSON 解析失败: {e}"))
        return report
    except Exception as e:
        report.add(Issue("E001", "ERROR", "/", f"读取失败: {e}"))
        return report

    # 顶层检查
    for fn in ALL_CHECKS:
        fn(graph, report)

    refs = graph.get("references", {}).get("RefIds", [])

    # refs 级检查
    for fn in REFS_CHECKS:
        fn(refs, report)

    # 边-节点引用检查（需要顶层 + refs）
    check_e006_edges_guid(graph, refs, report)
    # v2.5 PostMortem #022：dynamic port 出边自检（无误报，默认开启）
    check_e020_dynamic_port_edge(graph, refs, report)
    # v2.6 PostMortem #024：内置 BulletConfig 字段端口一致性（生产中大量真实模板
    # 即便同图有 ID 提供者也未连字段端口边，假阳性 88 条）→ 默认关闭，仅 builder
    # 自检场景调用 check_e022_bullet_field_port_consistency。
    # W006 孤立节点告警 — 子模板里大量使用"外部连线引用"模式（节点放画布上但跨文件引用），
    # 默认会产生 30+ 条误报。降级为可选规则，仅在新建模板的 builder 自检场景启用。
    # 启用方式：在调用 lint_file 时设 enable_w006=True，或直接在 builder 里调用 check_w006_isolated_node。
    # check_w006_isolated_node(graph, refs, report)

    return report


def print_report(report: LintReport, color: bool = True):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    print(f"\n=== Lint: {Path(report.file).name} ===")
    if report.errors:
        print(f"❌ ERRORS ({len(report.errors)}):")
        for issue in report.errors:
            print(f"  {issue}")
    if report.warnings:
        print(f"⚠️  WARNINGS ({len(report.warnings)}):")
        for issue in report.warnings:
            print(f"  {issue}")
    if not report.errors and not report.warnings:
        print(f"✅ PASS")
    print(f"Summary: {report.summary()}")


def main():
    parser = argparse.ArgumentParser(description="SkillGraph JSON Lint 验证器")
    parser.add_argument("input", help="输入 JSON 路径或 glob")
    parser.add_argument("--recursive", "-r", action="store_true", help="递归搜索")
    parser.add_argument("--strict", action="store_true", help="warning 也视为失败")
    parser.add_argument("--quiet", "-q", action="store_true", help="只输出错误")
    args = parser.parse_args()

    in_path = Path(args.input)
    files: list[Path] = []
    if in_path.is_file():
        files.append(in_path)
    elif in_path.is_dir():
        files.extend(in_path.rglob("SkillGraph_*.json") if args.recursive
                     else in_path.glob("SkillGraph_*.json"))
    else:
        # 当作 glob 处理
        files.extend(Path(".").glob(args.input))

    if not files:
        print(f"❌ 找不到匹配文件: {args.input}", file=sys.stderr)
        sys.exit(1)

    has_error = False
    has_warn = False
    for f in files:
        report = lint_file(f)
        if report.errors:
            has_error = True
        if report.warnings:
            has_warn = True
        if not args.quiet or report.errors or report.warnings:
            print_report(report)

    if has_error:
        sys.exit(1)
    if args.strict and has_warn:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
