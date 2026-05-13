// 模板引擎 / 递归遍历 templates/ + 渲染每个 .hbs / 直接 copy 非 .hbs
import fs from 'fs-extra';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderTemplate, findUnresolvedPlaceholders } from './placeholders.js';
import { sha256OfString } from './manifest.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * 模板目录 → 目标工程映射
 *
 * templates/
 * ├── _claude/   → ${projectRoot}/.claude/
 * ├── _doc/      → ${projectRoot}/doc/
 * └── _root/     → ${projectRoot}/   (CLAUDE.local.md / fengshen.config.json 等)
 */
const TEMPLATE_DIR_MAPPING = {
  _claude: '.claude',
  _doc: 'doc',
  _root: '' // 直接到工程根
};

export function getTemplatesRoot() {
  return path.join(__dirname, '..', '..', 'templates');
}

/**
 * 递归收集 templates/ 下所有文件
 * @returns {Array<{src, relPath, targetSubdir}>}
 */
export async function collectTemplateFiles() {
  const templatesRoot = getTemplatesRoot();
  const result = [];

  for (const [tplDirName, targetSubdir] of Object.entries(TEMPLATE_DIR_MAPPING)) {
    const dir = path.join(templatesRoot, tplDirName);
    if (!(await fs.pathExists(dir))) continue;

    await walk(dir, dir, async (filePath, relPath) => {
      result.push({
        src: filePath,
        relPath: relPath, // 相对 templates/_X/ 的路径
        targetSubdir // 目标子目录 ('.claude' / 'doc' / '')
      });
    });
  }

  return result;
}

async function walk(dir, baseDir, cb) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(full, baseDir, cb);
    } else {
      const rel = path.relative(baseDir, full).split(path.sep).join('/');
      await cb(full, rel);
    }
  }
}

/**
 * 计算目标文件路径
 */
export function computeTargetPath(projectRoot, tplFile) {
  // tplFile.relPath 例如 "agents/skill-designer.md.hbs"
  // tplFile.targetSubdir 例如 ".claude"
  // → ${projectRoot}/.claude/agents/skill-designer.md (去 .hbs)
  let rel = tplFile.relPath;
  if (rel.endsWith('.hbs')) {
    rel = rel.slice(0, -4);
  }
  return path.join(projectRoot, tplFile.targetSubdir, rel);
}

/**
 * 渲染并写入一个模板文件
 */
export async function renderAndWrite(tplFile, projectRoot, context, options = {}) {
  const targetPath = computeTargetPath(projectRoot, tplFile);
  const ext = path.extname(tplFile.src);
  const isHbs = tplFile.relPath.endsWith('.hbs');
  const filename = path.basename(tplFile.relPath);

  let content;
  if (isHbs) {
    const raw = await fs.readFile(tplFile.src, 'utf8');
    content = renderTemplate(filename.replace(/\.hbs$/, ''), raw, context);
  } else if (filename.endsWith('.py')) {
    // .py 文件用 Python 自定义 placeholder (避开 dict {{}} 冲突)
    const raw = await fs.readFile(tplFile.src, 'utf8');
    content = renderTemplate(filename, raw, context);
  } else {
    // 二进制 / 其他文件直接 copy
    if (options.dryRun) {
      return { targetPath, action: 'would-copy', hash: null };
    }
    await fs.ensureDir(path.dirname(targetPath));
    await fs.copy(tplFile.src, targetPath, { overwrite: true });
    const hash = sha256OfString(await fs.readFile(targetPath, 'utf8').catch(() => ''));
    return { targetPath, action: 'copied', hash };
  }

  // verification: 检查残留 placeholder
  const unresolved = findUnresolvedPlaceholders(content);
  if (unresolved.length > 0 && !options.allowUnresolved) {
    throw new Error(
      `模板 ${tplFile.relPath} 渲染后残留 ${unresolved.length} 个占位符: ${unresolved.slice(0, 5).join(', ')}`
    );
  }

  if (options.dryRun) {
    return { targetPath, action: 'would-render', hash: sha256OfString(content) };
  }

  await fs.ensureDir(path.dirname(targetPath));
  await fs.writeFile(targetPath, content, 'utf8');
  return { targetPath, action: 'rendered', hash: sha256OfString(content) };
}
