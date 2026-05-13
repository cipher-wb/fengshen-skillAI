// Windows ↔ Unix 路径互转 + resolve
import path from 'node:path';
import { existsSync, statSync } from 'node:fs';

/** 输出 POSIX 风格 (Unity + Python + Bash 都接受) */
export function posix(p) {
  if (!p) return p;
  return p.split(path.sep).join('/').replace(/\\/g, '/');
}

/** 输出 Windows 风格 (PowerShell 命令示例) */
export function windows(p) {
  if (!p) return p;
  return p.split('/').join('\\');
}

/** 用户输入 normalize / 处理 ~/x、./x、绝对路径、Windows 驱动器盘符 */
export function normalize(input) {
  if (!input) return input;
  // 用户可能输入 ~ 开头 (Unix-style home)
  if (input.startsWith('~/') || input.startsWith('~\\')) {
    const home = process.env.HOME || process.env.USERPROFILE || '';
    input = path.join(home, input.slice(2));
  }
  return posix(path.resolve(path.normalize(input)));
}

/** 检查路径是否合法 + 存在 */
export function pathExists(p, kind = 'any') {
  if (!p) return false;
  if (!existsSync(p)) return false;
  if (kind === 'dir') return statSync(p).isDirectory();
  if (kind === 'file') return statSync(p).isFile();
  return true;
}

/** 检查路径是否在某根路径下 (防 path traversal) */
export function isWithin(child, parent) {
  const c = path.resolve(child);
  const p = path.resolve(parent);
  return c.startsWith(p + path.sep) || c === p;
}

/** 拼接路径 (始终 POSIX 输出) */
export function joinPosix(...parts) {
  return posix(path.join(...parts));
}

/** Unity 项目检测 (target 路径下是否有 Assets/ 目录) */
export function detectUnityProject(projectRoot) {
  return pathExists(path.join(projectRoot, 'Assets'), 'dir');
}

/** SkillEditor 检测 (target 路径下是否有 SkillGraph_*.json) */
export function detectSkillEditor(skillgraphRoot) {
  if (!pathExists(skillgraphRoot, 'dir')) return false;
  // 简单 glob: 递归找一个 SkillGraph_*.json 即可
  // (避免依赖 glob 包 / 用 Node 内置 fs)
  try {
    const { readdirSync } = require('node:fs');
    const stack = [skillgraphRoot];
    let scanned = 0;
    while (stack.length && scanned < 100) {
      const dir = stack.pop();
      const entries = readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        scanned++;
        if (entry.isFile() && entry.name.startsWith('SkillGraph_') && entry.name.endsWith('.json')) {
          return true;
        }
        if (entry.isDirectory() && !entry.name.startsWith('.')) {
          stack.push(path.join(dir, entry.name));
        }
      }
    }
  } catch {
    return false;
  }
  return false;
}
