#!/usr/bin/env node
// scripts/extract-from-source.js
// 一次性从源工程 (F:/DreamRivakes2/...) 抽 SkillAI 系统到 templates/
//
// 用法：
//   node scripts/extract-from-source.js [--source <path>] [--dest <path>] [--include-batch-buffer]
//
// 默认：
//   --source = F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj
//   --dest = ./templates
//   --include-batch-buffer = false (默认仅 _archived/ 4 keep + 3 个分水岭代表)

import fs from 'fs-extra';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { argv } from 'node:process';
import { posix } from '../lib/core/path-utils.js';
import { sha256OfString } from '../lib/core/manifest.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(__dirname, '..');

// 默认值
const DEFAULTS = {
  source: 'F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj',
  dest: path.join(REPO_ROOT, 'templates'),
  includeBatchBuffer: false
};

function parseArgs() {
  const args = { ...DEFAULTS };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--source') args.source = argv[++i];
    else if (a === '--dest') args.dest = argv[++i];
    else if (a === '--include-batch-buffer') args.includeBatchBuffer = true;
    else if (a === '--include-batch-buffer=true') args.includeBatchBuffer = true;
    else if (a === '--include-batch-buffer=false') args.includeBatchBuffer = false;
    else if (a === '--validate') args.validate = true;
    else if (a === '-h' || a === '--help') {
      console.log(`
extract-from-source.js — 从源工程抽 SkillAI 系统到 templates/

用法：
  node scripts/extract-from-source.js [options]

选项：
  --source <path>          源工程根 (default: ${DEFAULTS.source})
  --dest <path>            目标 templates 根 (default: ${DEFAULTS.dest})
  --include-batch-buffer   抽完整 batch_buffer (default: false / 仅 _archived/)
  --validate               抽完后跑占位符 verify
`);
      process.exit(0);
    }
  }
  return args;
}

// 抽源映射：source 相对路径 → templates 子目录
const EXTRACT_MAP = [
  // .claude/agents/ → templates/_claude/agents/
  { src: '.claude/agents/skill-designer.md', dst: '_claude/agents/skill-designer.md.hbs' },
  { src: '.claude/agents/skill-reviewer.md', dst: '_claude/agents/skill-reviewer.md.hbs' },
  { src: '.claude/agents/skill-knowledge-curator.md', dst: '_claude/agents/skill-knowledge-curator.md.hbs' },
  { src: '.claude/agents/skill-knowledge-auditor.md', dst: '_claude/agents/skill-knowledge-auditor.md.hbs' },

  // .claude/skills/
  { src: '.claude/skills/skill-design', dst: '_claude/skills/skill-design', isDir: true, hbsAll: true },
  { src: '.claude/skills/skill-review', dst: '_claude/skills/skill-review', isDir: true, hbsAll: true },

  // .claude/settings.json
  { src: '.claude/settings.json', dst: '_claude/settings.json.hbs', optional: true },

  // doc/SkillAI/
  { src: 'doc/SkillAI/README.md', dst: '_doc/SkillAI/README.md.hbs' },
  { src: 'doc/SkillAI/进度.md', dst: '_doc/SkillAI/进度.md.hbs', optional: true },

  // doc/SkillAI/mental_model/
  { src: 'doc/SkillAI/mental_model', dst: '_doc/SkillAI/mental_model', isDir: true, hbsAll: false, excludeBatchBuffer: true },

  // doc/SkillAI/docs/
  { src: 'doc/SkillAI/docs', dst: '_doc/SkillAI/docs', isDir: true, hbsAll: false },

  // doc/SkillAI/tools/
  { src: 'doc/SkillAI/tools', dst: '_doc/SkillAI/tools', isDir: true, hbsAll: false, excludePycache: true },

  // doc/SkillAI/postmortem/
  { src: 'doc/SkillAI/postmortem', dst: '_doc/SkillAI/postmortem', isDir: true, hbsAll: false },

  // doc/SkillAI/samples/  (代表样本 / 限制数量)
  { src: 'doc/SkillAI/samples', dst: '_doc/SkillAI/samples', isDir: true, hbsAll: false, sampleOnly: true },

  // 根 / CLAUDE.local.md → 抽到 templates 作 CLAUDE.md (项目级)
  { src: 'CLAUDE.local.md', dst: '_root/CLAUDE.md.hbs' }
];

// 占位符替换 (针对 markdown 和 yaml; Python 单独处理)
// 顺序：先长后短 / 避免短匹配吃掉长匹配
const PLACEHOLDER_REPLACEMENTS = {
  markdown: [
    // 工程根（最长）
    [/F:\/DreamRivakes2\/ClientPublish\/DreamRivakes2_U3DProj/g, '{{PROJECT_ROOT}}'],
    [/F:\\DreamRivakes2\\ClientPublish\\DreamRivakes2_U3DProj/g, '{{PROJECT_ROOT_WIN}}'],
    // 主 Excel (1SkillEditor)
    [/F:\/DreamRivakes2\/Design\/Excel\/excel\/1SkillEditor\.xlsx/g, '{{SKILL_EXCEL_PATH}}'],
    [/F:\\DreamRivakes2\\Design\\Excel\\excel\\1SkillEditor\.xlsx/g, '{{SKILL_EXCEL_PATH_WIN}}'],
    // 其他 Excel 表所在目录 (derived 占位符 / 从 skill_excel_path dirname 推)
    [/F:\/DreamRivakes2\/Design\/Excel\/excel\//g, '{{SKILL_EXCEL_DIR}}/'],
    [/F:\\DreamRivakes2\\Design\\Excel\\excel\\/g, '{{SKILL_EXCEL_DIR_WIN}}\\'],
    // SkillGraph JSON 根
    [/Assets\/Thirds\/NodeEditor\/SkillEditor\/Saves\/Jsons\//g, '{{SKILLGRAPH_JSONS_ROOT}}']
  ],
  python: [
    [/F:\/DreamRivakes2\/ClientPublish\/DreamRivakes2_U3DProj/g, '<<PROJECT_ROOT>>'],
    [/F:\\DreamRivakes2\\ClientPublish\\DreamRivakes2_U3DProj/g, '<<PROJECT_ROOT_WIN>>'],
    [/F:\/DreamRivakes2\/Design\/Excel\/excel\/1SkillEditor\.xlsx/g, '<<SKILL_EXCEL_PATH>>'],
    [/F:\\DreamRivakes2\\Design\\Excel\\excel\\1SkillEditor\.xlsx/g, '<<SKILL_EXCEL_PATH_WIN>>'],
    [/F:\/DreamRivakes2\/Design\/Excel\/excel\//g, '<<SKILL_EXCEL_DIR>>/'],
    [/F:\\DreamRivakes2\\Design\\Excel\\excel\\/g, '<<SKILL_EXCEL_DIR_WIN>>\\'],
    [/Assets\/Thirds\/NodeEditor\/SkillEditor\/Saves\/Jsons\//g, '<<SKILLGRAPH_JSONS_ROOT>>']
  ]
};

function applyReplacements(content, isPython) {
  const replacements = isPython ? PLACEHOLDER_REPLACEMENTS.python : PLACEHOLDER_REPLACEMENTS.markdown;
  let result = content;
  for (const [pattern, replacement] of replacements) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

async function copyFile(srcPath, dstPath, opts = {}) {
  let content = await fs.readFile(srcPath, 'utf8');
  const isPython = srcPath.endsWith('.py');
  content = applyReplacements(content, isPython);
  await fs.ensureDir(path.dirname(dstPath));
  await fs.writeFile(dstPath, content, 'utf8');
  return content.length;
}

async function copyDir(srcDir, dstDir, options) {
  const stats = { files: 0, bytes: 0, skipped: 0 };
  if (!await fs.pathExists(srcDir)) {
    console.warn(`⚠ 源目录不存在: ${srcDir}`);
    return stats;
  }

  const entries = await fs.readdir(srcDir, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(srcDir, entry.name);

    // 排除规则
    if (options.excludePycache && entry.name === '__pycache__') continue;
    if (entry.name.startsWith('.git') || entry.name === '.DS_Store') continue;

    if (entry.isDirectory()) {
      // batch_buffer 特殊处理
      if (options.excludeBatchBuffer && entry.name === 'batch_buffer') {
        if (!options.includeBatchBuffer) {
          // 仅抽 _archived/ + 4 keep 文件
          const archivedSrc = path.join(srcPath, '_archived');
          const seedDst = path.join(dstDir, 'batch_buffer', '_seed');
          await fs.ensureDir(seedDst);

          // 仅抽几个分水岭文件作样本
          const KEEP_FILES = [
            '_archived/B-DESIGNER-CHAIN-001_yaml_COMMITTED_v0_16_39.md',
            '_aggregate_learning_inventory.py'
          ];
          for (const kf of KEEP_FILES) {
            const ksrc = path.join(srcPath, kf);
            if (await fs.pathExists(ksrc)) {
              const kdst = path.join(seedDst, path.basename(kf));
              await copyFile(ksrc, kdst);
              stats.files++;
            }
          }

          // 写一个 README 指向 GitHub Release
          await fs.writeFile(
            path.join(seedDst, 'README.md'),
            `# Batch Buffer (Learning History)

> 本目录仅含 v0.16.39 升正式分水岭的关键样本 (4 个 keep 文件)。
> 完整 batch_buffer (B-001 ~ B-061 / 581 文件 / ~34MB) 走 **GitHub Release**：
>
> \`\`\`bash
> npx fengshen-skillai download-history
> \`\`\`
>
> 或手动下载：
> https://github.com/cipher-wb/fengshen-skillAI/releases
`,
            'utf8'
          );
          stats.files++;
          continue;
        }
      }

      // 递归抽子目录
      const subStats = await copyDir(srcPath, path.join(dstDir, entry.name), options);
      stats.files += subStats.files;
      stats.bytes += subStats.bytes;
    } else if (entry.isFile()) {
      // sampleOnly 限制
      if (options.sampleOnly) {
        // 仅抽前 6 个代表样本
        if (stats.files >= 6) {
          stats.skipped++;
          continue;
        }
      }

      // 排除特定文件
      if (entry.name.endsWith('.pyc')) continue;
      if (entry.name === '.DS_Store') continue;

      const dstPath = options.hbsAll ? path.join(dstDir, entry.name + '.hbs') : path.join(dstDir, entry.name);
      const bytes = await copyFile(srcPath, dstPath);
      stats.files++;
      stats.bytes += bytes;
    }
  }
  return stats;
}

async function buildManifest(templatesDir) {
  const manifest = { version: 1, generatedAt: new Date().toISOString(), files: {} };

  async function walk(dir, baseDir) {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      const rel = posix(path.relative(baseDir, full));
      if (entry.isDirectory()) {
        await walk(full, baseDir);
      } else {
        const content = await fs.readFile(full, 'utf8').catch(() => null);
        if (content === null) continue;
        manifest.files[rel] = {
          sha256: sha256OfString(content),
          hbs: full.endsWith('.hbs'),
          py: full.endsWith('.py'),
          bytes: Buffer.byteLength(content, 'utf8')
        };
      }
    }
  }

  await walk(templatesDir, templatesDir);
  return manifest;
}

async function validateNoHardcoded(templatesDir) {
  const issues = [];
  async function walk(dir) {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await walk(full);
        continue;
      }
      const content = await fs.readFile(full, 'utf8').catch(() => null);
      if (!content) continue;
      // 不应残留绝对源路径
      if (content.includes('F:/DreamRivakes2/ClientPublish') || content.includes('F:\\DreamRivakes2\\ClientPublish')) {
        issues.push({ file: posix(path.relative(templatesDir, full)), kind: 'hardcoded-source-path' });
      }
      // 不应残留 1SkillEditor.xlsx 绝对路径
      if (content.includes('F:/DreamRivakes2/Design/Excel/excel/1SkillEditor.xlsx')) {
        issues.push({ file: posix(path.relative(templatesDir, full)), kind: 'hardcoded-excel-path' });
      }
    }
  }
  await walk(templatesDir);
  return issues;
}

async function main() {
  const args = parseArgs();

  console.log('═'.repeat(60));
  console.log('  extract-from-source.js — fengshen-skillai 模板抽源');
  console.log('═'.repeat(60));
  console.log(`  Source: ${args.source}`);
  console.log(`  Dest:   ${args.dest}`);
  console.log(`  Include batch_buffer: ${args.includeBatchBuffer}`);
  console.log('');

  // 检查源目录
  if (!await fs.pathExists(args.source)) {
    console.error(`✗ 源目录不存在: ${args.source}`);
    process.exit(1);
  }

  // 清空 templates 目录 (保留 _seed 内的 manifest README)
  if (await fs.pathExists(args.dest)) {
    console.log(`⚠ 清空 templates 目录: ${args.dest}`);
    await fs.emptyDir(args.dest);
  }

  // 按映射表抽
  let totalFiles = 0;
  let totalBytes = 0;
  for (const item of EXTRACT_MAP) {
    const srcPath = path.join(args.source, item.src);
    const dstPath = path.join(args.dest, item.dst);

    if (!await fs.pathExists(srcPath)) {
      if (item.optional) {
        console.log(`  ⊘ optional skip: ${item.src}`);
        continue;
      } else {
        console.warn(`  ⚠ 缺失: ${item.src}`);
        continue;
      }
    }

    if (item.isDir) {
      const stats = await copyDir(srcPath, dstPath, {
        excludeBatchBuffer: item.excludeBatchBuffer,
        excludePycache: item.excludePycache,
        sampleOnly: item.sampleOnly,
        hbsAll: item.hbsAll,
        includeBatchBuffer: args.includeBatchBuffer
      });
      console.log(`  ✓ ${item.src}/ → ${item.dst}/ (${stats.files} files / ${(stats.bytes / 1024).toFixed(1)}KB)`);
      totalFiles += stats.files;
      totalBytes += stats.bytes;
    } else {
      const bytes = await copyFile(srcPath, dstPath);
      console.log(`  ✓ ${item.src} → ${item.dst} (${(bytes / 1024).toFixed(1)}KB)`);
      totalFiles++;
      totalBytes += bytes;
    }
  }

  // 生成 manifest.json
  console.log('\n生成 templates/manifest.json...');
  const manifest = await buildManifest(args.dest);
  await fs.writeJson(path.join(args.dest, 'manifest.json'), manifest, { spaces: 2 });
  console.log(`  ✓ ${Object.keys(manifest.files).length} files in manifest`);

  // Validation
  console.log('\n校验 templates/ 无硬编码路径残留...');
  const issues = await validateNoHardcoded(args.dest);
  if (issues.length === 0) {
    console.log('  ✓ 0 个残留硬编码路径');
  } else {
    console.warn(`  ⚠ 发现 ${issues.length} 个残留硬编码路径:`);
    for (const issue of issues.slice(0, 10)) {
      console.warn(`    - ${issue.file} (${issue.kind})`);
    }
    if (issues.length > 10) console.warn(`    ... and ${issues.length - 10} more`);
  }

  console.log('\n═'.repeat(60));
  console.log(`完成 ✓ 总计 ${totalFiles} 文件 / ${(totalBytes / 1024 / 1024).toFixed(2)} MB`);
  console.log('═'.repeat(60));
}

main().catch((err) => {
  console.error('✗ 抽源失败:', err.message);
  console.error(err.stack);
  process.exit(1);
});
