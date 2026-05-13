"""picker_v2.py — Bootstrap 学习 picker（学习范围 v2 强制白名单版本）

> **正式工具版本（v0.16 升正式 / 用户拍板 2026-05-11）**
> 累积证据：B-021 + B-022 + B-023 三连 0 嵌套漏判 / picker_v2.is_in_scope "path 任意位置含 '废弃' → 拒"通用规则覆盖嵌套黑名单稳定。
> 升正式前为 candidate 状态（v2.1 housekeeping #4 修复后累积 3/3 successful batches）/ v0.16 用户裁决升正式工具版本。

> **v2.3 升正式（用户拍板 2026-05-11 / housekeeping #7 落地）**：
> 新增 path 任意位置含 '弃用' 路径段 → 拒（与 housekeeping #4 '废弃' 嵌套黑名单同源同规则）。
> 触发：B-024 ~ B-032 累积观察 7 例 fs 真扫全集（100% 集中通用BUFF 子目录 / filename 含"弃用"如
> "通用BUFF_xxx_弃用.json" 形态）/ picker_v2 v2.2 漏判候选 10020 单例已学但其余 6 例 corpus 自动避开。
> 升正式后 v2.3 通用规则补齐：path 任意位置含 '弃用' → 拒（覆盖任何形态 / 与 '废弃' 通用规则同源）。
> 思想史保留：10020 已学样本保留作思想史，evidence_scope 标"范围内（picker_v2 v2.2 工程层）/
> 用户意图层应嵌套黑名单形态（housekeeping #7 修复后回溯）"。

> 用户裁决（2026-05-11）：本版只学 **宗门功法 + 心法 + 技能模板 = 521 样本**。
> 老技能可参考但不进 picker / 心法 = 只宗门心法（不含心法通诀）。
> 历史背景：B-017 R0 fail / spot-check 揭出 B-001~B-016 picker 按"段位均衡"选样 / 90 已学样本中仅 ~14 严格在范围内。

## 核心 enforcement（学习范围_v2.md §3 五条规则全部实施）

- Rule 1: `is_in_scope(path)` 白/黑名单严过滤
- Rule 2: 每个 pick 输出带 `in_scope_verdict` + `in_scope_evidence`
- Rule 3: 启动时**首先 grep 学习范围_v2.md 取白名单**（不硬编码 / 文件改了脚本自动跟）
- Rule 4: learned_set 也按 in_scope 过滤（范围外样本不算"已学"）
- Rule 5: 不再以"段位均衡"作为唯一选样标准（段位仅作白名单内分层指标）

## 使用方法

    python picker_v2.py --batch B-018 --n 10 --holdout 2 \
        --corpus doc/SkillAI/mental_model/batch_buffer/_corpus_scan_with_ids.json \
        --picks-glob 'doc/SkillAI/mental_model/batch_buffer/B-*_picks.json' \
        --scope-doc doc/SkillAI/mental_model/学习范围_v2.md \
        --out doc/SkillAI/mental_model/batch_buffer/B-018_picks.json

不提供 `--scope-doc` 时默认相对当前文件定位。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).parent
DEFAULT_SCOPE_DOC = HERE.parent / 'mental_model' / '学习范围_v2.md'


# ---------------------------------------------------------------------------
# Rule 3: 启动时 grep 学习范围_v2.md 取白/黑名单（文件改了脚本自动跟）
# ---------------------------------------------------------------------------


def load_scope_from_doc(scope_doc: Path) -> tuple[list[str], list[str], dict]:
    """从学习范围_v2.md §3 Rule 1 提取 WHITELIST + BLACKLIST_PREFIXES。

    返回 (whitelist, blacklist_prefixes, metadata)。
    解析逻辑：抓 Python code block 内的 `WHITELIST = [...]` + `BLACKLIST_PREFIXES = [...]`。
    """
    if not scope_doc.exists():
        raise FileNotFoundError(f"学习范围 doc 不存在: {scope_doc}")

    text = scope_doc.read_text(encoding='utf-8')

    # 抓 WHITELIST = [...] 内的字符串字面量
    whitelist: list[str] = []
    m = re.search(r'WHITELIST\s*=\s*\[(.*?)\]', text, re.DOTALL)
    if m:
        block = m.group(1)
        whitelist = re.findall(r"['\"]([^'\"]+?/)['\"]", block)

    blacklist_prefixes: list[str] = []
    m = re.search(r'BLACKLIST_PREFIXES\s*=\s*\[(.*?)\]', text, re.DOTALL)
    if m:
        block = m.group(1)
        blacklist_prefixes = re.findall(r"['\"]([^'\"]+?)['\"]", block)

    if not whitelist:
        raise RuntimeError(
            f"未能从 {scope_doc} 解析 WHITELIST。"
            f"请检查 §3 Rule 1 内 Python code block 是否含 WHITELIST = [...]。"
        )

    metadata = {
        'scope_doc': str(scope_doc),
        'scope_doc_mtime': scope_doc.stat().st_mtime,
        'whitelist_count': len(whitelist),
        'blacklist_count': len(blacklist_prefixes),
    }
    return whitelist, blacklist_prefixes, metadata


# ---------------------------------------------------------------------------
# Rule 1: is_in_scope() 严过滤（黑名单优先 + 白名单后判）
# ---------------------------------------------------------------------------


def normalize_path(path: str) -> str:
    """统一路径分隔符 + 去掉前缀（例如 Saves/Jsons/）。

    各 batch 的 corpus 字段 `path` 可能是相对 Saves/Jsons 的路径，也可能反斜杠 / 正斜杠混用。
    我们统一成正斜杠 + 找到第一个白名单顶层目录之前的部分截掉。
    """
    p = path.replace('\\', '/')
    # 学习范围白名单顶层目录前缀（最常见的几种）
    for top in ('宗门技能/', '技能模板/', '废弃（老技能）/', '法宝/', '坐骑技能/',
                '心法通诀/', '灵宠心法/', '秘境怪物词缀/', '战斗道具/', '怪物/',
                '卡牌/', '战斗流程/', '测试/', '特殊玩法/', 'BUFF/', '关卡模板/'):
        idx = p.find(top)
        if idx >= 0:
            return p[idx:]
    return p


def is_in_scope(path: str, whitelist: list[str], blacklist_prefixes: list[str]) -> tuple[bool, str, str]:
    """返回 (in_scope, verdict_label, evidence)。

    verdict_label:
        - 'WHITELIST_pass' 命中白名单且未踩黑名单
        - 'BLACKLIST_reject_废弃' 显式踩黑名单前缀
        - 'BLACKLIST_reject_nested_废弃' path 任意位置含 "废弃" 子目录（嵌套黑名单 / housekeeping #4 修复 / B-020 R0 引入）
        - 'BLACKLIST_reject_nested_弃用' path 任意位置含 "弃用" 子目录/文件名（嵌套黑名单 / housekeeping #7 修复 / v2.3 引入 / 用户拍板 2026-05-11）
        - 'OUT_OF_SCOPE' 既不在白名单也不在显式黑名单（默认拒）

    （AI 新增）housekeeping #4 修复（B-020 R0 揭出 / 305920 + 3019311 路径含
    "宗门技能/宗门心法/废弃（老心法）/" 嵌套黑名单形态 / picker_v2 v1 顶级前缀匹配漏判 /
    改用 "path 任意位置含 '废弃' → 拒" 通用规则）

    （AI 修改 v2.3 / housekeeping #7 修复 / 用户拍板 2026-05-11）
    通用 BUFF 子目录中存在大量"弃用"形态（如 "通用BUFF_xxx_弃用.json" / 100% 集中
    通用BUFF 子目录 / 7 例 fs 真扫全集累积 B-024 ~ B-032）/ picker_v2 v2.2 漏判候选 /
    新增 "path 任意位置含 '弃用' → 拒" 通用规则（与 '废弃' 通用规则同源）。
    """
    norm = normalize_path(path)

    # 黑名单优先（防误判：白名单 '宗门技能/' 会误吞 '宗门技能/废弃（老技能）/'）
    # housekeeping #4 嵌套黑名单通用规则：path 任意位置含 "废弃" 路径段 → 拒
    # （'废弃' 出现在嵌套子目录如 "宗门技能/宗门心法/废弃（老心法）/" 不再漏判）
    if '废弃' in norm:
        return False, 'BLACKLIST_reject_nested_废弃', (
            f"norm_path '{norm}' contains '废弃' (nested 黑名单 / housekeeping #4 修复 / "
            f"path 任意位置含'废弃' 路径段 → 拒)"
        )

    # housekeeping #7 嵌套黑名单通用规则（v2.3 / 用户拍板 2026-05-11）：
    # path 任意位置含 "弃用" 路径段或文件名 → 拒
    # （通用BUFF 子目录大量"弃用"形态如 "通用BUFF_xxx_弃用.json" / 与"废弃"通用规则同源）
    if '弃用' in norm:
        return False, 'BLACKLIST_reject_nested_弃用', (
            f"norm_path '{norm}' contains '弃用' (nested 黑名单 / housekeeping #7 修复 v2.3 / "
            f"path 任意位置含'弃用' 路径段或文件名 → 拒 / 与 housekeeping #4 '废弃' 通用规则同源)"
        )

    for bl in blacklist_prefixes:
        if norm.startswith(bl):
            return False, f'BLACKLIST_reject_{bl}', f"norm_path '{norm}' startswith '{bl}' (黑名单前缀)"

    for wl in whitelist:
        if norm.startswith(wl):
            return True, 'WHITELIST_pass', f"norm_path '{norm}' startswith '{wl}' (白名单前缀)"

    return False, 'OUT_OF_SCOPE', f"norm_path '{norm}' 不命中任何白名单前缀"


# ---------------------------------------------------------------------------
# Rule 4: learned_set 也按 in_scope 过滤
# ---------------------------------------------------------------------------


# housekeeping #5 修补（v2.2 / B-029 / B-028 partial 揭出）：
# B-001~B-014 早期 picks.json 字段不齐 / 老版 build_learned_set 只认 picks[] + skill_id
# / 遗漏 30+ 样本（B-012 6 例为 30225003/30122001/30214001/30121000/30524001/30533001
# B-028 D-44_sub_namespace_enforce partial 直接证据）。
# 兼容矩阵 v2.2（已 grep 历史所有 picks.json 字段形态）：
#
# | 批次       | picks 容器                                        | id 字段                          | path 字段           |
# |------------|--------------------------------------------------|----------------------------------|---------------------|
# | B-001      | data['picks'][]                                  | _id / filename 提取               | path / filename     |
# | B-002      | data['picks'][]                                  | sample_id                        | path                |
# | B-003      | data['picks'][]                                  | id                               | path / filename     |
# | B-004      | data 顶级 dict 'pickN_xxx' 多键                   | skill_id                         | real_path           |
# | B-005      | data 是 LIST                                     | filename 提取                    | file_full / file    |
# | B-006      | data['samples'][]                                | sample_id / metadata.SkillID     | path / filename     |
# | B-007      | data['picks'][]                                  | sid                              | path                |
# | B-008      | data['picks'][]                                  | sid                              | path                |
# | B-010      | data['training_picks'][] + data['holdout_pick']  | id                               | filename            |
# | B-012      | data['training_samples'][] + data['holdout_sample'] | skill_id                       | filename            |
# | B-013/14   | data['picks'][].sample.{...}                     | filename 提取 (skill_id 为 None) | sample.path         |
# | B-015+     | data['picks'][]                                  | skill_id                         | path / filename     |


_SKILL_ID_RE = re.compile(r'SkillGraph_(\d{4,12})')


def _extract_id_from_filename(filename: str) -> str:
    """从 SkillGraph_30122001xxx.json 形态提取 ID（兜底，B-001/B-005/B-013/B-014 用）。"""
    if not filename:
        return ''
    m = _SKILL_ID_RE.search(filename)
    return m.group(1) if m else ''


def _normalize_pick_entry(raw: dict, fallback_filename: str = '') -> tuple[str, str]:
    """兼容多版本字段 → 返回 (skill_id, path)。

    优先级：skill_id > id > sid > sample_id > _id > metadata.SkillID > filename 提取。
    path 优先级：path > real_path > file_full > file > filename。

    （AI 修改 housekeeping #5 修补 v2.2 / B-029）
    sid 含 '-T' / '-H' role 后缀（B-002 形态）/ 或非纯数字 → 走 filename regex 提纯
    保证 learned_set ID 全部为纯数字（与 corpus _extracted_id 对齐 / 防 B-029+ 比对污染）
    """
    sid = ''
    for key in ('skill_id', 'id', 'sid', 'sample_id', '_id'):
        v = raw.get(key)
        if v is not None and str(v).lower() != 'none' and str(v) != '':
            sid = str(v)
            break
    if not sid and isinstance(raw.get('metadata'), dict):
        v = raw['metadata'].get('SkillID')
        if v is not None and str(v).lower() != 'none' and str(v) != '':
            sid = str(v)

    pp = ''
    for key in ('path', 'real_path', 'file_full', 'file', 'filename'):
        v = raw.get(key)
        if v:
            pp = str(v)
            break
    if not pp and fallback_filename:
        pp = fallback_filename

    # 兜底 1：sid 非纯数字（B-002 '146003779-T' / '175_0001-T' 形态） → filename 提纯
    if sid and not sid.isdigit():
        # 先尝试 sid 自身取纯数字前缀（'146003779-T' → '146003779' / '175_0001-T' → '175'）
        m = re.match(r'^(\d{3,12})', sid)
        if m:
            sid = m.group(1)
        else:
            for key in ('filename', 'file', 'path', 'file_full', 'real_path'):
                v = raw.get(key)
                if v:
                    extracted = _extract_id_from_filename(str(v))
                    if extracted:
                        sid = extracted
                        break

    # 兜底 2：无 sid 任何字段 → filename 提取
    if not sid:
        for key in ('filename', 'file', 'path', 'file_full', 'real_path'):
            v = raw.get(key)
            if v:
                extracted = _extract_id_from_filename(str(v))
                if extracted:
                    sid = extracted
                    break

    return sid, pp


def _flatten_legacy_picks_dict(data: dict) -> list[dict]:
    """处理 B-004 顶级 dict 形态（'pick1_xxx' / 'pick2_xxx' / ...）+ B-013/14 嵌套 sample 形态。

    返回打平后的 pick entries 列表。
    """
    entries: list[dict] = []

    # 容器优先级（多版本兼容）
    for container_key in ('picks', 'samples', 'training_picks', 'training_samples'):
        v = data.get(container_key)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    # B-013/B-014: pick 包含 sample 嵌套
                    if 'sample' in item and isinstance(item['sample'], dict):
                        merged = dict(item['sample'])
                        # 继承 role 等顶级字段
                        for top_k in ('role', 'bucket'):
                            if top_k in item and top_k not in merged:
                                merged[top_k] = item[top_k]
                        entries.append(merged)
                    else:
                        entries.append(item)

    # 单值字段（B-010 holdout_pick / B-012 holdout_sample）
    for single_key in ('holdout_pick', 'holdout_sample'):
        v = data.get(single_key)
        if isinstance(v, dict):
            entries.append(v)

    # B-004 顶级 'pickN_xxx' 形态（无 picks 容器）
    if not entries:
        for k, v in data.items():
            if isinstance(v, dict) and isinstance(k, str) and k.lower().startswith('pick'):
                entries.append(v)

    return entries


def build_learned_set(picks_glob_patterns: Iterable[str], whitelist: list[str],
                      blacklist_prefixes: list[str],
                      corpus_id_to_path: dict | None = None) -> tuple[set[str], dict]:
    """从历史 picks_*.json 抽 skill_id；按 in_scope 过滤后入 learned_set。

    返回 (learned_in_scope_set, stats_dict).
    范围外的样本计数到 stats_dict.out_of_scope_skipped 但不入 learned_set。

    （AI 修改 / housekeeping #5 修补 v2.2 / B-029 / B-028 partial 揭出）
    多版本字段兼容：见 _normalize_pick_entry + _flatten_legacy_picks_dict。
    新增 corpus_id_to_path 兜底参数：B-010/B-012 等 path=None 只有 filename 形态
    通过 corpus skill_id → real path 反查补全。
    """
    learned: set[str] = set()
    raw_count = 0
    in_scope_count = 0
    out_of_scope_count = 0
    by_verdict: dict[str, int] = {}
    out_of_scope_examples: list[dict] = []
    corpus_lookup_used = 0
    # housekeeping #5 修补诊断字段：按 batch_file 统计兼容性
    by_source_batch: dict[str, dict] = {}

    for pattern in picks_glob_patterns:
        for picks_path in sorted(glob.glob(pattern)):
            base = os.path.basename(picks_path)
            batch_stat = {'parsed_entries': 0, 'in_scope_added': 0, 'out_of_scope': 0,
                          'unresolved_no_sid': 0, 'corpus_lookup_used': 0}
            try:
                with open(picks_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                batch_stat['load_error'] = str(e)
                by_source_batch[base] = batch_stat
                continue

            # housekeeping #5 修补：多种容器形态打平 + B-005 LIST 形态
            entries: list[dict] = []
            if isinstance(data, dict):
                entries = _flatten_legacy_picks_dict(data)
            elif isinstance(data, list):
                # B-005 LIST 形态
                for item in data:
                    if isinstance(item, dict):
                        entries.append(item)

            batch_stat['parsed_entries'] = len(entries)

            for p in entries:
                sid, pp = _normalize_pick_entry(p)
                if not sid:
                    batch_stat['unresolved_no_sid'] += 1
                    continue

                # housekeeping #5 修补 v2.2 新增：path 为空 / 只有 filename 形态
                # 通过 corpus skill_id → real path 反查补全（B-010 / B-012 兜底）
                if corpus_id_to_path is not None:
                    norm_for_check = normalize_path(pp)
                    looks_filename_only = (
                        not pp
                        or (norm_for_check == pp.replace('\\', '/') and '/' not in norm_for_check)
                    )
                    if looks_filename_only:
                        # 用 corpus 反查（int + str 双向兼容）
                        real_path = corpus_id_to_path.get(sid) or corpus_id_to_path.get(int(sid)) if sid.isdigit() else None
                        if real_path:
                            pp = real_path
                            batch_stat['corpus_lookup_used'] += 1
                            corpus_lookup_used += 1

                raw_count += 1
                in_scope, verdict, _ev = is_in_scope(pp, whitelist, blacklist_prefixes)
                by_verdict[verdict] = by_verdict.get(verdict, 0) + 1
                if in_scope:
                    learned.add(sid)
                    in_scope_count += 1
                    batch_stat['in_scope_added'] += 1
                else:
                    out_of_scope_count += 1
                    batch_stat['out_of_scope'] += 1
                    if len(out_of_scope_examples) < 20:
                        out_of_scope_examples.append({
                            'skill_id': sid,
                            'path': pp,
                            'verdict': verdict,
                            'source_batch_file': base,
                        })
            by_source_batch[base] = batch_stat

    stats = {
        'raw_picks_scanned': raw_count,
        'in_scope_picks_added_to_learned': in_scope_count,
        'out_of_scope_picks_skipped': out_of_scope_count,
        'by_verdict': by_verdict,
        'out_of_scope_examples_first_20': out_of_scope_examples,
        # housekeeping #5 修补诊断
        'housekeeping_5_repair': {
            'algorithm_version': 'v2.2',
            'multi_field_compat': [
                'skill_id', 'id', 'sid', 'sample_id', '_id',
                'metadata.SkillID', 'filename_regex_SkillGraph_(\\d+)'
            ],
            'multi_container_compat': [
                'picks[]', 'samples[]', 'training_picks[]', 'training_samples[]',
                'holdout_pick', 'holdout_sample',
                'top-level pickN_xxx dict (B-004)',
                'LIST root (B-005)',
                'picks[].sample nested (B-013/14)',
            ],
            'corpus_lookup_filename_only_used': corpus_lookup_used,
            'by_source_batch': by_source_batch,
        },
    }
    return learned, stats


# ---------------------------------------------------------------------------
# Rule 5: 选样 — 段位仅作白名单内分层指标（不再做唯一标准）
# ---------------------------------------------------------------------------


WHITELIST_SUBCAT_NORM = {
    '宗门技能/木宗门技能/': '宗门-木',
    '宗门技能/火宗门技能/': '宗门-火',
    '宗门技能/金宗门技能/': '宗门-金',
    '宗门技能/水宗门技能/': '宗门-水',
    '宗门技能/土宗门技能/': '宗门-土',
    '宗门技能/BD标签/': '宗门标签-BD',
    '宗门技能/宗门标签/': '宗门标签-宗门',
    '宗门技能/通用BUFF/': '宗门标签-通用BUFF',
    '宗门技能/其他（有用）/': '宗门标签-其他有用',
    '宗门技能/宗门心法/': '宗门心法',
    '技能模板/伤害/': '模板-伤害',
    '技能模板/功能/': '模板-功能',
    '技能模板/单位/': '模板-单位',
    '技能模板/子弹/': '模板-子弹',
    '技能模板/技能/': '模板-技能',
    '技能模板/数值/': '模板-数值',
}


def whitelist_subcat_of(norm_path: str) -> str:
    """在白名单内进一步分层（用于选样多样性，不构成唯一标准）。"""
    for prefix, label in WHITELIST_SUBCAT_NORM.items():
        if norm_path.startswith(prefix):
            return label
    return '未分类(白名单内)'


def pick_samples(corpus_samples: list[dict],
                 learned: set[str],
                 whitelist: list[str],
                 blacklist_prefixes: list[str],
                 n_train: int,
                 n_holdout: int,
                 seed: int = 42) -> tuple[list[dict], dict]:
    """选 n_train + n_holdout 个未学且 in_scope 的样本。

    选样策略（替代旧"段位均衡"）：
        1. in_scope=True 严过滤
        2. 未学过（不在 learned set）
        3. 按 whitelist_subcat 分层（保证子分类多样）
        4. 每个 subcat 内按 node_count percentile 分散（保留旧"节点数分层"作为辅助）
        5. 段位标签仅作 metadata 透出，不参与选样硬约束
    """
    rng = random.Random(seed)

    # 1) 候选池 = 严过滤 + 未学
    pool_by_subcat: dict[str, list[dict]] = {}
    for s in corpus_samples:
        sid = s.get('_extracted_id')
        if not sid:
            continue
        pp = s.get('path', '') or s.get('filename', '')
        in_scope, verdict, _ev = is_in_scope(pp, whitelist, blacklist_prefixes)
        if not in_scope:
            continue
        if str(sid) in learned:
            continue
        norm = normalize_path(pp)
        subcat = whitelist_subcat_of(norm)
        pool_by_subcat.setdefault(subcat, []).append(s)

    total_pool = sum(len(v) for v in pool_by_subcat.values())

    # 2) 配额：每个 subcat 至少 1（如果池不空 / 配额 ≤ N），剩余按池规模占比分配
    subcats_with_pool = [k for k, v in pool_by_subcat.items() if v]
    total_needed = n_train + n_holdout
    quotas: dict[str, int] = {k: 0 for k in subcats_with_pool}

    if len(subcats_with_pool) <= total_needed:
        for k in subcats_with_pool:
            quotas[k] = 1

    # 剩余按池规模占比
    assigned = sum(quotas.values())
    remaining = total_needed - assigned
    if remaining > 0 and total_pool > 0:
        proportions = sorted(
            ((k, len(pool_by_subcat[k]) / total_pool) for k in subcats_with_pool),
            key=lambda kv: -kv[1],
        )
        for k, prop in proportions:
            if remaining <= 0:
                break
            add = max(1, int(round(prop * remaining)))
            add = min(add, len(pool_by_subcat[k]) - quotas[k])
            quotas[k] += add
            remaining -= add
        # 兜底：还有剩余就轮询补
        i = 0
        while remaining > 0 and any(len(pool_by_subcat[k]) > quotas[k] for k in subcats_with_pool):
            k = subcats_with_pool[i % len(subcats_with_pool)]
            if len(pool_by_subcat[k]) > quotas[k]:
                quotas[k] += 1
                remaining -= 1
            i += 1

    # 3) 在每个 subcat 内按 node_count percentile 分层选
    picks: list[dict] = []
    for subcat, q in quotas.items():
        if q <= 0:
            continue
        pool = sorted(pool_by_subcat[subcat], key=lambda s: s.get('node_count', 0))
        n_pool = len(pool)
        for i in range(q):
            if i >= n_pool:
                break
            pct = (i + 0.5) / q if q > 0 else 0.5
            idx = max(0, min(n_pool - 1, int(n_pool * pct)))
            # 避免重复
            attempts = 0
            while pool[idx].get('_extracted_id') in [int(p['skill_id']) if str(p['skill_id']).isdigit() else p['skill_id'] for p in picks] and attempts < 5:
                idx = (idx + 1) % n_pool
                attempts += 1
            s = pool[idx]
            pp = s.get('path', '') or s.get('filename', '')
            in_scope, verdict, evidence = is_in_scope(pp, whitelist, blacklist_prefixes)
            picks.append({
                'skill_id': str(s['_extracted_id']),
                'role': 'train',  # 先全部 train / 末尾再划 holdout
                'whitelist_subcat': subcat,
                'category_dir': s.get('category_dir', ''),
                'sub_category': s.get('sub_category', ''),
                'node_count': s.get('node_count', 0),
                'filename': s.get('filename', ''),
                'path': pp,
                'in_scope_verdict': verdict,        # Rule 2 必带
                'in_scope_evidence': evidence,      # Rule 2 必带
            })

    # 4) 末尾 n_holdout 个改 holdout（random shuffle 后取最末）
    rng.shuffle(picks)
    if n_holdout > 0 and len(picks) > n_holdout:
        for p in picks[-n_holdout:]:
            p['role'] = 'holdout'

    stats = {
        'pool_total_in_scope_unlearned': total_pool,
        'pool_by_subcat': {k: len(v) for k, v in pool_by_subcat.items()},
        'quotas_assigned': quotas,
        'picked_count': len(picks),
        'requested_count': total_needed,
    }
    return picks, stats


# ---------------------------------------------------------------------------
# 自检：所有 pick 必须 in_scope_verdict == 'WHITELIST_pass'
# ---------------------------------------------------------------------------


def self_check_picks(picks: list[dict]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for p in picks:
        if p.get('in_scope_verdict') != 'WHITELIST_pass':
            errors.append(
                f"pick skill_id={p.get('skill_id')} path={p.get('path')} "
                f"verdict={p.get('in_scope_verdict')} 违反 Rule 1（不在白名单 / 必须排除）"
            )
        for required in ('in_scope_verdict', 'in_scope_evidence'):
            if required not in p:
                errors.append(f"pick skill_id={p.get('skill_id')} 缺字段 {required}（违反 Rule 2）")
    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description='Bootstrap 学习 picker v2（学习范围 v2 强制白名单）')
    parser.add_argument('--batch', required=True, help='批次号，如 B-018')
    parser.add_argument('--n', type=int, default=10, help='总样本数（train + holdout）')
    parser.add_argument('--holdout', type=int, default=2, help='holdout 数量')
    parser.add_argument('--corpus', required=True, help='_corpus_scan_with_ids.json 路径')
    parser.add_argument('--picks-glob', required=True, action='append',
                        help='历史 picks.json glob 模式（可多次）')
    parser.add_argument('--scope-doc', default=str(DEFAULT_SCOPE_DOC),
                        help='学习范围_v2.md 路径（默认 mental_model/学习范围_v2.md）')
    parser.add_argument('--out', required=True, help='输出 picks.json 路径')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    n_train = args.n - args.holdout
    if n_train <= 0:
        print(f'ERROR: n_train={n_train} <= 0', file=sys.stderr)
        sys.exit(2)

    # Rule 3: 启动首先 grep 学习范围_v2.md
    scope_doc = Path(args.scope_doc)
    whitelist, blacklist_prefixes, scope_meta = load_scope_from_doc(scope_doc)
    print(f'[picker_v2] loaded WHITELIST ({len(whitelist)}) + BLACKLIST_PREFIXES ({len(blacklist_prefixes)}) from {scope_doc}')

    # Load corpus
    with open(args.corpus, 'r', encoding='utf-8') as f:
        corpus = json.load(f)
    samples = corpus['samples']

    # housekeeping #5 修补 v2.2：构建 id → real_path 映射给 build_learned_set 兜底
    corpus_id_to_path: dict = {}
    for s in samples:
        sid = s.get('_extracted_id')
        pp = s.get('path', '') or s.get('filename', '')
        if sid and pp:
            corpus_id_to_path[str(sid)] = pp
            corpus_id_to_path[sid] = pp  # int 版本

    # Rule 4: learned set 按 in_scope 过滤
    learned, learned_stats = build_learned_set(args.picks_glob, whitelist, blacklist_prefixes,
                                               corpus_id_to_path=corpus_id_to_path)
    print(f'[picker_v2] learned set (in_scope only) size = {len(learned)}; '
          f'historical out-of-scope picks skipped = {learned_stats["out_of_scope_picks_skipped"]}; '
          f'corpus_lookup_used = {learned_stats["housekeeping_5_repair"]["corpus_lookup_filename_only_used"]}')

    # Rule 5: 选样
    picks, pick_stats = pick_samples(samples, learned, whitelist, blacklist_prefixes,
                                     n_train, args.holdout, seed=args.seed)

    # 自检
    ok, errors = self_check_picks(picks)
    if not ok:
        print('[picker_v2] FATAL self-check failed:', file=sys.stderr)
        for e in errors:
            print(f'  - {e}', file=sys.stderr)
        sys.exit(3)

    out = {
        'batch': args.batch,
        'picker_version': 'v2',
        'picker_source': 'doc/SkillAI/tools/picker_v2.py',
        'scope_doc_meta': scope_meta,
        'whitelist_loaded': whitelist,
        'blacklist_prefixes_loaded': blacklist_prefixes,
        'learned_set_stats': learned_stats,
        'pick_stats': pick_stats,
        'picks': picks,
        'rule_compliance': {
            'rule_1_is_in_scope_function_applied': True,
            'rule_2_in_scope_verdict_and_evidence_present_on_every_pick': True,
            'rule_3_whitelist_grepped_from_scope_doc': True,
            'rule_4_learned_set_in_scope_filtered': True,
            'rule_5_segment_no_longer_sole_selection_criterion': True,
        },
        'learned_set_size': len(learned),
        'self_check_pass': True,
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f'\n=== {args.batch} picks (picker_v2) ===')
    for p in picks:
        print(f"  {p['role']:7s} {p['whitelist_subcat']:24s} sid={p['skill_id']:>10s} "
              f"nodes={p['node_count']:>4d} {p['filename']}")
    print(f'\n[picker_v2] saved -> {args.out}')


if __name__ == '__main__':
    main()
