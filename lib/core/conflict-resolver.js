// 冲突处理 / .claude/ 已存在 / CLAUDE.local.md 已有 / fengshen.config.json 已有
import fs from 'fs-extra';
import path from 'node:path';
import chalk from 'chalk';

/**
 * 备份目录或文件
 * @param {string} targetPath - 要备份的路径
 * @param {string} [suffix='bak'] - 后缀
 * @returns {string} 备份后的路径
 */
export async function backup(targetPath, suffix = 'fengshen.bak') {
  const ts = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0] + '_' + Date.now();
  const backupPath = `${targetPath}.${suffix}.${ts}`;
  await fs.move(targetPath, backupPath, { overwrite: false });
  return backupPath;
}

/**
 * 处理 CLAUDE.md 合并 (特殊处理 / 不覆盖用户写的部分)
 *
 * 策略：
 * - 用户文件 = 已存在 / 没有 fengshen 标记 → 在文件顶部插入 fengshen 段
 * - 用户文件 = 已存在 / 有 fengshen 标记 → 替换段内
 * - 用户文件 = 不存在 → 直接写
 *
 * fengshen 段格式：
 * <!-- fengshen-skillai begin v1.0.0 -->
 * ...content...
 * <!-- fengshen-skillai end -->
 *
 * 历史名称兼容：原函数名 mergeClaudeLocalMd 已 alias 兼容
 */
const BEGIN_MARKER = '<!-- fengshen-skillai begin';
const END_MARKER = '<!-- fengshen-skillai end -->';

export async function mergeClaudeMd(targetPath, fengshenContent) {
  const fengshenSection = `${BEGIN_MARKER} v1.0.0 -->\n\n${fengshenContent}\n\n${END_MARKER}`;

  if (!(await fs.pathExists(targetPath))) {
    // 新文件 / 直接写
    await fs.writeFile(targetPath, fengshenSection + '\n', 'utf8');
    return { action: 'created', backupPath: null };
  }

  const existing = await fs.readFile(targetPath, 'utf8');

  // 检测是否已有 fengshen 段
  const beginIdx = existing.indexOf(BEGIN_MARKER);
  const endIdx = existing.indexOf(END_MARKER);

  if (beginIdx !== -1 && endIdx !== -1 && endIdx > beginIdx) {
    // 已有 / 替换段内
    const before = existing.substring(0, beginIdx);
    const after = existing.substring(endIdx + END_MARKER.length);
    const newContent = before + fengshenSection + after;
    await fs.writeFile(targetPath, newContent, 'utf8');
    return { action: 'replaced-section', backupPath: null };
  }

  // 已有 / 无 fengshen 段 → 顶部插入
  const newContent = fengshenSection + '\n\n---\n\n' + existing;
  await fs.writeFile(targetPath, newContent, 'utf8');
  return { action: 'prepended-section', backupPath: null };
}

// 向后兼容 alias (老函数名 mergeClaudeLocalMd 别动)
export const mergeClaudeLocalMd = mergeClaudeMd;

/**
 * 处理 .claude/agents/ 冲突
 *
 * 策略 (按 strategy 字段):
 * - 'backup-and-overwrite' (默认): 备份现有 → 覆盖
 * - 'merge': 跳过同名文件 (保留用户的)
 * - 'force': 直接覆盖 (不备份)
 * - 'abort': 报错退出
 */
export async function resolveClaudeDirConflict(targetClaudeDir, strategy = 'backup-and-overwrite') {
  if (!(await fs.pathExists(targetClaudeDir))) {
    return { action: 'no-conflict', backupPath: null };
  }

  // 检查是否有任何 fengshen agent (skill-designer 等) 已存在
  const agentsDir = path.join(targetClaudeDir, 'agents');
  let hasFengshenAgents = false;
  if (await fs.pathExists(agentsDir)) {
    const fengshenAgentNames = ['skill-designer.md', 'skill-reviewer.md', 'skill-knowledge-curator.md', 'skill-knowledge-auditor.md'];
    for (const name of fengshenAgentNames) {
      if (await fs.pathExists(path.join(agentsDir, name))) {
        hasFengshenAgents = true;
        break;
      }
    }
  }

  if (!hasFengshenAgents) {
    // 用户有 .claude/ 但没有 fengshen agents → 直接 merge (不破坏用户内容)
    return { action: 'merge-no-conflict', backupPath: null };
  }

  switch (strategy) {
    case 'force':
      return { action: 'overwrite-without-backup', backupPath: null };
    case 'abort':
      throw new Error(`检测到 .claude/agents/ 已含 fengshen agent / 终止 (用 --force 跳过 / --merge 合并)`);
    case 'merge':
      return { action: 'merge-skip-existing', backupPath: null };
    case 'backup-and-overwrite':
    default: {
      const backupPath = await backup(agentsDir, 'fengshen.bak');
      return { action: 'backup-and-overwrite', backupPath };
    }
  }
}

/**
 * 处理 fengshen.config.json 已存在 (update 场景)
 */
export async function preserveConfig(targetPath) {
  if (!(await fs.pathExists(targetPath))) {
    return { existing: null };
  }
  return { existing: await fs.readJson(targetPath) };
}
