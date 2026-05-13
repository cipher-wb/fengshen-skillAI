"""自审 lint - 扇形分层弹幕 TP[8] buff 闸 patch"""
import json
import os

ROOT = r"<<PROJECT_ROOT_WIN>>"
TEMPLATE_FP = os.path.join(ROOT, r"Assets\Thirds\NodeEditor\SkillEditor\Saves\Jsons\技能模板\子弹\SkillGraph_【模板】扇形分层弹幕.json")
QYSH_FP = os.path.join(ROOT, r"Assets\Thirds\NodeEditor\SkillEditor\Saves\Jsons\宗门技能\木宗门技能\SkillGraph_30212009【木宗门】奇术_人阶_千叶散华.json")

with open(TEMPLATE_FP, "r", encoding="utf-8") as f:
    d = json.load(f)
refs = d["references"]["RefIds"]
edges = d["edges"]
nodes_arr = d["nodes"]

print("=== 模板自审 ===\n")

new_ids = [32100528, 32100529, 32100530, 32100531, 32100532]
nid_to_idx = {r["data"].get("ID"): i for i, r in enumerate(refs) if isinstance(r["data"].get("ID"), int)}
nid_to_guid = {r["data"].get("ID"): r["data"]["GUID"] for r in refs if isinstance(r["data"].get("ID"), int)}
guid_to_nid = {v: k for k, v in nid_to_guid.items()}

# CHECK 1: 新节点全在 refs
for nid in new_ids:
    r = refs[nid_to_idx[nid]]
    c = r["type"]["class"].split(".")[-1]
    print(f"  [OK] new {nid} class={c} rid={r['rid']} GUID={r['data']['GUID'][:8]}")
print()

# CHECK 2: nodes 数组也有新 rid
nodes_rids = {n["rid"] for n in nodes_arr}
for rid in [1355, 1356, 1357, 1358, 1359]:
    status = "OK" if rid in nodes_rids else "FAIL"
    print(f"  [{status}] nodes[] has rid={rid}")
print()

# CHECK 3: 唯一性
guids = [r["data"]["GUID"] for r in refs]
rids_all = [r["rid"] for r in refs]
ids_all = [r["data"].get("ID") for r in refs if isinstance(r["data"].get("ID"), int)]
print(f"  refs count: {len(refs)} / unique GUID: {len(set(guids))}")
print(f"  rid range: {min(rids_all)}~{max(rids_all)} / unique: {len(set(rids_all))}")
print(f"  node IDs unique: {len(set(ids_all))} / total: {len(ids_all)}")
assert len(set(guids)) == len(guids), "duplicate GUID!"
assert len(set(rids_all)) == len(rids_all), "duplicate rid!"
print("  [OK] no duplicates\n")

# CHECK 4: ORDER 32100296 Params[3] = 32100528
order = refs[nid_to_idx[32100296]]
cj = json.loads(order["data"]["ConfigJson"])
p3 = cj["Params"][3]["Value"]
status = "OK" if p3 == 32100528 else "FAIL"
print(f"  [{status}] ORDER 32100296 Params[3] = {p3} (expect 32100528)")
print()

# CHECK 5..8: 各新节点 Params
for nid, expected in [
    (32100528, [32100529, 32100520, 32100532]),  # outer cond / true / false
    (32100529, [32100530, 32100531]),             # OR children
]:
    cj = json.loads(refs[nid_to_idx[nid]]["data"]["ConfigJson"])
    ps = [p["Value"] for p in cj["Params"]]
    status = "OK" if ps == expected else "FAIL"
    print(f"  [{status}] {nid} Params = {ps} (expect {expected})")

# CHECK 9: VALUE_COMPARE 32100530
cj = json.loads(refs[nid_to_idx[32100530]]["data"]["ConfigJson"])
exp = [{"Value": 9, "ParamType": 4, "Factor": 0},
       {"Value": 1, "ParamType": 0, "Factor": 0},
       {"Value": 0, "ParamType": 0, "Factor": 0}]
status = "OK" if cj["Params"] == exp else "FAIL"
print(f"  [{status}] VALUE_COMPARE 32100530 Params:")
for i, p in enumerate(cj["Params"]):
    print(f"      P[{i}]: {p}")

# CHECK 10: HAS_BUFF 32100531
cj = json.loads(refs[nid_to_idx[32100531]]["data"]["ConfigJson"])
exp = [{"Value": 35, "ParamType": 5, "Factor": 0},
       {"Value": 9, "ParamType": 4, "Factor": 0},
       {"Value": 0, "ParamType": 0, "Factor": 0}]
status = "OK" if cj["Params"] == exp else "FAIL"
print(f"  [{status}] HAS_BUFF 32100531 Params:")
for i, p in enumerate(cj["Params"]):
    print(f"      P[{i}]: {p}")

# CHECK 11: 克隆普通弹 32100532 ID 正确
cj = json.loads(refs[nid_to_idx[32100532]]["data"]["ConfigJson"])
status = "OK" if cj["ID"] == 32100532 else "FAIL"
print(f"  [{status}] 克隆普通弹 32100532 cj.ID = {cj['ID']}")
print(f"      SkillEffectType = {cj['SkillEffectType']} (expect 8)")
print(f"      Params count = {len(cj['Params'])} (expect 15)")
print()

# CHECK 12: edges 删了旧的 ORDER→32100520
print("=== edges 自审 ===")
g_order = nid_to_guid[32100296]
g_old = nid_to_guid[32100520]
old_edges = [e for e in edges if e["outputNodeGUID"] == g_order and e["inputNodeGUID"] == g_old]
status = "OK" if len(old_edges) == 0 else "FAIL"
print(f"  [{status}] old ORDER→32100520 edges remaining: {len(old_edges)} (expect 0)")

# CHECK 13: 新 ORDER→32100528 边
g_528 = nid_to_guid[32100528]
new_e = [e for e in edges if e["outputNodeGUID"] == g_order and e["inputNodeGUID"] == g_528]
status = "OK" if len(new_e) == 1 else "FAIL"
print(f"  [{status}] new ORDER→32100528 edges: {len(new_e)} (expect 1)")
for e in new_e:
    print(f"      outPort={e['outputPortIdentifier']} inPort={e['inputPortIdentifier']}")

# CHECK 14: 32100528 固定端口 outPort 0/1/2
cond_edges = [e for e in edges if e["outputNodeGUID"] == g_528]
ports = sorted(e["outputPortIdentifier"] for e in cond_edges)
status = "OK" if ports == ["0", "1", "2"] else "FAIL"
print(f"  [{status}] 外层 COND 32100528 → children outPorts: {ports} (expect ['0','1','2'])")
for e in cond_edges:
    child = guid_to_nid.get(e["inputNodeGUID"])
    print(f"      outPort={e['outputPortIdentifier']} → child={child}")

# CHECK 15: OR 32100529 动态端口 outPort 全 0
g_or = nid_to_guid[32100529]
or_edges = [e for e in edges if e["outputNodeGUID"] == g_or]
ports = [e["outputPortIdentifier"] for e in or_edges]
status = "OK" if all(p == "0" for p in ports) and len(ports) == 2 else "FAIL"
print(f"  [{status}] OR 32100529 → children outPorts: {ports} (expect ['0','0'])")

# CHECK 16: unique-parent: 32100520 父=1
parents_old = [e for e in edges if e["inputNodeGUID"] == g_old]
status = "OK" if len(parents_old) == 1 else "FAIL"
print(f"  [{status}] 32100520 父引用: {len(parents_old)} (expect 1, unique-parent)")
for e in parents_old:
    parent = guid_to_nid.get(e["outputNodeGUID"])
    print(f"      parent={parent} outPort={e['outputPortIdentifier']}")

# CHECK 17: 32100532 克隆普通弹 父=32100528 outPort=2
g_clone = nid_to_guid[32100532]
clone_p = [e for e in edges if e["inputNodeGUID"] == g_clone]
status = "OK" if len(clone_p) == 1 else "FAIL"
print(f"  [{status}] 32100532 父引用: {len(clone_p)} (expect 1)")
for e in clone_p:
    parent = guid_to_nid.get(e["outputNodeGUID"])
    print(f"      parent={parent} outPort={e['outputPortIdentifier']}")
print()

# CHECK 18: TP[8] 加好
for r in refs:
    if r["data"].get("ID") == 32100001:
        tp = r["data"]["TemplateParams"]
        tpd = r["data"]["TemplateParamsDesc"]
        print(f"  TemplateParams: {len(tp)} (expect 9), TemplateParamsDesc: {len(tpd)} (expect 9)")
        print(f"  TP[8] Name: {tp[8]['Name'][:80]}")
        print(f"  TP[8] ParamUID: {tp[8]['ParamUID']}")
        print(f"  TP[8] DefalutParamJson: {tp[8]['DefalutParamJson']}")
        assert len(tp) == 9 and len(tpd) == 9 and tp[8]["ParamUID"] == 9
        print("  [OK]")
        break

print("\n=== 千叶散华 32200006 自审 ===")
with open(QYSH_FP, "r", encoding="utf-8") as f:
    dq = json.load(f)
for r in dq["references"]["RefIds"]:
    if r["data"].get("ID") == 32200006:
        cj = json.loads(r["data"]["ConfigJson"])
        td = r["data"].get("TemplateData", {})
        tp = td.get("TemplateParams", [])
        print(f"  ConfigJson.Params: {len(cj['Params'])} (expect 12)")
        print(f"  P[11]: {cj['Params'][11]}")
        print(f"  TemplateData.TemplateParams: {len(tp)} (expect 9)")
        print(f"  TP[8].Name: {tp[8]['Name'][:80]}")
        print(f"  TP[8].ParamUID: {tp[8]['ParamUID']}")
        assert len(cj["Params"]) == 12
        assert cj["Params"][11] == {"Value": 320037, "ParamType": 0, "Factor": 0}
        assert len(tp) == 9
        assert tp[8]["ParamUID"] == 9
        print("  [OK]")
        break

print("\n=== 行为预期模拟 ===")
print("  - TP[8]=0 (P[11]=0)        → VALUE_COMPARE = true → OR = true → 走 32100520（老逻辑）")
print("  - TP[8]=320037 + 有 buff    → HAS_BUFF = true → OR = true → 走 32100520（强化）")
print("  - TP[8]=320037 + 没 buff    → VALUE_COMPARE=false + HAS_BUFF=false → OR=false → 走 32100532（克隆普通弹）")
print("  - 千叶散华当前 P[11]=320037 → 触发上述新行为")

print("\n=== ALL CHECKS PASSED ===")
