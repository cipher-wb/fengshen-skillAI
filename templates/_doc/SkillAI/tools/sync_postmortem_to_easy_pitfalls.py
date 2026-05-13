#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sync_postmortem_to_easy_pitfalls.py — v2.5 自动同步工具

把 postmortem/*.md 里"已 accepted"的 PostMortem 关键规则汇总到 docs/易错点速查.md，
避免最近的 PostMortem 教训漏到团队公开版。

v2.5（2026-05-09 由 ralph US-004 加入）：同一遍同步时，会把每条新 postmortem 作为
pending triage 行追加到 mental_model/learning_log.md §6 失败归因表，等 curator 后续
归因。已在表里出现过的 title（按"任务"列文本）不会重复追加，幂等。

工作流：
  1. 扫 postmortem/*.md，跳过 README.md 和 *.rejected.md / *.merged-into-*.md
  2. 解析每篇的 frontmatter（status / sediment_target / related_skill）+ 标题 + 决策
  3. 在 docs/易错点速查.md 末尾的 "## 自动同步区（来自 PostMortem 入库）" 章节
     维护一份索引 + 每条 PostMortem 的精简摘要（hashable 标记，重复运行可幂等更新）
  4. 不删除人工写的章节，只在自动同步区域内增删
  5. 同步同时把 pending 条目追加到 mental_model/learning_log.md §6
     失败归因表（在 §7 之前）— 只追加新 title，不动旧行

用法：
  python doc/SkillAI/tools/sync_postmortem_to_easy_pitfalls.py
  python doc/SkillAI/tools/sync_postmortem_to_easy_pitfalls.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
POSTMORTEM_DIR = PROJECT_ROOT / "doc" / "SkillAI" / "postmortem"
EASY_PITFALLS_PATH = PROJECT_ROOT / "doc" / "SkillAI" / "docs" / "易错点速查.md"
LEARNING_LOG_PATH = PROJECT_ROOT / "doc" / "SkillAI" / "mental_model" / "learning_log.md"

AUTO_SECTION_BEGIN = "<!-- AUTO_SYNC_BEGIN — 由 sync_postmortem_to_easy_pitfalls.py 维护，勿手改 -->"
AUTO_SECTION_END = "<!-- AUTO_SYNC_END -->"

# learning_log.md §6 表头识别（用于幂等追加）
LEARNING_LOG_SEC6_HEADER_RE = re.compile(r"^## §6 ", re.MULTILINE)
LEARNING_LOG_SEC7_HEADER_RE = re.compile(r"^## §7 ", re.MULTILINE)


def _parse_frontmatter_and_body(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, parts[2]


def _extract_h1_title(body: str) -> str:
    """提取第一个 # 标题"""
    m = re.search(r"^# (.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else "(无标题)"


def _extract_section(body: str, section_title: str) -> str:
    """提取 ## section_title 章节的内容（到下一个 ## 或文件结束）"""
    pat = re.compile(rf"^## {re.escape(section_title)}\s*$(.*?)(?=^## |\Z)",
                     re.MULTILINE | re.DOTALL)
    m = pat.search(body)
    if not m:
        return ""
    return m.group(1).strip()


def _slugify_proposal_id(filename: str) -> str:
    """从文件名提取 proposal_id (e.g. 2026-05-08-019)"""
    m = re.match(r"^(\d{4}-\d{2}-\d{2}-\d+)", filename)
    return m.group(1) if m else filename


def collect_postmortems() -> list[dict]:
    """扫 postmortem/*.md，收集 accepted 的条目"""
    if not POSTMORTEM_DIR.exists():
        print(f"❌ {POSTMORTEM_DIR} 不存在", file=sys.stderr)
        return []
    items = []
    for p in sorted(POSTMORTEM_DIR.glob("*.md")):
        name = p.name
        # 跳过索引、被拒绝、被合并的
        if name == "README.md":
            continue
        if ".rejected." in name or ".merged-into-" in name:
            continue
        text = p.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter_and_body(text)
        status = (meta.get("status") or "").lower()
        if status not in ("accepted", "partial", ""):
            continue
        title = _extract_h1_title(body)
        # 提取关键章节
        decision = _extract_section(body, "决策")
        manifest = _extract_section(body, "现象") or _extract_section(body, "现象（用户实测后反馈）")
        root_cause = _extract_section(body, "根因")
        fix = _extract_section(body, "修法（已落地）") or _extract_section(body, "修法")
        items.append({
            "proposal_id": _slugify_proposal_id(name),
            "filename": name,
            "title": title,
            "status": status or "accepted",
            "related_skill": meta.get("related_skill", ""),
            "ir_version": meta.get("ir_version", ""),
            "sediment_target": meta.get("sediment_target", []) or [],
            "decision": decision[:200],
            "manifest": manifest[:300],
            "root_cause": root_cause[:300],
            "fix": fix[:400],
        })
    return items


def render_auto_section(items: list[dict]) -> str:
    """生成自动同步区域的 markdown 内容"""
    if not items:
        return f"{AUTO_SECTION_BEGIN}\n\n_暂无已入库 PostMortem。_\n\n{AUTO_SECTION_END}"

    lines = [AUTO_SECTION_BEGIN, ""]
    lines.append("> 本节由 `tools/sync_postmortem_to_easy_pitfalls.py` 自动维护。"
                 "更新方式：写新 PostMortem → 跑此脚本。")
    lines.append("")

    # 索引表
    lines.append(f"### 自动同步索引（{len(items)} 条 PostMortem）")
    lines.append("")
    lines.append("| 编号 | 标题 | 关联技能 | IR 版本 | 详情 |")
    lines.append("|------|------|----------|---------|------|")
    for it in items:
        # 标题里取 # 后的部分简化
        title_short = it["title"].replace("**", "").replace("—", " ").strip()[:60]
        sk = (it.get("related_skill") or "").replace("（", "(")[:30]
        ver = it.get("ir_version", "")
        lines.append(f"| [{it['proposal_id']}](../postmortem/{it['filename']}) "
                     f"| {title_short} "
                     f"| {sk} "
                     f"| {ver} "
                     f"| 见下方详情 |")
    lines.append("")

    # 详情段落
    for it in items:
        lines.append(f"### {it['proposal_id']} — {it['title'].replace('**','').strip()}")
        lines.append("")
        if it.get("related_skill"):
            lines.append(f"**关联**：{it['related_skill']}")
        if it.get("ir_version"):
            lines.append(f"**IR 版本**：{it['ir_version']}")
        lines.append("")

        if it["manifest"]:
            lines.append("**现象 / 触发场景**：")
            lines.append(it["manifest"])
            lines.append("")

        if it["root_cause"]:
            lines.append("**根因（一句话）**：")
            lines.append(it["root_cause"][:200])
            lines.append("")

        if it["fix"]:
            lines.append("**修法（关键点）**：")
            lines.append(it["fix"][:300])
            lines.append("")

        if it["sediment_target"]:
            lines.append("**沉淀位置**：")
            for s in it["sediment_target"]:
                lines.append(f"- `{s}`")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append(AUTO_SECTION_END)
    return "\n".join(lines)


def update_easy_pitfalls(items: list[dict], dry_run: bool = False) -> bool:
    """把 auto section 写入 易错点速查.md。返回是否有变更。"""
    if not EASY_PITFALLS_PATH.exists():
        print(f"❌ {EASY_PITFALLS_PATH} 不存在", file=sys.stderr)
        return False

    original = EASY_PITFALLS_PATH.read_text(encoding="utf-8")
    new_section = render_auto_section(items)

    # 如果文件里已有 AUTO 区块，替换它；否则追加
    if AUTO_SECTION_BEGIN in original and AUTO_SECTION_END in original:
        pat = re.compile(
            re.escape(AUTO_SECTION_BEGIN) + r".*?" + re.escape(AUTO_SECTION_END),
            re.DOTALL,
        )
        updated = pat.sub(new_section, original)
    else:
        # 追加在文件末尾，保留人工内容
        sep = "" if original.endswith("\n") else "\n"
        updated = f"{original}{sep}\n---\n\n{new_section}\n"

    if updated == original:
        return False

    if not dry_run:
        EASY_PITFALLS_PATH.write_text(updated, encoding="utf-8")
    return True


def _normalize_title(raw: str) -> str:
    """归一化标题：去掉 markdown 加粗、首尾空白、行内 `|`（避免破坏表格）。"""
    return raw.replace("**", "").replace("|", "／").strip()


def _extract_existing_titles_in_log_sec6(text: str) -> tuple[set[str], int, int]:
    """从 learning_log.md 中扫 §6 段，返回 (已有 title 集, sec6 起始 idx, sec7 起始 idx)。

    sec7 起始 idx：若没有 §7 标题，返回 len(text)。已有 title 取自表格"任务"列（第二列）。
    """
    m6 = LEARNING_LOG_SEC6_HEADER_RE.search(text)
    if not m6:
        return set(), -1, -1
    sec6_start = m6.start()
    m7 = LEARNING_LOG_SEC7_HEADER_RE.search(text, pos=m6.end())
    sec7_start = m7.start() if m7 else len(text)

    sec6_block = text[sec6_start:sec7_start]
    existing: set[str] = set()
    for line in sec6_block.splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 2:
            continue
        first, second = cols[0], cols[1]
        # 跳过表头 / 分隔线 / 占位行
        if first.startswith("---") or second.startswith("---"):
            continue
        if first in ("日期", "Date", ""):
            continue
        if first.startswith("_") or "（待第一次失败后填充）" in first:
            continue
        existing.add(second)
    return existing, sec6_start, sec7_start


def _build_pending_triage_lines(items: list[dict],
                                existing_titles: set[str]) -> list[tuple[str, str]]:
    """为 collect_postmortems 出的 items 生成尚未在 §6 出现的 pending triage 行。

    返回 [(title, table_row_str), ...]。
    table_row_str 形如：
        | 2026-05-08 | <title> | (待 curator 归因) | (待) | pending_curator_triage |
    """
    out: list[tuple[str, str]] = []
    for it in items:
        title = _normalize_title(it.get("title", ""))
        if not title:
            continue
        if title in existing_titles:
            continue
        # 日期取 proposal_id 前 10 位（YYYY-MM-DD），失败则留空
        pid = it.get("proposal_id", "") or ""
        date = pid[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", pid) else ""
        row = (
            f"| {date} | {title} | (待 curator 归因) | (待) | "
            f"pending_curator_triage |"
        )
        out.append((title, row))
    return out


def update_learning_log_with_pending_triage(
    items: list[dict],
    dry_run: bool = False,
) -> tuple[bool, list[str]]:
    """把每条新 postmortem 追加到 learning_log.md §6 失败归因表（pending triage）。

    幂等：表里第二列（任务）已存在的 title 不再追加。
    返回 (是否有变更, 新追加的 title 列表)。
    """
    if not LEARNING_LOG_PATH.exists():
        print(f"⚠️ {LEARNING_LOG_PATH} 不存在，跳过 mental_model triage 同步",
              file=sys.stderr)
        return False, []

    text = LEARNING_LOG_PATH.read_text(encoding="utf-8")
    existing, sec6_start, sec7_start = _extract_existing_titles_in_log_sec6(text)
    if sec6_start < 0:
        print(f"⚠️ {LEARNING_LOG_PATH} 中未找到 ## §6 段，跳过", file=sys.stderr)
        return False, []

    pending = _build_pending_triage_lines(items, existing)
    if not pending:
        return False, []

    sec6_block = text[sec6_start:sec7_start]
    sec6_lines = sec6_block.splitlines()

    # 在表格的最后一个 `|` 行之后插入
    last_table_idx = -1
    for i, line in enumerate(sec6_lines):
        if line.startswith("|"):
            last_table_idx = i
    if last_table_idx == -1:
        print(f"⚠️ §6 段未找到表格行，跳过", file=sys.stderr)
        return False, []

    new_rows = [row for _, row in pending]
    new_sec6_lines = (
        sec6_lines[: last_table_idx + 1]
        + new_rows
        + sec6_lines[last_table_idx + 1:]
    )
    new_sec6_block = "\n".join(new_sec6_lines)
    # 保留尾换行（如果原 block 最后是换行）
    if sec6_block.endswith("\n") and not new_sec6_block.endswith("\n"):
        new_sec6_block += "\n"

    updated = text[:sec6_start] + new_sec6_block + text[sec7_start:]
    if updated == text:
        return False, []

    if not dry_run:
        LEARNING_LOG_PATH.write_text(updated, encoding="utf-8")

    return True, [title for title, _ in pending]


def main():
    parser = argparse.ArgumentParser(description="把 PostMortem 自动同步到易错点速查")
    parser.add_argument("--dry-run", action="store_true", help="只显示会改什么，不写文件")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

    items = collect_postmortems()
    print(f"扫到 {len(items)} 条 accepted PostMortem")
    for it in items:
        print(f"  [{it['proposal_id']}] {it['title'][:60]}")

    changed = update_easy_pitfalls(items, dry_run=args.dry_run)
    if changed:
        if args.dry_run:
            print(f"\n[dry-run] 会更新 {EASY_PITFALLS_PATH.relative_to(PROJECT_ROOT)}")
        else:
            print(f"\n✓ 已更新 {EASY_PITFALLS_PATH.relative_to(PROJECT_ROOT)}")
    else:
        print(f"\n（易错点速查无变更）")

    log_changed, new_titles = update_learning_log_with_pending_triage(
        items, dry_run=args.dry_run
    )
    if log_changed:
        if args.dry_run:
            print(f"\n[dry-run] 会向 {LEARNING_LOG_PATH.relative_to(PROJECT_ROOT)} "
                  f"§6 追加 {len(new_titles)} 行 pending triage：")
            for t in new_titles:
                print(f"  + {t}")
        else:
            print(f"\n✓ 已向 {LEARNING_LOG_PATH.relative_to(PROJECT_ROOT)} "
                  f"§6 追加 {len(new_titles)} 行 pending triage")
    else:
        print(f"\n（mental_model/learning_log.md §6 无新增 pending triage）")


if __name__ == "__main__":
    main()
