"""id_allocator.py — 复刻 NodeEditor.ConfigIDManager 的 ID 分配规则

源码出处：
- Assets/Thirds/NodeEditor/Datas/ConfigIDManager.cs:345  GetNextConfigID
- Assets/Thirds/NodeEditor/Utils/Utils.cs:147  IP_End()
- Assets/Thirds/NodeEditor/SkillEditor/Saves/TableAnnotation.json  各表 ConfigIDAdd

规则:
  ip = IPv4 第 4 段（如 192.168.1.32 → 32）
  addNum = TableAnnotation.{table}.ConfigIDAdd
  idMin = ip * addNum
  idMax = (ip+1) * addNum - 1
  nextID = max(已分配 ID 集合) + 1（限定在段位内）

不持久化 ConfigID.json（[JsonIgnore]）/ 通过扫描所有 SkillGraph JSON 重建已分配集合。

用法:
    from id_allocator import IDAllocator
    alloc = IDAllocator(ip=32)  # 不指定 ip 时自动从本机 IPv4 取
    new_se_id = alloc.get_next('SkillEffectConfig')
    new_tag_id = alloc.get_next('SkillTagsConfig')
    new_bullet_id = alloc.get_next('BulletConfig')
"""
import json
import socket
from pathlib import Path
from collections import defaultdict


PROJECT_ROOT = Path(r'f:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj')
TABLE_ANNOTATION_PATH = PROJECT_ROOT / 'Assets/Thirds/NodeEditor/SkillEditor/Saves/TableAnnotation.json'
SKILL_GRAPH_DIR = PROJECT_ROOT / 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons'
USER_CONFIG_PATH = Path(__file__).parent / 'user_config.json'

DEFAULT_CONFIG_ID_ADD = 10000  # ConfigIDManager.cs:26


def load_user_config():
    """Read tools/user_config.json (per-user local config). Falls back to defaults."""
    if not USER_CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(USER_CONFIG_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}


def get_local_ip_end():
    """复刻 Utils.IP_End() — 取本机 IPv4 第 4 段
    优先级: user_config.json ip_end > socket 自检 > fallback 32
    """
    cfg = load_user_config()
    if 'ip_end' in cfg and isinstance(cfg['ip_end'], int):
        return cfg['ip_end']
    try:
        # Connect to a dummy address to force the OS to pick local IPv4
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return int(ip.split('.')[3])
    except Exception:
        return 32  # fallback


def load_table_steps():
    """读 TableAnnotation.json 提取所有表的 ConfigIDAdd"""
    if not TABLE_ANNOTATION_PATH.exists():
        return {}
    with open(TABLE_ANNOTATION_PATH, encoding='utf-8') as f:
        data = json.load(f)
    steps = {}
    for k, v in data.items():
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and 'ConfigIDAdd' in item and 'name' in item:
                    steps[item['name']] = item['ConfigIDAdd']
    return steps


# Mapping from node cls → which table it belongs to
NODE_CLS_TO_TABLE = {
    'SkillConfigNode': 'SkillConfig',
    'SkillTagsConfigNode': 'SkillTagsConfig',
    'BulletConfigNode': 'BulletConfig',
    'ModelConfigNode': 'ModelConfig',
    'BuffConfigNode': 'BuffConfig',
    'SkillIndicatorConfigNode': 'SkillIndicatorConfig',
    'SkillSelectConfigNode': 'SkillSelectConfig',
    'SkillInterruptConfigNode': 'SkillInterruptConfig',
    # All TSET_* nodes are SkillEffectConfig
}


def cls_to_table(cls):
    if cls.startswith('TSET_'):
        return 'SkillEffectConfig'
    return NODE_CLS_TO_TABLE.get(cls)


class IDAllocator:
    def __init__(self, ip=None, exclude_files=None):
        self.ip = ip if ip is not None else get_local_ip_end()
        self.steps = load_table_steps()
        if not self.steps:
            raise RuntimeError("Failed to load table steps from TableAnnotation.json")
        # Build allocated ID set per table (scan all SkillGraph_*.json)
        self.allocated = self._scan_all_allocated_ids(exclude_files or set())
        # Pending IDs allocated in this session (not yet written)
        self.pending = defaultdict(set)

    def _scan_all_allocated_ids(self, exclude_files):
        """Walk all SkillGraph_*.json, collect (table_name, ID) pairs"""
        allocated = defaultdict(set)
        for path in SKILL_GRAPH_DIR.rglob('SkillGraph_*.json'):
            if str(path) in exclude_files:
                continue
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                refids = data.get('references', {}).get('RefIds', [])
                for r in refids:
                    cls = r.get('type', {}).get('class', '')
                    table = cls_to_table(cls)
                    if not table:
                        continue
                    cj_str = r.get('data', {}).get('ConfigJson', '')
                    if not cj_str:
                        continue
                    try:
                        cj = json.loads(cj_str)
                        ID = cj.get('ID') or r.get('data', {}).get('ID')
                        if isinstance(ID, int) and ID > 0:
                            allocated[table].add(ID)
                    except Exception:
                        pass
            except Exception:
                pass
        return allocated

    def get_next(self, table_name):
        """Allocate next ID for given table, in ip-segment"""
        if table_name not in self.steps:
            raise ValueError(f"Unknown table: {table_name}. Known: {list(self.steps.keys())[:10]}...")
        step = self.steps[table_name]
        id_min = self.ip * step
        id_max = (self.ip + 1) * step - 1

        used = self.allocated.get(table_name, set()) | self.pending.get(table_name, set())
        in_segment = sorted([i for i in used if id_min <= i <= id_max])
        next_id = (in_segment[-1] + 1) if in_segment else id_min + 1

        if next_id > id_max:
            raise RuntimeError(
                f"ID exhausted in segment [{id_min}, {id_max}] for {table_name} ip={self.ip}")

        self.pending[table_name].add(next_id)
        return next_id

    def info(self):
        """Print allocation status per table"""
        print(f'IP={self.ip}  /  Table steps + allocated counts:')
        for t in sorted(self.steps.keys()):
            step = self.steps[t]
            seg = (self.ip * step, (self.ip + 1) * step - 1)
            used = self.allocated.get(t, set())
            in_seg = [i for i in used if seg[0] <= i <= seg[1]]
            print(f'  {t:<32} step={step:<10} ip={self.ip} segment={seg}  used in seg: {len(in_seg)}')


if __name__ == '__main__':
    alloc = IDAllocator()
    alloc.info()
    print()
    print('Sample allocations:')
    for t in ['SkillEffectConfig', 'SkillTagsConfig', 'BulletConfig', 'ModelConfig']:
        print(f'  next {t}: {alloc.get_next(t)}')
