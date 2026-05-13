---
type: 复盘页
summary: 30212017 旋转扩张子弹圈 PoC — 用 inline 7-MVP 路线一步步打通（替代 v08 自产模板路线）
date: 2026-05-11
tags: [PostMortem, MVP 路线, PT=2 NodeRef, MODIFY_ENTITY_ATTR, attr=91, 视觉-飞行解耦, SkillEffectType]
severity: 中（学习样本 / 多个反直觉点）
---

# PostMortem #031 — 30212017 旋转扩张子弹圈 7 段 MVP 推进总结

## 一句话

**30212016 v08 模板路线翻 6 轮（PostMortem #030）后，重起炉灶用 inline 7-MVP（30212017）一段段打通：N=1 → N=2 → birth offset → flight follows facing → 相对 caster → 圆周辐射 → 视觉/飞行同步自旋。每段都用最小可测原子修改 + 实测 + log 验证，最终拿到可用的旋转扩张子弹圈 PoC**。

---

## 推进时间线（MVP-1 → MVP-8）

| MVP | 目标 | 关键改动 | 验证方式 |
|-----|------|---------|---------|
| 1 | 单弹直线右移 | CREATE_BULLET + OnTick CHANGE_POS X+=5 | 视觉 |
| 2a | cos 节点取值 | 加 MATH_COS / 验 PT=2 NodeRef | log |
| 2b | t 累加振荡 | SkillTag angle_acc + COS(angle_acc)/100 振荡 | 视觉 S 曲线 |
| 3 | vR 加速 | SkillTag vR_acc / 每帧 +1 / X+=vR_acc | 视觉外扩 |
| 5a | N=2 | CREATE_B clone + ROOT_ORDER 4 项 | log MainEntity=8/9 各自累加 |
| 5b | 不同 birth facing | SkillTag 320931 + CREATE_B P[1] PT=3 SkillTag | 视觉 2 颗不同方向 |
| 5c | flight = facing 驱动 | OnTick 加 GET_facing + cos/sin 驱动 newX/newY | 视觉跟 facing 飞 |
| 5d | facing 相对 caster | GET_caster.facing + 90° → CREATE_B P[1] PT=2 NodeRef | 主角朝任意方向都 90° 夹角 |
| 5e | N=8 圆周辐射 | 6 个 NUM_CALC `caster.facing + offset_i` + 6 CREATE | 视觉 8 方向均匀 |
| 6a | 自旋（最初） | SkillTag spin_angle + effective_facing = self.facing + spin - 90 | **失败**：视觉静止不跟随 |
| 6a-fix1 | 视觉 +90 补偿 | 全部 CREATE.P[1] 视觉偏移 + effective_facing -90 抵消 | 视觉初始方向对了 |
| 6a-fix2 | 自旋方向翻转 | ADD_angle step +1 → -1 | 视觉初始还是不对 |
| 6a-final | MODIFY attr=91 驱动 | OnTick 加 MODIFY_ENTITY_ATTR_VALUE self.facing -= 1 每帧 | 视觉 + 飞行同步旋转 ✓ |
| 7 | 命中伤害（尝试） | 加碰撞 + 伤害模板（118）调用 | **崩溃**：模板内部 REPEAT_EXECUTE 拿到 interval=0+count=9999 |
| 8 | 提取 SkillTag 参数 | spin_step / vR_step / vR_initial 3 个 SkillTag | Lint E=0 / 待用户视觉调参验证 |

---

## 关键认知（按反直觉程度排序）

### 1. ⭐ MODIFY attr=91 → LocateComp.LogicFace → 视觉每帧 lerp 旋转

**反直觉**：源码 `BattleEntityProcessor.cs:2575` `rotation.y = -angle` 只在 entity 创建时执行一次。看上去 attr=91 改了视觉也不会跟。

**真相**：`BattleBulletAttrCollectComp.cs:91-93` 监听 attr 91 变化 → 写到 `LocateComp.LogicFace`，每帧 `SetEngineFace()` 把 LogicFace lerp 到 ViewFace 再 `SyncRotation()` → 模型旋转每帧更新。

**应用**：让 bullet 每帧自旋必须 MODIFY attr=91（直接改 `self.facing` 实属性），不能只改 SkillTag 累加器（SkillTag 不影响 entity 实属性，视觉不动）。

**证据**：MVP-6a-final 验证。

### 2. ⭐ 子弹 prefab 局部坐标轴 vs engine facing 不一致

**现象**：CREATE_BULLET P[1] = caster.facing + offset_i（理论上应该让 tip 指向 offset_i 方向），实测视觉 tip 是切向（90° 偏差）。

**根因**：叶子 prefab 局部 tip 沿 -Z 轴（推导）。engine `rotation.y = -facing` 后，local -Z 经 Y 旋转 -facing 后世界方向 = `(sin facing, 0, -cos facing)` = 比 facing 落后 90°（CW）。

**解法（视觉/飞行解耦）**：
- `CREATE.P[1]` 视觉 = `intended_radial + 90`（补 90° 让模型实际朝向 intended_radial）
- `effective_facing` (用于 cos/sin 飞行) = `self.facing - 90`（抵消上面的 +90）
- 净效果：visual ≈ flight direction（用户可见的）

**应用**：每个 bullet 模型都可能有自己的轴向偏移。配置层补偿前，**先实测**一颗子弹的 visual vs flight 方向差，再决定补偿值。

### 3. ⭐ SkillEffectType=5 ≠ TSET_RUN_SKILL_EFFECT_TEMPLATE，正确值是 118

**翻车现场**：MVP-7 给伤害节点填 `SkillEffectType=5`，SkillEditor 编辑器立刻"模板引用无效 190016485" + 参数 UI 显示成"挂载Buff单位 / 移除方式 / 参数1 / 参数2"（不是模板参数标签）。

**根因**：5 不是 RUN_TEMPLATE 的枚举。`TSET_RUN_SKILL_EFFECT_TEMPLATE = 118`（在 `common.nothotfix.cs:19407` 定义）。SkillEditor 按 type=5 加载 schema → 解析成 BUFF 节点 → 参数标签 fall-back to "参数N"。

**应用**：填 `SkillEffectType` 前必须查 `Assets/Scripts/TableDR_CS/NotHotfix/Gen/common.nothotfix.cs` 的 enum 定义，**不能凭感觉填**。常用值速查：
- `1 = ORDER_EXECUTE`
- `8 = CREATE_BULLET`
- `12 = MODIFY_ENTITY_ATTR_VALUE`
- `21 = REPEAT_EXECUTE`（待确认）
- `22 = CHANGE_ENTITY_POSITION`
- `31 = NUM_CALCULATE`
- `32 = GET_ENTITY_ATTR_VALUE`
- `46 = MODIFY_SKILL_TAG_VALUE`
- `50 = MATH_SIN`
- `51 = MATH_COS`
- `118 = RUN_SKILL_EFFECT_TEMPLATE`

### 4. CREATE_BULLET P[1] FACE_DIR 接受 3 种 PT 来源

**反直觉**：以为 P[1] 只能 PT=1 entity attr（如 V=91）或 PT=3 SkillTag ref。

**真相**：还可以 PT=2 NodeRef（指向 NUM_CALC），实现"动态计算出生方向"。MVP-5d 验证。

**应用**：要让多颗 bullet 各自相对 caster 不同方向出生 = 给每颗一个独立 NUM_CALC `caster.facing + offset_i` + CREATE_BULLET P[1] = NodeRef。

### 5. 模板内部 REPEAT_EXECUTE 不安全依赖 BulletConfig.FlyType

**MVP-7 崩溃**：碰撞模板 190016404 内部 REPEAT_EXECUTE (190016472) 拿到 `interval=0, count=9999`。

**差异点排查**：真实 30212010 BulletConfig 320112 `FlyType=1 / Speed=1500`，我们 320258 `FlyType=0 / Speed=0`（手动 CHANGE_POS 控制位置）。怀疑模板从 BulletConfig 读 FlyType/Speed 推算 REPEAT interval，FlyType=0 时取到 0 → 崩。

**应用**：手动位移 (FlyType=0) 子弹接入引擎标准模板时**不安全**。后续 MVP-7 改用：
- 方案 A：策划在 SkillEditor 手拖模板节点 + UI 选 schema（绕过 AI 填错）
- 方案 B：改 BulletConfig FlyType=1（变更大 / 需重测整体）
- 方案 C：跳过模板，自己 inline 写 TSKILLSELECT_CIRCLE + TSET_DAMAGE

### 6. NUM_CALC 5 项链式左结合可用

MVP-6a-fix1: `effective_facing = self.facing + spin_angle - 90` = `((self.facing + spin_angle) + -90)` → 5 项 [P[0]=self, P[1]=ADD, P[2]=spin, P[3]=ADD, P[4]=-90]。运行正常 / 跟 7 项链 (MVP-5c newX) 一致。

---

## 工程层教训

### A. inline 路线 vs 模板路线的取舍

PostMortem #030 (v08 模板) 翻 6 轮，本会话 inline 7-MVP 也翻几轮（视觉偏差 / 自旋方向 / MVP-7 模板崩），但每轮 fail 很小（节点级修改），用户视觉 / log 都能立刻发现。**对 PoC 场景，inline + 小步迭代 >> 自产模板复用**。

### B. SkillTag 提取 = 给策划的"调旋钮"

MVP-8 把 3 个常量 (spin_step / vR_step / vR_initial) 提取为 SkillTag PT=3 ref。策划在 SkillEditor SkillTag 面板能直接改默认值，不用动 JSON / builder。这是从 PoC → 策划可用资产的关键转换。

类似 PoC 资产化常用提取：N (bullet count)、半径 R、生命周期 LastTime、伤害值 / 系数。

### C. AI 自审/自纠失误链

- MVP-7 SkillEffectType=5 错填 → 没有事前查 enum / 凭"5 看起来像个低数应该对" 直觉填 = 翻车
- MVP-6a-fix1 视觉偏移符号搞反 → 没有事前理解 prefab 局部轴向 / 凭感觉填 -90 = 翻车（用户帮助翻转 +90 才对）

**改进**：填 enum 值 / 角度符号 / 偏移量前 **必须查源码 + 实测一组 case 验证假设**。

---

## 待做（本会话未完成）

1. **MVP-7 命中伤害**：跳过 / 待后续手拖配 + log 实测
2. **MVP-6 边界处理**：maxR / followPlayer / 销毁特效
3. **真实技能 30212010 移植**：当前 30212017 是 PoC / 可作为 30212010 的样板

---

## 心智模型回流条目（提案）

需 curator agent (Mode B) 评估是否入 mental_model 子系统页：

1. **bullet/视觉系统**：MODIFY attr=91 驱动 LocateComp.LogicFace（条目 1） + prefab 局部轴向补偿（条目 2）
2. **SkillEffectType 速查表**：常用 enum 值（条目 3）
3. **PT 来源扩展**：CREATE_BULLET P[1] 接受 PT=1/2/3 三种（条目 4）
4. **模板 + FlyType 耦合警告**：标准模板对 FlyType=0 不安全（条目 5）
5. **NUM_CALC 多项链式可用**：5 项 / 7 项验证 OK（条目 6 + 复述 MVP-5c）

---

## 引用

- [BattleBulletAttrCollectComp.cs:91-93](../../../Assets/Scripts/GameApp/GameApp/Components/Battle/Bullet/BattleBulletAttrCollectComp.cs#L91-L93)
- [BattleLocateComp.cs SetEngineFace()](../../../Assets/Scripts/GameApp/GameApp/Components/Battle/BattleLocateComp.cs#L774)
- [BattleEntityProcessor.cs:2575](../../../Assets/Scripts/GameApp/GameApp/Battle/BattleEntityProcessor.cs#L2575)
- [common.nothotfix.cs:19407](../../../Assets/Scripts/TableDR_CS/NotHotfix/Gen/common.nothotfix.cs#L19407) — TSET_RUN_SKILL_EFFECT_TEMPLATE = 118
- [doc/SkillAI/postmortem/2026-05-11-030-ai-self-produced-template-trap.md] — 上一版 v08 翻车前传
- [PostMortem #026 REPEAT_EXECUTE C++ crash] — MVP-7 同源
