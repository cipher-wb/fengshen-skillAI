# -*- coding: utf-8 -*-
"""
学习清单自动聚合脚本（每批 COMMIT 后 curator 强制调用 / CLAUDE.local.md §AI 主动沉淀守则）

工作流：
1. 扫所有 doc/SkillAI/mental_model/batch_buffer/B-*_picks.json 聚合已学 sid 清单
2. 递归扫 <<SKILLGRAPH_JSONS_ROOT>> 内 521 in_scope 范围
3. 对比 → 输出 doc/SkillAI/mental_model/学习清单.md

排除规则：
- 路径含"废弃" / "AIGen" / "AIGC" 的不进 in_scope
- 文件名不以 SkillGraph_ 开头的跳过

调用：
    cd 工程根目录
    python3 doc/SkillAI/mental_model/batch_buffer/_aggregate_learning_inventory.py
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = "Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons"
BATCH_DIR = "doc/SkillAI/mental_model/batch_buffer"
OUT_MD = "doc/SkillAI/mental_model/学习清单.md"
OUT_JSON = "doc/SkillAI/mental_model/batch_buffer/_learning_inventory.json"

INSCOPE = {
    "宗门功法-木": "宗门技能/木宗门技能",
    "宗门功法-火": "宗门技能/火宗门技能",
    "宗门功法-金": "宗门技能/金宗门技能",
    "宗门功法-水": "宗门技能/水宗门技能",
    "宗门功法-土": "宗门技能/土宗门技能",
    "宗门标签-BD": "宗门技能/BD标签",
    "宗门标签-宗门": "宗门技能/宗门标签",
    "宗门标签-通用BUFF": "宗门技能/通用BUFF",
    "宗门标签-其他(有用)": "宗门技能/其他（有用）",
    "宗门心法": "宗门技能/宗门心法",
    "技能模板-伤害": "技能模板/伤害",
    "技能模板-功能": "技能模板/功能",
    "技能模板-单位": "技能模板/单位",
    "技能模板-子弹": "技能模板/子弹",
    "技能模板-技能": "技能模板/技能",
    "技能模板-数值": "技能模板/数值",
}

EXCLUDE_PARTS = ["废弃", "AIGen", "AIGC"]


def aggregate_learned():
    """扫所有 picks.json 聚合已学 sid → 来自哪批"""
    learned = {}
    picks_files = sorted(
        [
            os.path.join(BATCH_DIR, f)
            for f in os.listdir(BATCH_DIR)
            if re.match(r"B-\d+_picks\.json$", f)
        ]
    )
    for pf in picks_files:
        batch_id = os.path.basename(pf).split("_")[0]
        try:
            with open(pf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"WARN {pf}: {e}")
            continue
        picks = data.get("picks", []) if isinstance(data, dict) else data
        if not isinstance(picks, list):
            continue
        for p in picks:
            if not isinstance(p, dict):
                continue
            sid = (
                p.get("skill_id_homogeneity")
                or p.get("skill_id")
                or p.get("sid")
                or p.get("id")
            )
            fname = p.get("filename") or p.get("file") or p.get("path")
            if not sid and fname:
                m = re.search(r"SkillGraph_(\d+)", fname)
                if m:
                    sid = m.group(1)
            if sid:
                sid = str(sid)
                if sid not in learned:
                    learned[sid] = []
                if batch_id not in learned[sid]:
                    learned[sid].append(batch_id)
    return learned


def scan_inscope():
    """递归扫 in_scope 目录"""
    out = {}
    for cat, subpath in INSCOPE.items():
        full = os.path.join(ROOT, subpath)
        files = []
        for dirpath, _, fnames in os.walk(full):
            if any(ex in dirpath for ex in EXCLUDE_PARTS):
                continue
            for fn in fnames:
                if not fn.endswith(".json") or fn.endswith(".meta"):
                    continue
                if not fn.startswith("SkillGraph_"):
                    continue
                m = re.match(r"SkillGraph_([\w]+?)(?:[【\[]|_|$)", fn)
                if not m:
                    continue
                sid = m.group(1)
                rel = os.path.relpath(dirpath, ROOT)
                files.append((sid, fn, rel))
        out[cat] = sorted(files)
    return out


def gen_markdown(inscope, learned):
    cat_stats = {}
    total = 0
    for cat, files in inscope.items():
        L = sum(1 for sid, _, _ in files if sid in learned)
        cat_stats[cat] = (len(files), L, len(files) - L)
        total += len(files)
    total_L = sum(s[1] for s in cat_stats.values())
    total_U = sum(s[2] for s in cat_stats.values())

    lines = []
    lines.append("---")
    lines.append("type: 学习清单 / 索引")
    lines.append(
        "summary: 521 in_scope 学习样本已学/未学全清单 / 每批 COMMIT 后由 curator 自动 patch / Boot 段必读"
    )
    lines.append(f"total_inscope: {total}")
    lines.append(f"total_learned: {total_L}")
    lines.append(f"total_unlearned: {total_U}")
    lines.append(f"progress_pct: {100*total_L/total:.1f}")
    lines.append("tags: [学习清单, 索引, 已学未学]")
    lines.append("---")
    lines.append("")
    lines.append("# 学习清单（已学 / 未学全索引）")
    lines.append("")
    lines.append(
        "> 本文件 = SkillAI mental_model bootstrap 学习的**全样本索引**。"
    )
    lines.append(
        "> **谁来维护**：每批 fast-path COMMIT 后由 curator Mode B 自动 patch（守则强制 / [CLAUDE.local.md §AI 主动沉淀守则](../../../CLAUDE.local.md)）。"
    )
    lines.append(
        '> **如何使用**：用户问"还有多少没学/学过 XX 没"时，AI 直接读本文件回答。'
    )
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append("| 维度 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| in_scope 总数（path-level fs 真扫）| **{total}** |")
    lines.append(f"| 已学 | **{total_L}**（{100*total_L/total:.1f}%）|")
    lines.append(f"| 未学 | **{total_U}**（{100*total_U/total:.1f}%）|")
    lines.append("")
    lines.append("## 学习范围根目录")
    lines.append("")
    lines.append("```")
    lines.append("<<SKILLGRAPH_JSONS_ROOT>>")
    lines.append("```")
    lines.append("")
    lines.append("**排除规则**：`废弃` / `AIGen` / `AIGC` 路径不进 in_scope。")
    lines.append("")
    lines.append("## 按类别清单")
    lines.append("")

    for cat, files in inscope.items():
        n, L, U = cat_stats[cat]
        lines.append(f"### {cat} ({n} 个 / 已学 {L} / 未学 {U})")
        lines.append("")
        if not files:
            lines.append("_无文件_")
            lines.append("")
            continue
        if U == 0:
            lines.append("**全员已学** ✓")
            lines.append("")
            lines.append("<details><summary>展开看全 ID</summary>")
            lines.append("")
            for sid, fname, _ in files:
                batches = ",".join(learned.get(sid, []))
                lines.append(f"- ✓ `{sid}` {fname} _({batches})_")
            lines.append("")
            lines.append("</details>")
            lines.append("")
        else:
            lines.append("| 状态 | ID | 文件名 | 批次 |")
            lines.append("|------|----|----|------|")
            for sid, fname, _ in files:
                if sid in learned:
                    batches = ",".join(learned[sid])
                    lines.append(f"| ✓ | `{sid}` | {fname} | {batches} |")
                else:
                    lines.append(f"| ⏸ | `{sid}` | {fname} | _未学_ |")
            lines.append("")

    lines.append("## 未学样本速查（按类别）")
    lines.append("")
    lines.append("| 类别 | 未学 ID 列表 |")
    lines.append("|------|-------------|")
    for cat, files in inscope.items():
        unlearned = [(sid, fname) for sid, fname, _ in files if sid not in learned]
        if not unlearned:
            continue
        ids = " / ".join(f"`{sid}`" for sid, _ in unlearned)
        lines.append(f"| {cat} | {ids} |")
    lines.append("")

    lines.append("## 维护守则")
    lines.append("")
    lines.append(
        "1. **自动更新**：每批 fast-path COMMIT 后 / curator Mode B 必须重跑本目录 [_aggregate_learning_inventory.py](batch_buffer/_aggregate_learning_inventory.py) → 覆写本文件 / 不需要用户提醒。"
    )
    lines.append(
        '2. **手动查询**：用户问"还有多少没学"/"XX 学过没"时 AI 直接读本文件 / 不要再扫 fs。'
    )
    lines.append(
        "3. **范围修订**：如学习范围变化（如新增子目录入 in_scope）/ 走用户拍板升格通道修订本文件 + CLAUDE.local.md §本版学习范围。"
    )
    lines.append(
        "4. **rule_2 严守**：本文件 path / sid 列表是 fs 真扫 ground truth / 历史快照不保留作思想史（属索引层 / 不是不变量层 / 不适用 rule_2）。"
    )
    lines.append("")

    return "\n".join(lines), {
        "total_inscope": total,
        "total_learned": total_L,
        "total_unlearned": total_U,
        "cat_stats": cat_stats,
    }


def main():
    print(f"扫 picks.json...")
    learned = aggregate_learned()
    print(f"已学 sid 总数: {len(learned)}")

    print(f"递归扫 in_scope...")
    inscope = scan_inscope()
    total = sum(len(v) for v in inscope.values())
    print(f"in_scope 总数: {total}")

    print(f"生成 markdown...")
    md, stats = gen_markdown(inscope, learned)

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ 已覆写 {OUT_MD}")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "inscope_dirs": INSCOPE,
                "exclude_parts": EXCLUDE_PARTS,
                "inscope_files": {k: [list(t) for t in v] for k, v in inscope.items()},
                "learned_sids": learned,
                **stats,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"✅ 已覆写 {OUT_JSON}")

    print(f"\n📊 进度: {stats['total_learned']}/{stats['total_inscope']} = {100*stats['total_learned']/stats['total_inscope']:.1f}%")
    print(f"   未学: {stats['total_unlearned']}")


if __name__ == "__main__":
    main()
