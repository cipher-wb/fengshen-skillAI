# SkillAI 工具链 — 用户本地配置 + ID 分配工具

> 给每位策划用 SkillAI 工具链时的"本机身份"配置。

---

## 一、为什么需要 user_config.json

SkillEditor 内置 `ConfigIDManager` 在策划手动加节点时自动分配 ID，规则是：
```
ID = 本机 IPv4 第 4 段 × 表的 ConfigIDAdd + 序号
```

每位策划机器的 IPv4 第 4 段不同 → ID 段位天然隔离 → 多人协作不会冲突。

但 **AI 跑 Python builder 时拿不到 Unity 内的 IPv4**（不同进程 / 不同网络命名空间 / 容器化等）。
所以我们用 `user_config.json` 让你**显式告诉工具你的 IP 段**。

---

## 二、首次使用 — 3 步配置

### 1. 查你的 IPv4 第 4 段

在 Unity SkillEditor 里看任意一个你**手动加过的节点**的 ID：
- 节点 ID = `326123` → 你 IP 末段 = **32**（10000 步长 / 32 × 10000 = 320000 段位）
- 节点 ID = `33500045` → 你 IP 末段 = **33**（百万级表 SkillEffectConfig）
- 节点 ID = `3300451` → 你 IP 末段 = **33**（十万级表 ModelConfig）

或者：Windows 终端 `ipconfig` 看本机 IPv4 第 4 个数字。

### 2. 编辑 `doc/SkillAI/tools/user_config.json`

```json
{
    "user_name": "你的名字",
    "ip_end": 32,
    ...
}
```

只改 `ip_end` 字段（数字 / 1-255）。

### 3. 验证

```bash
python doc/SkillAI/tools/id_allocator.py
```

应该输出：
```
IP=32  /  Table steps + allocated counts:
  ...
Sample allocations:
  next SkillEffectConfig: 32900xxx   ← 应该在你 IP 段
  next SkillTagsConfig: 32xxxx       ← 应该在你 IP 段
```

---

## 三、ID 段位规则（自动计算 / 不用手动算）

| 表 | ConfigIDAdd（步长）| 你 IP=32 的段位 | 容量 |
|----|------------------|----------------|------|
| SkillEffectConfig | 1,000,000 | [32000000, 32999999] | 100 万 |
| ModelConfig | 100,000 | [3200000, 3299999] | 10 万 |
| SkillTagsConfig | 10,000 | [320000, 329999] | 1 万 |
| BulletConfig | 10,000 | [320000, 329999] | 1 万 |
| BuffConfig | 10,000 | [320000, 329999] | 1 万 |

**注意**：SkillConfig 表也有 ConfigIDAdd=10000，但 SkillID 是策划**人工命名**（如 30212017 = 30 木宗门 / 21 人阶 / 20 奇术 / 17 序号），不走自动分配。

---

## 四、工具一览

### `id_allocator.py` — 核心库

```python
from id_allocator import IDAllocator
alloc = IDAllocator()              # 默认从 user_config.json 读 ip_end
alloc = IDAllocator(ip=33)         # 显式指定 ip
alloc.info()                       # 打印各表段位 + 已用数量
new_id = alloc.get_next('SkillEffectConfig')   # 下一个可用 SkillEffect ID
new_id = alloc.get_next('SkillTagsConfig')
new_id = alloc.get_next('BulletConfig')
new_id = alloc.get_next('ModelConfig')
```

它会 grep 全工程所有 `SkillGraph_*.json` 拿到已用 ID 集合，自动 max+1 → 跟 SkillEditor 行为一致。

### `reallocate_node_ids.py` — 重分配已有蓝图

如果有蓝图节点 ID 错段位（如别的策划的机器配的 / 或 AI builder 之前写错的），用这个修：

```bash
python doc/SkillAI/tools/reallocate_node_ids.py <蓝图.json> --ip 32 --dry-run
# 看预览 / 确认无误后去掉 --dry-run 落盘
python doc/SkillAI/tools/reallocate_node_ids.py <蓝图.json> --ip 32
```

自动备份原文件到 `.bak`，更新所有 ConfigJson 内 Params 引用 / AfterBorn / SkillEffectExecuteInfo 等。

---

## 五、未来 Builder 默认用法（约定）

任何新 builder 脚本统一这个开头：

```python
from id_allocator import IDAllocator

def main():
    alloc = IDAllocator()                              # 自动读 user_config.json
    skill_effect_id = alloc.get_next('SkillEffectConfig')
    bullet_id = alloc.get_next('BulletConfig')
    # ... 用这些 ID 建节点 / 不再硬编 30212017x 这种错段位 ID
```

**禁止**在 builder 里硬编节点 ID（除 SkillConfig.ID 人工命名）。

---

## 六、团队多人协作

把 team_members 里登记好每个人的 IP 段：
```json
"team_members": {
    "insectwb": 32,
    "zhang_san": 33,
    "li_si": 34
}
```

> 这只是给人查的 / 工具不读这字段 / 实际只用 ip_end 一个值。

碰到 ID 冲突时（SkillEditor 启动报 `[ID冲突]`），看冲突 ID 落在哪个段位 → 反查谁的机器配的。

---

## 七、git 注意

`user_config.json` **不应提交到 git**（每个人本机不同）。
在 `.gitignore` 里加：
```
doc/SkillAI/tools/user_config.json
```

`README_user_config.md` 和 `id_allocator.py` `reallocate_node_ids.py` 提交。

---

## 八、源码出处

| 概念 | 源码位置 |
|------|---------|
| IP_End() | [Assets/Thirds/NodeEditor/Utils/Utils.cs:147](../../../Assets/Thirds/NodeEditor/Utils/Utils.cs#L147) |
| GetNextConfigID | [Assets/Thirds/NodeEditor/Datas/ConfigIDManager.cs:345](../../../Assets/Thirds/NodeEditor/Datas/ConfigIDManager.cs#L345) |
| ConfigIDAdd | [Assets/Thirds/NodeEditor/SkillEditor/Saves/TableAnnotation.json](../../../Assets/Thirds/NodeEditor/SkillEditor/Saves/TableAnnotation.json) |
| LocalSettings.Inst.ID | [Assets/Thirds/NodeEditor/Datas/LocalSettings.cs:84](../../../Assets/Thirds/NodeEditor/Datas/LocalSettings.cs#L84) |
