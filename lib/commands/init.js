// fengshen-skillai init [path] — 核心 scaffold 命令
import fs from 'fs-extra';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';
import ora from 'ora';
import chalk from 'chalk';

import { log } from '../utils/logger.js';
import { askInput, askSelect, askConfirm } from '../utils/prompt.js';
import { detectUnityProject, detectSkillEditor, normalize, posix, pathExists } from '../core/path-utils.js';
import { defaultConfig, writeConfig, validateConfig } from '../core/config.js';
import { buildContext } from '../core/placeholders.js';
import {
  collectTemplateFiles,
  computeTargetPath,
  renderAndWrite,
  getTemplatesRoot
} from '../core/template-engine.js';
import { mergeClaudeMd, resolveClaudeDirConflict } from '../core/conflict-resolver.js';
import {
  newInstallManifest,
  writeInstallManifest,
  readInstallManifest,
  sha256OfFile
} from '../core/manifest.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(readFileSync(path.join(__dirname, '..', '..', 'package.json'), 'utf8'));

export async function initCommand(targetPath, options) {
  const projectRoot = normalize(targetPath || '.');

  // Hero
  log.hero(`fengshen-skillai v${pkg.version} • FengshenForge`);
  log.dim(`  Claude Code SkillAI System for Unity SkillEditor`);
  log.dim(`  mental_model: ${pkg.fengshenMentalModelVersion}\n`);

  // 1. 工程目录检查
  if (!(await fs.pathExists(projectRoot))) {
    log.warn(`目标目录不存在: ${projectRoot}`);
    if (!options.nonInteractive) {
      const create = await askConfirm({
        message: `是否创建目录 ${projectRoot}?`,
        default: true
      });
      if (!create) {
        log.error('已取消');
        process.exit(1);
      }
    }
    await fs.ensureDir(projectRoot);
  }

  const isUnity = detectUnityProject(projectRoot);
  if (!isUnity) {
    log.warn(`目标目录未检测到 Unity 工程标志 (Assets/ 目录不存在): ${projectRoot}`);
    log.dim('  仍可继续 (适合自定义 SkillEditor 路径 / 非标准 Unity 工程)');
    if (!options.nonInteractive) {
      const cont = await askConfirm({ message: '是否继续?', default: true });
      if (!cont) process.exit(0);
    }
  } else {
    log.success(`检测到 Unity 工程: ${projectRoot}`);
  }

  // 2. 收集配置参数
  const config = defaultConfig(projectRoot);
  config.project_root = '.';
  config.fengshen_skillai_version = pkg.version;
  config.mental_model_version = pkg.fengshenMentalModelVersion;
  config.installed_at = new Date().toISOString();
  config.installed_by_cli = `fengshen-skillai/${pkg.version}`;

  if (options.skillgraphRoot) {
    config.skillgraph_jsons_root = options.skillgraphRoot;
  } else if (!options.nonInteractive) {
    const choices = [
      { name: 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/  (默认 / 《封神》风格)', value: 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/' },
      { name: 'Assets/SkillEditor/Saves/Jsons/  (简化版)', value: 'Assets/SkillEditor/Saves/Jsons/' },
      { name: '自定义路径...', value: '__custom__' }
    ];
    const sel = await askSelect({
      message: 'SkillGraph_*.json 根目录 (相对 project_root)：',
      choices,
      default: choices[0].value
    });
    if (sel === '__custom__') {
      config.skillgraph_jsons_root = await askInput({
        message: '输入自定义路径：',
        default: 'Assets/SkillEditor/Saves/Jsons/'
      });
    } else {
      config.skillgraph_jsons_root = sel;
    }
  }

  if (options.excelPath) {
    config.skill_excel_path = posix(normalize(options.excelPath));
  } else if (!options.nonInteractive) {
    config.skill_excel_path = posix(normalize(await askInput({
      message: 'SkillEditor 导出 Excel 绝对路径 (1SkillEditor.xlsx)：',
      default: '',
      validate: (v) => {
        if (!v.trim()) return '路径不能为空 / 即使文件暂不存在也请填预期路径';
        if (!v.toLowerCase().endsWith('.xlsx')) return '必须是 .xlsx 文件';
        return true;
      }
    })));
  } else {
    config.skill_excel_path = options.excelPath || '/path/to/your/1SkillEditor.xlsx';
  }

  if (options.aiIdSegment) {
    config.ai_id_segment = parseInt(options.aiIdSegment, 10);
  }

  // 3. 验证配置
  const errors = validateConfig(config);
  if (errors.length > 0) {
    log.error('配置验证失败：');
    for (const e of errors) log.error('  ' + e);
    process.exit(1);
  }

  // 4. 冲突处理
  const claudeDir = path.join(projectRoot, '.claude');
  let conflictStrategy = 'backup-and-overwrite';
  if (await fs.pathExists(claudeDir) && !options.force && !options.nonInteractive) {
    log.warn(`\n.claude/ 目录已存在: ${claudeDir}`);
    conflictStrategy = await askSelect({
      message: '如何处理？',
      choices: [
        { name: '备份现有 .claude/ 为 .claude.bak.<ts> 后覆盖 (推荐)', value: 'backup-and-overwrite' },
        { name: '合并 (仅新增 fengshen-* agents / 不覆盖已有)', value: 'merge' },
        { name: '强制覆盖 (危险 / 不备份)', value: 'force' },
        { name: '中止', value: 'abort' }
      ],
      default: 'backup-and-overwrite'
    });
    if (conflictStrategy === 'abort') {
      log.error('已取消');
      process.exit(0);
    }
  } else if (options.force) {
    conflictStrategy = 'force';
  }

  // 5. dry-run 模式打印计划
  if (options.dryRun) {
    log.section('Dry Run - 将执行的操作:');
    log.info(`  • 创建 fengshen.config.json (project_root=${config.project_root})`);
    log.info(`  • 创建 .claude/agents/ (4 agents)`);
    log.info(`  • 创建 .claude/skills/{skill-design,skill-review}/`);
    log.info(`  • 创建 doc/SkillAI/ (mental_model + postmortem + tools + docs + samples)`);
    log.info(`  • 创建 CLAUDE.local.md (含 fengshen 段)`);
    if (options.plugin !== false) {
      log.info(`  • 创建 .claude-plugin/plugin.json`);
    }
    log.info(`\n实际执行去掉 --dry-run 标志`);
    return;
  }

  // 6. 处理 .claude/ 冲突
  const conflictResult = await resolveClaudeDirConflict(claudeDir, conflictStrategy);
  if (conflictResult.backupPath) {
    log.success(`已备份现有 .claude/agents/ → ${conflictResult.backupPath}`);
  }

  // 7. 收集模板文件
  const spinner = ora('收集 templates...').start();
  const tplFiles = await collectTemplateFiles();
  spinner.succeed(`收集 ${tplFiles.length} 个模板文件`);

  // 8. 构建渲染上下文
  const context = buildContext(config, projectRoot);

  // 9. 渲染并写入
  const manifestData = newInstallManifest(pkg.version, pkg.fengshenMentalModelVersion);
  const renderSpinner = ora('渲染并写入模板...').start();
  let rendered = 0;
  let skipped = 0;
  // 找 CLAUDE.md 模板 (兼容 .md.hbs / .local.md.hbs 两种命名 / 优先 .md.hbs)
  const claudeMdSrc = tplFiles.find((t) =>
    (t.relPath === 'CLAUDE.md.hbs' || t.relPath === 'CLAUDE.local.md.hbs') && t.targetSubdir === ''
  );

  for (const tplFile of tplFiles) {
    // 特殊文件：CLAUDE.md 走合并策略
    if (tplFile === claudeMdSrc) continue;

    // 特殊文件：fengshen.config.json 单独处理
    if (tplFile.relPath === 'fengshen.config.json.hbs') continue;

    // plugin manifest 控制
    if (!options.plugin && tplFile.relPath.startsWith('.claude-plugin/')) {
      skipped++;
      continue;
    }

    try {
      const result = await renderAndWrite(tplFile, projectRoot, context);
      manifestData.files[posix(path.relative(projectRoot, result.targetPath))] = {
        sha256: result.hash,
        owner: 'fengshen-skillai',
        source_template: tplFile.relPath,
        action: result.action
      };
      rendered++;
    } catch (err) {
      renderSpinner.fail(`渲染失败: ${tplFile.relPath}`);
      throw err;
    }
  }
  renderSpinner.succeed(`渲染并写入 ${rendered} 个文件 (跳过 ${skipped})`);

  // 10. 写 fengshen.config.json
  await writeConfig(projectRoot, config);
  log.success('写入 fengshen.config.json');

  // 11. 处理 CLAUDE.md (特殊合并 / 如目标工程已有团队级 CLAUDE.md 则合并 fengshen 段不覆盖)
  if (claudeMdSrc) {
    const claudeMdPath = path.join(projectRoot, 'CLAUDE.md');
    const raw = await fs.readFile(claudeMdSrc.src, 'utf8');
    const { renderTemplate } = await import('../core/placeholders.js');
    const rendered = renderTemplate('CLAUDE.md', raw, context);
    const result = await mergeClaudeMd(claudeMdPath, rendered);
    log.success(`处理 CLAUDE.md: ${result.action}`);
  }

  // 12. 写 install manifest
  await writeInstallManifest(projectRoot, manifestData);

  // 13. Post-install hints
  log.section('安装完成 ✨');
  log.info(`
  ${chalk.bold.yellow('⚠️  确认前置依赖已装：')}
  ${chalk.dim('Node 18+ / Python 3.10+ / Git / Claude Code CLI / CC Switch')}
  ${chalk.dim('详见 https://github.com/cipher-wb/fengshen-skillAI#%EF%B8%8F-%E5%89%8D%E7%BD%AE%E4%BE%9D%E8%B5%96')}

  ${chalk.bold('下一步：')}

  ${chalk.dim('# 1. 检查 Python 装好了 (重要 - 没装 pip 后面会报错)')}
  $ python --version    ${chalk.dim('# 应看到 Python 3.10+ / 否则去 python.org 装 (Windows 装时勾 "Add Python to PATH")')}
  $ pip --version       ${chalk.dim('# 应有版本号')}

  ${chalk.dim('# 2. 安装 Python 工具依赖：')}
  $ cd ${projectRoot}
  $ pip install -r doc/SkillAI/tools/requirements.txt
  ${chalk.dim('# 如果报错 "pip 不是内部或外部命令" = Python 没装 / 看上面第 1 步')}

  ${chalk.dim('# 3. 检查 Claude Code 装了 (没装的话):')}
  $ claude --version
  ${chalk.dim('# 没装 → 跑: npm install -g @anthropic-ai/claude-code')}
  ${chalk.dim('# 配 API Key 用 CC Switch (桌面 GUI / https://github.com/farion1231/cc-switch/releases)')}
  ${chalk.dim('# 不需要登录 Anthropic 官方账号')}

  ${chalk.dim('# 4. 配置个人 user_config.json：')}
  $ cp doc/SkillAI/tools/user_config.json.example doc/SkillAI/tools/user_config.json
  ${chalk.dim('# 编辑 user_config.json → 设置你的 IPv4 末段等')}

  ${chalk.bold.cyan('# 5. ⚠️ 重要：在 Unity 工程根（当前目录）跑 claude / 别在其他目录！')}
  $ cd ${projectRoot}    ${chalk.dim('# 必须在含 .claude/ 那一层')}
  $ claude
  > 配一个木宗门的直线子弹技能 (示例)

  ${chalk.dim('# 6. 健康检查 (随时跑 / 自动检测 Python+Claude+各项配置)：')}
  $ npx fengshen-skillai doctor

  ${chalk.dim('# 7. 想看完整学习痕迹？(可选 / ~3.5MB tarball)：')}
  $ npx fengshen-skillai download-history
`);
}
