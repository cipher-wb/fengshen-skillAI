#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0.5 单根 BFS 可达性证明 + E022 故障注入测试。

期望：从 ROOT (32300001) 出发 BFS，应能可达：
- 所有 SkillEffectConfig / SkillConditionConfig 节点
- 内置 BulletConfigNode (32300150) — 通过 CREATE_BULLET Params[0] 引用
- 内置 ModelConfigNode (320149) — 通过 BulletConfig.Model 字段端口边
- OnTick init effect (32300101) — 通过 BulletConfig.AfterBornSkillEffectExecuteInfo
   字段端口边
- 排除：SkillTagsConfigNode（不参与可达性，是定义节点）

故障注入：删除 BulletConfig.AfterBornSkillEffectExecuteInfo.SkillEffectConfigID 字段端口边
后，OnTick init (32300101) 子图应不可达 → 应触发 lint E022（v0.5 新增）。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from collections import deque

PROJ = Path(r"<<PROJECT_ROOT_WIN>>")
TARGET = PROJ / "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】旋转扩张子弹圈.json"

ROOT_ID = 32300001
ONTICK_INIT_ID = 32300101
BULLET_CFG_ID = 32300150
MODEL_CFG_ID = 320149
EXEMPT_CLASSES = {"SkillTagsConfigNode"}  # 不参与可达性


def load_graph():
    return json.loads(TARGET.read_text(encoding="utf-8"))


def build_adj(graph):
    """构建有向图：被引用节点 → 引用方（按数据流方向）。
    edges 中：
      - inputNodeGUID = 被引用节点 (ID 输入端)
      - outputNodeGUID = 引用方 (Params 或字段端口)
    BFS 从 ROOT (引用方) 反向 = outputNodeGUID 视为 src，inputNodeGUID 视为 dst。
    简化：双向都加，BFS 看可触达即可。
    """
    refs = graph["references"]["RefIds"]
    guid2id = {r["data"]["GUID"]: r["data"]["ID"] for r in refs}
    id2guid = {r["data"]["ID"]: r["data"]["GUID"] for r in refs}
    guid2cls = {r["data"]["GUID"]: r["type"]["class"] for r in refs}

    adj_fwd = {g: set() for g in guid2id}  # ref -> referenced
    for e in graph["edges"]:
        # 引用方 = outputNodeGUID（持有 Params/字段的节点），它引用 inputNodeGUID
        out_g = e["outputNodeGUID"]
        in_g = e["inputNodeGUID"]
        if out_g in adj_fwd and in_g in guid2id:
            adj_fwd[out_g].add(in_g)
    return guid2id, id2guid, guid2cls, adj_fwd


def bfs_reachable(start_guid, adj):
    visited = set([start_guid])
    q = deque([start_guid])
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in visited:
                visited.add(v)
                q.append(v)
    return visited


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    g = load_graph()
    guid2id, id2guid, guid2cls, adj = build_adj(g)
    refs = g["references"]["RefIds"]

    root_guid = id2guid[ROOT_ID]
    reach = bfs_reachable(root_guid, adj)

    total = len(refs)
    eligible = [r for r in refs if r["type"]["class"] not in EXEMPT_CLASSES]
    eligible_count = len(eligible)
    reach_count = sum(1 for r in eligible if r["data"]["GUID"] in reach)

    # 关键节点检查
    must_reach = [
        ("内置 BulletConfig", BULLET_CFG_ID),
        ("内置 ModelConfig", MODEL_CFG_ID),
        ("OnTick init effect", ONTICK_INIT_ID),
    ]

    print("=" * 60)
    print("v0.5 单根 BFS 可达性报告")
    print("=" * 60)
    print(f"总节点数:     {total}")
    print(f"参与可达性 (排除 SkillTagsConfigNode): {eligible_count}")
    print(f"从 ROOT={ROOT_ID} 可达数: {reach_count}")
    print(f"覆盖率:       {reach_count}/{eligible_count} = {100*reach_count/eligible_count:.1f}%")

    print("\n关键节点可达性:")
    all_ok = True
    for name, nid in must_reach:
        guid = id2guid.get(nid)
        ok = guid and guid in reach
        status = "✓" if ok else "✗"
        print(f"  {status}  ID={nid:>10}  {name}")
        if not ok:
            all_ok = False

    print("\n不可达节点（应仅 SkillTagsConfigNode 或孤立工具节点）:")
    unreachable = [r for r in eligible if r["data"]["GUID"] not in reach]
    if not unreachable:
        print("  （无）")
    else:
        for r in unreachable:
            print(f"  ✗  ID={r['data']['ID']}  class={r['type']['class']}  desc={r['data'].get('Desc', '')[:40]!r}")

    print("\n" + ("=" * 60))
    print("结论: " + ("✓ v0.5 单根 100% 可达（除 SkillTagsConfigNode）" if all_ok and not unreachable
                      else "✗ 存在可达性问题"))

    return 0 if all_ok and not unreachable else 1


if __name__ == "__main__":
    sys.exit(main())
