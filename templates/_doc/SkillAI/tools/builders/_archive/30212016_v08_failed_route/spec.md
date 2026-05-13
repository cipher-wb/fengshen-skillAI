# 旋转扩张矩形子弹圈 — 算法 Spec（v1.0 / 2026-05-11）

> 来源：用户原始算法需求文档（HTML 可视化 + MD 文档）
> 目的：新建 PoC 木宗门人阶奇术技能（**叶散风行旋转圈版**）
> 路径建议：`{{SKILLGRAPH_JSONS_ROOT}}宗门技能/木宗门技能/`
> 建议 ID：30212016（同段位下一个可用，3021201x 已占 0/1/2/3/4/5）

---

## 1. 用户裁决（2026-05-11）

| 决策 | 选择 |
|------|------|
| 改造范围 | **新建 PoC**（不动 30212010） |
| 默认参数预设 | **§9 "花瓣绽放" ± 召饰** |

---

## 2. 核心算法

### 2.1 第 i 颗子弹（i = 0..N-1）

```
初始角度 θ_i(0) = 2π · i / N          (弧度)
当前角度 θ_i(t) = θ_i(0) + ω · t       (ω 弧度/秒)
当前半径 R(t)   = R0 + vR · t + 0.5 · aR · t²
位置：x = px + R(t) · cos(θ_i(t))
     y = py + R(t) · sin(θ_i(t))      // Unity XZ: z = py + R(t) · sin(θ_i(t))
朝向：heading_i(t) = θ_i(t) + π/2 + φ  (矩形长边方向 / φ 是切线偏移)
```

### 2.2 必须把"度"转弧度

- 编辑器面板填 **度/秒** / **度**
- 公式用 **弧度/秒** / **弧度**
- 节点内必须做 `× π / 180` 转换

### 2.3 Unity XZ 平面（2.5D）

- 角度 θ 映射 `Vector3(cosθ, 0, sinθ)`
- 矩形朝向用 `Quaternion.LookRotation(切线 Vector3)`
- ω 正方向需明确（俯视顺时针/逆时针 → 通过 ω 符号控制）

---

## 3. 默认参数（花瓣绽放预设 ± 召饰）

> 文档原值是 px / Canvas 单位；本项目 Unity unit，按 SkillRange=800（千叶散华/叶散风行同尺度）反推大致 1 unit ≈ 1 px 或 4 px，待 designer GATE-0.5 验证

| 参数 | 文档 px 值 | Unity unit 值（建议） | 备注 |
|------|-----------|---------------------|------|
| bulletCount N | 8 | **8** | 圆周分布 |
| initialRadius R0 | 50 | **200**（≈ SkillRange/4） | t=0 半径 |
| radialVelocity vR | 150 | **400**/sec | 径向扩张速度 |
| radialAcceleration aR | 0 | **0** | 匀速扩张 |
| angularVelocity ω | 90°/s | **90°/s** | 整体旋转角速度 |
| tangentOffsetAngle φ | 0° | **0°** | 矩形纯切线 |
| lifetime | 2.0s | **2.0s** | 生命周期 |
| maxRadius | 1500 | **1200** | 超界销毁 |
| minRadius | 0 | **0** | 收缩下界 |
| 矩形长 L | 50 | **80**（unit） | 子弹模型长 |
| 矩形宽 W | 14 | **20**（unit） | 子弹模型宽 |
| followPlayer | false | **false** | 释放瞬间锁中心，不跟随主角 |
| damagePerHit | — | **100**（占位待数值表） | 每次命中伤害 |
| pierceCount | 1 | **1** | 穿透次数 |

---

## 4. 技能 SkillConfig 元数据（建议）

| 字段 | 值 |
|------|---|
| SkillID | 30212016（待 designer GATE-0.5 确认） |
| SkillNameEditor | "叶旋"（或团队拍板的木宗门技能名） |
| SubType | 102（沿用木宗门人阶奇术子型，与同段位 30212001-15 一致） |
| Icon | 木系 mu_xxx（沿用木宗门图标库） |
| Cast | 0（无抬手）|
| BD | 30 |
| CD | 900 |
| Indicator | Type=1（圆形 AOE）/ Range=1200（含 maxRadius）|
| EnhanceSkillBuffConfigID | 0（无心法增强）|

---

## 5. SkillTag 声明（Pattern A 技能级 / 沿用叶散风行命名空间）

> 命名遵循 [PostMortem #017](../postmortem/) 严格 "技能名XXX" 前缀

| Tag ID | 名称 | 默认 | 用途 |
|--------|------|------|------|
| 320180 | 叶旋_子弹数N | 8 | bulletCount |
| 320181 | 叶旋_初始半径R0 | 200 | initialRadius |
| 320182 | 叶旋_径向速度vR | 400 | radialVelocity |
| 320183 | 叶旋_径向加速度aR | 0 | radialAcceleration |
| 320184 | 叶旋_角速度ω度每秒 | 90 | angularVelocity (degree/sec) |
| 320185 | 叶旋_切线偏移φ度 | 0 | tangentOffsetAngle (degree) |
| 320186 | 叶旋_生命周期ms | 2000 | lifetime (ms) |
| 320187 | 叶旋_最大半径 | 1200 | maxRadius |
| 320188 | 叶旋_最小半径 | 0 | minRadius |
| 320189 | 叶旋_穿透次数 | 1 | pierceCount |

**ID 段位**：320180-320189（叶散风行用 320098/110/127/160 / 三重碧叶用 320100 / 叶旋用 320180+ 避冲突，待 designer 全局 ID 检查）

---

## 6. 关键实现节点（designer GATE-2 IR 规划参考）

### 6.1 OnSkillStart

- 加载 10 个 SkillTag 默认值（GET_SKILL_TAG_VALUE → 落到本地变量）
- 锁定中心：根据 followPlayer 选 caster pos 还是固定 pos
- 循环创建 N 颗 BulletConfig（每颗带初始 θ_i = 2π·i/N）
- 启动 Tick / Lifetime 计时

### 6.2 OnTick（每帧）

- 算 `t = currentTime - startTime`
- 检查 `t >= lifetime` → OnSkillEnd
- 算 `R = R0 + vR·t + 0.5·aR·t²`
- 检查 `R > maxRadius || R < minRadius` → OnSkillEnd
- 每颗子弹：
  - θ_i = θ_i(0) + ω·t
  - position = center + (R·cosθ, 0, R·sinθ)
  - heading = θ_i + π/2 + φ
  - CHANGE_ENTITY_POSITION + 朝向更新
  - 碰撞检测（穿透+ pierceCount 递减）

### 6.3 OnSkillEnd

- 销毁所有子弹 visual / collider
- 清理 buff / 标记

---

## 7. 边界条件清单

按算法文档 §8：

1. ✅ R < minRadius → 默认销毁（onMinRadius=Destroy）
2. ✅ R > maxRadius → 默认销毁（onMaxRadius=Destroy）
3. ✅ followPlayer=false（中心锁定，非默认跟随）
4. ✅ pierceCount + hitTargets 集合（防同一帧多次命中）
5. ✅ t = now - startTime（不用增量 dt 累积，防漂移）
6. ✅ N=1 / R0=0 不崩溃

---

## 8. designer agent 必做 GATE 流程（不可跳）

按 [.claude/skills/skill-design/SKILL.md](../../../.claude/skills/skill-design/SKILL.md)：

- **GATE-MENTAL-IN**：显式输出对子系统理解（SkillTag / BulletConfig / Tick / 数学计算 / Pattern A/B/C）
- **GATE-0**：grep 21 条 PostMortem
- **GATE-0.5**：**关键**——找 3 个相似真实样本（项目里有没有"圆周旋转弹幕"？"扩张圈层"？"用 SkillTag 计数器做位置"？grep 关键字 `MATH_COS` / `MATH_SIN` / `REPEAT_EXECUTE` 高 N 数的样本 / 30212009 千叶散华和 30212010 叶散风行也参考）
- **GATE-1**：mermaid + 参数表给用户审
- **GATE-2**：IR YAML 严校
- **GATE-3**：编译 + StickyNote 自动 emit
- **GATE-3.5**：AI 自审 4 项
- **GATE-4**：Lint E=0
- **GATE-5**：用户 Unity 实测

---

## 9. 已知坑（必须查 PostMortem）

- #018：所有 ID ≤ int32 max
- #019/#020：SkillTag Pattern A 技能级 vs Pattern B 实体级 vs Pattern C 临时计算
- #021：全局 ID 唯一性（特别是新增 320180-320189 段必扫全工程）
- #024：空子弹 Model 必填 4，不要填 0
- #026：REPEAT_EXECUTE 间隔=0 时 C++ 引擎 200 次硬上限
- 矩形子弹 heading：必须用 `θ + π/2 + φ`，不要用 θ 直接做 heading（文档 §7.1）
- 不要用增量 `position += velocity*dt` 累积（文档 §8.7 / 防多客户端漂移）

---

## 10. 原始可视化与算法文档参考

- HTML 可视化（用户本地）：`f:/AI/草稿/rotating_expanding_bullets.html`
- 算法 MD 文档：用户消息附件，重点 §3 数学模型 + §5 次级参数 + §8 边界 + §9 预设
