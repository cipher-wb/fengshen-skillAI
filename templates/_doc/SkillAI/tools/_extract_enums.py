"""一次性提取 TableDR_CS 中所有相关枚举的中文-整数-枚举名映射，输出为 JSON。"""
import json
import re
from pathlib import Path

PROJ = Path(r"<<PROJECT_ROOT_WIN>>")
ENUMS_CS_LIST = [
    PROJ / "Assets/Scripts/TableDR_CS/NotHotfix/Gen/common.nothotfix.cs",
    PROJ / "Assets/Scripts/TableDR_CS/Hotfix/Gen/common.hotfix.cs",
]
DROPDOWN_CS = PROJ / "Assets/Scripts/TableDR_CS/Hotfix/Gen/EnumUtility.Editor.cs"
OUT = Path(__file__).parent / "skill_editor_enums.json"

# 我们关心的枚举（白名单——避免把全 200 个枚举都吃进来）
WANTED_ENUMS = {
    "TParamType", "TCommonParamType",
    "TSkillEffectType", "TSkillSelectType", "TSkillConditionType",
    "TElementsType", "TBattleNatureEnum", "TEntityState", "TEntityType", "TEntityEffectType",
    "TBattleSkillSubType", "TBattleSkillMainType",
    "TSkillColdType", "TSkillTagsType", "TSkillUseType", "TSkillXinfaType",
    "TRoleAnimType", "TNumOperators", "TCompareType",
    "TScreenEffectType", "TSpecialSkillSelectFlag",
    "TSkillEntityGroupType", "TIndicatorType", "TShapeType",
    "TBuffType", "TBulletFlyType", "TCollisionLayer",
    "TSkillEffectBuffOverlyingAddType", "TSkillPreConditionType",
    "TSkillFulness", "TSkillEventSubType",
    "TBattleSkillPriorityType",
}

# === 1) 解析 common.*.cs：得到每个枚举 中文 → (整数值, 枚举名) ===
enums: dict[str, dict] = {}
text = ""
for cs in ENUMS_CS_LIST:
    text += cs.read_text(encoding="utf-8") + "\n"

# 匹配 `public enum Xxx { ... }`
pattern = re.compile(
    r"public\s+enum\s+(\w+)\s*\{([^}]*)\}",
    re.S,
)
# 在每个枚举体内提取每条：DescAttr + 名 = 整数
entry_pattern = re.compile(
    r'\[System\.ComponentModel\.Description\("([^"]*)"\)\][^A-Z]*?(?:\[[^\]]*\][^A-Z]*?)*([A-Z][A-Z0-9_]*)\s*=\s*(\d+)',
    re.S,
)

for m in pattern.finditer(text):
    name = m.group(1)
    if name not in WANTED_ENUMS:
        continue
    body = m.group(2)
    entries = []
    cn_to_int = {}
    cn_to_enum = {}
    int_to_cn = {}
    int_to_enum = {}
    enum_to_cn = {}
    for em in entry_pattern.finditer(body):
        cn = em.group(1)
        en = em.group(2)
        iv = int(em.group(3))
        entries.append({"cn": cn, "enum": en, "value": iv})
        cn_to_int[cn] = iv
        cn_to_enum[cn] = en
        int_to_cn[str(iv)] = cn
        int_to_enum[str(iv)] = en
        enum_to_cn[en] = cn
    enums[name] = {
        "entries": entries,
        "cn_to_int": cn_to_int,
        "cn_to_enum": cn_to_enum,
        "int_to_cn": int_to_cn,
        "int_to_enum": int_to_enum,
        "enum_to_cn": enum_to_cn,
        "count": len(entries),
    }

# === 2) 用 EnumUtility.Editor.cs 的 VD_xxx 字典作为补充（兜底/校验） ===
# 通常 common.nothotfix.cs 已有完整定义；这里只在某些枚举缺失时补充
# (跳过 — 当前 common 文件已满足)

# === 3) 输出 ===
out = {
    "_README": (
        "Auto-extracted from TableDR_CS. "
        "Use cn_to_int / cn_to_enum / int_to_cn / int_to_enum / enum_to_cn lookups."
    ),
    "enums": enums,
    "missing": sorted(WANTED_ENUMS - set(enums.keys())),
}

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

import sys
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
print(f"Wrote {OUT.name}")
print(f"Extracted {len(enums)} enums:")
for n, info in sorted(enums.items()):
    print(f"  {n}: {info['count']} entries")
print(f"Missing: {out['missing']}")
