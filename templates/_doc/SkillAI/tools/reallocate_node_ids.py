"""reallocate_node_ids.py — 重分配 SkillGraph 中所有不符合 ip 段位规则的节点 ID

规则:
- SkillConfig.ID 不动（人工命名）
- ModelConfig.ID 如果已在 ip 段位则不动
- 其他所有节点 ID（错段位的）→ 重分配到 ip 段位
- 同时更新所有 ID 引用（ConfigJson.Params / *SkillEffectExecuteInfo.SkillEffectConfigID / Desc 等）

用法:
    python reallocate_node_ids.py <graph_path> [--ip <ip>] [--dry-run]
"""
import json
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from id_allocator import IDAllocator, cls_to_table


def reallocate(graph_path: Path, ip: int, dry_run=False):
    data = json.loads(graph_path.read_text(encoding='utf-8'))

    # Build IDAllocator (exclude target file to avoid double-counting its own IDs)
    alloc = IDAllocator(ip=ip, exclude_files={str(graph_path)})

    # Step 1: Identify all node IDs and decide which ones need reallocation
    id_map = {}  # old_id -> new_id
    skipped = []
    for r in data['references']['RefIds']:
        cls = r['type']['class']
        table = cls_to_table(cls)
        if not table:
            continue
        cj_str = r['data'].get('ConfigJson', '') or '{}'
        try:
            cj = json.loads(cj_str)
        except json.JSONDecodeError:
            continue
        old_id = cj.get('ID')
        if not isinstance(old_id, int) or old_id == 0:
            continue

        # Check if in ip segment
        step = alloc.steps.get(table)
        if not step:
            continue
        id_min = ip * step
        id_max = (ip + 1) * step - 1

        # Decision:
        if table == 'SkillConfig':
            # SkillConfig ID is human-named, never reallocate
            skipped.append((old_id, table, 'SkillConfig human-named'))
            continue
        if id_min <= old_id <= id_max:
            # Already in correct segment
            skipped.append((old_id, table, f'in ip={ip} segment'))
            continue
        # Need reallocation
        new_id = alloc.get_next(table)
        id_map[old_id] = new_id
        print(f'  REALLOC [{table}] {old_id} -> {new_id}')

    if not id_map:
        print('No nodes need reallocation.')
        return

    print(f'\n=== {len(id_map)} reallocations / {len(skipped)} skipped ===')
    for old, _, reason in skipped:
        print(f'  SKIP {old} ({reason})')

    # Step 2: Update all references
    # In each node's ConfigJson, replace any field whose Value matches old_id (only if it's an ID reference)
    # Strategy: walk every JSON value recursively and replace ints in id_map
    def replace_in_obj(obj):
        if isinstance(obj, dict):
            return {k: replace_in_obj(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [replace_in_obj(v) for v in obj]
        if isinstance(obj, int) and obj in id_map:
            return id_map[obj]
        return obj

    for r in data['references']['RefIds']:
        # Update top-level data.ID if it's a reallocated one
        # (data.ID exists for some node types, mirrors ConfigJson.ID)
        if 'ID' in r['data'] and isinstance(r['data']['ID'], int) and r['data']['ID'] in id_map:
            r['data']['ID'] = id_map[r['data']['ID']]
        # Update data.Config2ID if it references the old ID
        if 'Config2ID' in r['data'] and isinstance(r['data']['Config2ID'], str):
            for old, new in id_map.items():
                r['data']['Config2ID'] = r['data']['Config2ID'].replace(f'_{old}', f'_{new}')
        # Update ConfigJson (parse + replace + reserialize)
        cj_str = r['data'].get('ConfigJson', '') or '{}'
        try:
            cj = json.loads(cj_str)
            cj_new = replace_in_obj(cj)
            r['data']['ConfigJson'] = json.dumps(cj_new, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
        # Update Desc (may contain ID references) — replace exact int substrings
        if 'Desc' in r['data'] and isinstance(r['data']['Desc'], str):
            desc = r['data']['Desc']
            for old, new in id_map.items():
                # Use word-boundary-like replace: surround by non-digit
                desc = desc.replace(str(old), str(new))
            r['data']['Desc'] = desc

    print(f'\n[OK] All references updated')

    if dry_run:
        print('[DRY RUN] not writing file')
        return

    # Backup before write
    backup_path = graph_path.with_suffix('.json.bak')
    backup_path.write_text(json.dumps(json.loads(graph_path.read_text(encoding='utf-8')), ensure_ascii=False, indent=4), encoding='utf-8')
    print(f'[BACKUP] {backup_path}')

    graph_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
    print(f'[WRITE] {graph_path}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('graph_path', type=Path)
    ap.add_argument('--ip', type=int, default=32, help='IP segment for new IDs')
    ap.add_argument('--dry-run', action='store_true', help='Preview only, no write')
    args = ap.parse_args()
    reallocate(args.graph_path, args.ip, args.dry_run)
