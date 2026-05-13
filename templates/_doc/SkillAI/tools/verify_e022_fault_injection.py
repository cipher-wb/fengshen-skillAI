#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E022 故障注入测试。

步骤：
1. 读取 v0.5 模板 JSON
2. 故意删除 BulletConfig.AfterBornSkillEffectExecuteInfo.SkillEffectConfigID 的字段端口边
3. 写到 /tmp 临时文件
4. 跑 lint，期望 E022 报错
5. 同样测试删除 Model 字段端口边
"""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path

PROJ = Path(r"<<PROJECT_ROOT_WIN>>")
TARGET = PROJ / "<<SKILLGRAPH_JSONS_ROOT>>技能模板/子弹/SkillGraph_【模板】旋转扩张子弹圈.json"

sys.path.insert(0, str(PROJ / "doc/SkillAI/tools"))
from skill_lint import lint_file, LintReport, check_e022_bullet_field_port_consistency


def remove_field_port_edge(graph: dict, port_id: str) -> int:
    """删除所有 outputPortIdentifier == port_id 的边，返回删除数量。"""
    before = len(graph["edges"])
    graph["edges"] = [
        e for e in graph["edges"]
        if not (e.get("outputFieldName") == "PackedMembersOutput"
                and e.get("outputPortIdentifier") == port_id)
    ]
    return before - len(graph["edges"])


def run_test(label: str, port_id_to_remove: str, expected_error_substr: str):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    g = json.loads(TARGET.read_text(encoding="utf-8"))
    removed = remove_field_port_edge(g, port_id_to_remove)
    print(f"\n--- {label} ---")
    print(f"删除字段端口边 outputPortIdentifier={port_id_to_remove!r}，移除条数: {removed}")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tf:
        tf.write(json.dumps(g, ensure_ascii=False, indent=2))
        tmp_path = Path(tf.name)

    try:
        # E022 默认未注册到 lint_file（避免对生产文件大量误报），手动调用
        report = lint_file(tmp_path)
        graph = json.loads(tmp_path.read_text(encoding="utf-8"))
        refs = graph.get("references", {}).get("RefIds", [])
        check_e022_bullet_field_port_consistency(graph, refs, report)
        # 找 E022 错误
        e022_errors = [e for e in report.errors if e.code == "E022"]
        if e022_errors:
            print(f"✓ E022 触发！共 {len(e022_errors)} 条错误：")
            for err in e022_errors:
                msg = str(err)
                print(f"  {msg[:300]}")
                if expected_error_substr in msg:
                    print(f"  ↑ 包含期望子串 {expected_error_substr!r}: ✓")
            return len(e022_errors) > 0
        else:
            print(f"✗ E022 未触发！全部错误:")
            for err in report.errors:
                print(f"  {err}")
            return False
    finally:
        tmp_path.unlink()


def main():
    print("=" * 60)
    print("E022 故障注入测试 — v0.5 模板内置 BulletConfig 字段端口一致性")
    print("=" * 60)

    # 测试 1：删除 AfterBornSkillEffectExecuteInfo.SkillEffectConfigID
    ok1 = run_test(
        "测试 1：删除 AfterBorn 字段端口边",
        "AfterBornSkillEffectExecuteInfo.SkillEffectConfigID",
        "AfterBorn"
    )

    # 测试 2：删除 Model 字段端口边
    ok2 = run_test(
        "测试 2：删除 Model 字段端口边",
        "Model",
        "BulletConfig.Model"
    )

    print("\n" + ("=" * 60))
    print(f"测试 1 (AfterBorn): {'✓' if ok1 else '✗'}")
    print(f"测试 2 (Model):     {'✓' if ok2 else '✗'}")
    print("总结论:    " + ("✓ E022 故障注入测试全部通过" if ok1 and ok2
                            else "✗ E022 拦截能力不足"))
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
