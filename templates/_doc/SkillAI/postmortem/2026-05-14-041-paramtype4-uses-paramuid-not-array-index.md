---
type: 复盘页
summary: SkillEditor 节点 ConfigJson.Params 中 PT=4 引用的 Value 字段是 ParamUID（1-indexed 业务编号），不是 TemplateParamsDesc 数组的 0-indexed 索引
date: 2026-05-14
tags: [PostMortem, SkillEditor, ParamUID, PT=4, TemplateParam, 模板引用]
---

# PostMortem #041 — PT=4 引用 Value 是 ParamUID（不是 TPD 数组索引）

## 新规则

**SkillEditor 节点 `ConfigJson.Params[i]` 当 `ParamType=4` (TPT_EXTRA_PARAM) 时，`Value` 字段必须填目标 TemplateParam 的 `ParamUID`（1-indexed 业务编号）**，不是 TemplateParamsDesc 数组的 0-indexed 索引。

校验式：`for each Params with PT=4: assert exists TemplateParam where ParamUID == Value`

## 现象

2026-05-14 用户实战测试 L0 模板 `子弹通用逻辑-伤害` 的 case 4（条件附加伤害）TP[7] 触发条件守卫：

- **预期**：TP[7]=某 SCT ID → 条件满足才加 +N / 条件不满足时不加
- **实际**：不论 TP[7] 填什么值（0 / 任意 SCT ID / 永远 false 的 SCT），case 4 都**总是**加 +N
- 用户原话："技能增伤-触发条件 没有效果，就是他配不配都没有区别，技能增伤的伤害倒是增加上去了"

## 根因

排查 3 个守卫节点的 ConfigJson.Params 后发现：

- 1090 P[0] = `{V:7, PT:4}`（应该引用 TP[7] 触发条件）
- 1092 P[0] = `{V:7, PT:4}`（同上）
- 1093 P[0] = `{V:7, PT:4}`（同上）

但 L0 TP[7] (TPD[7] 数组位置) 的 `ParamUID = 8`！PT=4 引用按 ParamUID 而非数组索引，所以 V=7 实际指向 **ParamUID=7 = TPD[6] "自定义额外伤害"**。

**错位结果**：
- 1093 `TSCT_VALUE_COMPARE(自定义额外伤害 == 0)` → 默认填 -1 永远不等于 0 → 走"内层动态评估"
- 1090/1092 `TSET_CONDITION_EXECUTE(P[0]=自定义额外伤害值当 SCT ID)` → 用 -1 当 SCT ID → runtime 找不到 → 默认行为 fallback 到 true → 永远 ADD attr960

合并：**不管 TP[7] 实际填什么，守卫总是走到 ADD**。

## 修复

1090/1092/1093 三个节点 P[0] V 从 7 改成 8（对应 TP[7] 触发条件的 ParamUID）。

```python
for r in refs:
    if r['rid'] in [1090, 1092, 1093]:
        cj = json.loads(r['data']['ConfigJson'])
        cj['Params'][0]['Value'] = 8  # was 7
```

修复后行为：
- TP[7]=0 → 1093 评估 true → 直接 ADD（无条件触发分支）✓
- TP[7]=某真 SCT → 1090/1092 用它当 SCT ID 评估 → true 才 ADD ✓
- TP[7]=永远 false SCT → 1090/1092 评估 false → 不 ADD ✓

## 建议沉淀位置

- ✅ **memory**：[feedback_paramtype4_uses_paramuid.md](../../../memory/feedback_paramtype4_uses_paramuid.md)（已写 / 私人速查 + 校验脚本）
- ✅ **PostMortem**：本文件
- ⏳ **mental_model**：建议加到 `doc/SkillAI/mental_model/SkillEditor文件结构.md` 新立 §H 或并入 §A 节点双数组铁律（由 curator Mode B 决定）
- ⏳ **代码护栏候选**：`doc/SkillAI/tools/lint_paramuid_ref.py`（PT=4 引用合法性检查，未来加 lint）

## 利 / 弊 / 噪音风险

- **利**：彻底防止 PT=4 引用错位 / 这种 bug 表面看起来"逻辑对"（节点都存在 / edges 都对 / 字段都填了）但实际指向错参数 / 用户实战才发现 / 排查极难
- **弊**：sub-agent / 脚本写引用前必须 fs 真扫 TemplateParams 的 ParamUID，不能凭"数组索引经验"
- **噪音**：低 — 配置节点引用本来就该精确

## 关联

- **同源 PostMortem #038** "接力消息不可全信"：上次是接力消息字段名错（"触发条件-形式" vs "技能增伤-形式"），这次是我自己脑补的"V=TPD数组索引"规则错。两次都是 **fs 真扫 ground truth 第一原则**的反面教材。
- **同源 PostMortem #037** "双数组写入铁律"：都属于 SkillEditor JSON 结构层"看起来对实际错"陷阱。

## 决定项

✅ **入库 3 处**（memory + PostMortem + 待 curator 加 mental_model）+ 代码护栏待办。

## 校验脚本（开发时自查）

```python
def verify_pt4_refs(graph_json_path):
    """检查所有 PT=4 引用是否合法"""
    d = json.load(open(graph_json_path, encoding='utf-8'))
    for r in d['references']['RefIds']:
        if r['rid'] != 1000: continue
        root_tps = r['data']['TemplateParams']
        break

    valid_uids = {tp['ParamUID'] for tp in root_tps}

    errors = []
    for r in d['references']['RefIds']:
        cj_str = r['data'].get('ConfigJson', '')
        try:
            cj = json.loads(cj_str)
        except:
            continue
        for i, prm in enumerate(cj.get('Params', [])):
            if prm.get('ParamType') == 4 and prm.get('Value') not in valid_uids:
                errors.append(f'rid={r["rid"]} P[{i}] V={prm["Value"]} 不是合法 ParamUID')
    return errors
```
