# -*- coding: utf-8 -*-
"""
verify_homogeneity.py — 通用同质度 fs 真扫验证脚本

目的（v0.16.23 B-043 R1 Gate (g) 新立配套工具）：
- 任何 candidate 累积 ≥4 例 / 升 candidate 或升正式之前 / 必须 fs 真扫所有兄弟样本验证主张维度同质度
- 禁止 curator 凭闭卷 + read.json 单 sample 印象归纳同质度
- 违反 Gate (g) → R1 自动必修 + 主张范围缩到真同质例 / 或扩为开放矩阵

用法：
  python verify_homogeneity.py --pattern "SkillGraph_30512*.json" \
    --root "F:/.../Jsons/宗门技能/宗门心法/木宗门心法" \
    --dims nodes,active_root,passive_root,skill_config_node,main_type,sub_type,element_type

输出：JSON 报告 / stdout 表格 / 同质度 % 摘要
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from collections import Counter
from typing import Any


def extract_fields(json_path: Path) -> dict:
    """从 SkillGraph JSON 提取关键维度字段。

    v0.16.29 / B-049 R1 修正（Gate (g) v3 立法 / master-flag-any-True 语义对齐 D-2401/D-4004 升正式 grep_source）：

    - **原 v0.16.23 实现**：读 data['nodes'] 作节点列表 + 找 NodeClassType / Type 字段提取 SkillConfigNode
      → 在 SkillEditor 真实 schema 下 data['nodes'] 仅是 [{rid: ...}] 指针，真实节点 data 在 data['references']['RefIds'][].type.class
    - **v0.16.29 B-049 R0 修正**：align B-049_read.py / SkillEditor schema ground truth / 改读 references.RefIds[].type.class
      → 但 is_template 仍仅取**单个** SkillConfigNode refid 的 IsTemplate / **语义窄化** = D-2401 概念反转误判 (B-049 R0 0/3121 命中)
    - **v0.16.29 B-049 R1 修正 (Gate (g) v3)**：is_template 改为 master-flag-any-True 语义
      → **任何 refid (含 SkillConfigNode / BulletConfig / TemplateNode 等任意类型节点) data.IsTemplate=true → is_template_any_true=true**
      → 与 D-2401/D-4004 升正式主张本体 "filename【模板】 + IsTemplate master flag" 语义一致
      → B-049 R0 因 curator 印象 "0/3121 命中" 误判触发 fast-path 真硬停 #1 候选 = 工具语义窄化 bug 非真概念反转
      → 同 B-044 D-4002 (A) 工具 bug 误判真硬停 #1 模式 / curator 性质误判第 4 次

    保留 is_template_sc（旧字段，仅 SkillConfigNode level）作为参考维度 / 不删除 / rule_2 严守。
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}", "_file": str(json_path)}

    refs = data.get("references", {}) or {}
    rids = refs.get("RefIds", []) or []
    top_nodes_count = len(data.get("nodes", []) or [])  # 指针列表长度 = 节点数
    top_edges_count = len(data.get("edges", []) or [])

    # 真实节点数据扫描
    active_root = None
    passive_root = None
    main_type = None
    sub_type = None
    element_type = None
    is_template_sc = None        # 单 SkillConfigNode refid IsTemplate（v0.16.29 B-049 R0 旧语义 / 保留参考）
    is_template_any_true = False # master-flag-any-True 语义（v0.16.29 B-049 R1 Gate (g) v3 新立 / 对齐 D-2401/D-4004 升正式）
    is_template_true_node_classes = []  # any-True 命中的节点类列表（诊断用）
    has_skill_config_node = False
    bullet_count = 0
    skill_entry_found = False

    for r in rids:
        t = r.get("type", {}) or {}
        cls = t.get("class", "")
        d = r.get("data", {}) or {}

        # ⭐ master-flag-any-True 扫描（v0.16.29 Gate (g) v3）
        # 任何节点 data.IsTemplate=true → is_template_any_true=true
        node_is_template = d.get("IsTemplate")
        if node_is_template is True:
            is_template_any_true = True
            is_template_true_node_classes.append(cls)

        if "Bullet" in cls and "Config" in cls:
            bullet_count += 1
        if cls == "SkillConfigNode":
            has_skill_config_node = True
            is_template_sc = d.get("IsTemplate")  # 单 SC level IsTemplate（旧语义保留）
            cj = d.get("ConfigJson")
            if isinstance(cj, str):
                try:
                    cj = json.loads(cj)
                except Exception:
                    cj = None
            if isinstance(cj, dict):
                sei = cj.get("SkillEffectExecuteInfo")
                spe = cj.get("SkillEffectPassiveExecuteInfo")
                if isinstance(sei, dict):
                    sec_id = sei.get("SkillEffectConfigID", 0)
                    if sec_id and sec_id != 0:
                        active_root = sec_id
                if isinstance(spe, dict):
                    sec_id = spe.get("SkillEffectConfigID", 0)
                    if sec_id and sec_id != 0:
                        passive_root = sec_id
                main_type = cj.get("SkillMainType")
                sub_type = cj.get("SkillSubType")
                element_type = cj.get("ElementType")
            # SkillEntry 与 SkillConfigNode 在此 schema 下统一为 SkillConfigNode refid 解析
            skill_entry_found = True

    # SC 维度 = SkillConfigNode refid 存在
    sc_flag = has_skill_config_node

    # dual_NULL: AR/PR 都 None or 0
    def is_null(v):
        return v is None or v == 0 or v == "" or v == "0"

    dual_NULL = is_null(active_root) and is_null(passive_root)
    dual_zero = (active_root == 0 or active_root is None) and (passive_root == 0 or passive_root is None)

    return {
        "filename": json_path.name,
        "skill_id": extract_skill_id(json_path.name),
        "nodes": top_nodes_count,  # 顶层 nodes[] 长度 = refid 长度
        "edges": top_edges_count,
        "active_root": active_root,
        "passive_root": passive_root,
        "main_type": main_type,
        "sub_type": sub_type,
        "element_type": element_type,
        "skill_config_node_raw": has_skill_config_node,
        "SC": sc_flag,
        "is_template": is_template_any_true,  # ⭐ v0.16.29 Gate (g) v3 主语义 = master-flag-any-True
        "is_template_any_true": is_template_any_true,  # 显式字段
        "is_template_sc": is_template_sc,  # 旧语义（仅 SC refid 上）/ 保留参考 / 不删除 (rule_2)
        "is_template_true_node_classes": is_template_true_node_classes,  # 诊断用 / 哪些节点类带 IsTemplate=true
        "mode": None,  # legacy field placeholder
        "bullet_count": bullet_count,
        "dual_NULL": dual_NULL,
        "dual_zero": dual_zero,
    }


def extract_skill_id(filename: str) -> str:
    """从 SkillGraph_30512003【木宗门】密卷-生春术.json 提取 30512003。"""
    base = filename.replace("SkillGraph_", "").replace(".json", "")
    # 数字 prefix
    sid = ""
    for c in base:
        if c.isdigit():
            sid += c
        else:
            break
    return sid


def homogeneity_check(samples: list[dict], dims: list[str], claim_filter: dict | None = None) -> dict:
    """
    对样本做同质度分析。

    dims: 维度列表，对每个维度统计分布
    claim_filter: 可选 {dim: expected_value} 过滤 / 用于校对主张
    """
    result = {
        "total_samples": len(samples),
        "valid_samples": len([s for s in samples if "_error" not in s]),
        "errors": [s for s in samples if "_error" in s],
        "dim_distribution": {},
        "claim_match": None,
    }

    valid = [s for s in samples if "_error" not in s]

    for dim in dims:
        values = [s.get(dim) for s in valid]
        counter = Counter([str(v) for v in values])
        result["dim_distribution"][dim] = {
            "unique_values": len(counter),
            "distribution": dict(counter.most_common()),
        }

    if claim_filter:
        # 过滤符合 claim 的样本 / 统计 hit rate
        def match(s):
            for k, v in claim_filter.items():
                if s.get(k) != v:
                    return False
            return True
        hits = [s for s in valid if match(s)]
        result["claim_match"] = {
            "filter": claim_filter,
            "hit_count": len(hits),
            "hit_ids": [s["skill_id"] for s in hits],
            "miss_count": len(valid) - len(hits),
            "miss_details": [
                {"skill_id": s["skill_id"], **{k: s.get(k) for k in claim_filter}}
                for s in valid if not match(s)
            ],
            "homogeneity_pct": round(100.0 * len(hits) / max(1, len(valid)), 2),
        }

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="兄弟样本根目录")
    ap.add_argument("--pattern", required=True, help="glob 文件名 pattern (例: SkillGraph_30512*.json)")
    ap.add_argument("--dims", default="nodes,active_root,passive_root,SC,main_type,sub_type,element_type,is_template",
                    help="同质度维度列表 / 逗号分隔")
    ap.add_argument("--claim-json", help="主张过滤 JSON / 例 '{\"nodes\": 1, \"SC\": true}'")
    ap.add_argument("--out", help="输出 JSON 报告路径")
    ap.add_argument("--exclude", default="废弃", help="排除路径关键词 / 默认排废弃技能")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        sys.exit(1)

    # 递归找文件
    files = list(root.rglob(args.pattern))
    # 排除关键词
    if args.exclude:
        files = [f for f in files if args.exclude not in str(f)]
    files = sorted(files)

    print(f"[scan] root={root}", file=sys.stderr)
    print(f"[scan] pattern={args.pattern} / exclude={args.exclude}", file=sys.stderr)
    print(f"[scan] {len(files)} files matched", file=sys.stderr)

    samples = [extract_fields(f) for f in files]

    dims = [d.strip() for d in args.dims.split(",")]
    claim_filter = json.loads(args.claim_json) if args.claim_json else None

    report = homogeneity_check(samples, dims, claim_filter)
    report["files_scanned"] = [str(f) for f in files]
    report["samples"] = samples

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"[out] {args.out}", file=sys.stderr)

    # stdout 摘要
    print(f"\n=== verify_homogeneity report ===")
    print(f"total: {report['total_samples']}  valid: {report['valid_samples']}  errors: {len(report['errors'])}")
    for dim, info in report["dim_distribution"].items():
        print(f"\n[dim] {dim}  unique={info['unique_values']}")
        for v, c in info["distribution"].items():
            print(f"  {v!r:30s} -> {c}")
    if report["claim_match"]:
        cm = report["claim_match"]
        print(f"\n[claim] filter={cm['filter']}")
        print(f"  hit  {cm['hit_count']}/{report['valid_samples']}  ({cm['homogeneity_pct']}%)")
        print(f"  hit_ids: {cm['hit_ids']}")
        if cm["miss_count"]:
            print(f"  miss {cm['miss_count']}:")
            for m in cm["miss_details"]:
                print(f"    {m}")


if __name__ == "__main__":
    main()
