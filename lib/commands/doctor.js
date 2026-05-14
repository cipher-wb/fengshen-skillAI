// fengshen-skillai doctor [path] — 健康检查 / 10 项验证
import fs from 'fs-extra';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';
import { exec as execCb } from 'node:child_process';
import { promisify } from 'node:util';

import { log } from '../utils/logger.js';
import { normalize, pathExists } from '../core/path-utils.js';
import { readConfig, validateConfig } from '../core/config.js';
import { readInstallManifest } from '../core/manifest.js';

const exec = promisify(execCb);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(readFileSync(path.join(__dirname, '..', '..', 'package.json'), 'utf8'));

export async function doctorCommand(targetPath, options) {
  const projectRoot = normalize(targetPath || '.');
  const checks = [];

  log.hero(`fengshen-skillai doctor v${pkg.version}`);
  log.dim(`  Project: ${projectRoot}\n`);

  // [1] fengshen.config.json 存在且 schema 合法
  const config = await readConfig(projectRoot);
  if (!config) {
    checks.push({ id: 1, status: 'fail', msg: 'fengshen.config.json 不存在 (运行 npx fengshen-skillai init)' });
  } else {
    const errors = validateConfig(config);
    if (errors.length > 0) {
      checks.push({ id: 1, status: 'fail', msg: `fengshen.config.json schema 不合法: ${errors[0]}` });
    } else {
      checks.push({ id: 1, status: 'pass', msg: 'fengshen.config.json 存在且 schema 合法' });
    }
  }

  // [2] skillgraph_jsons_root 解析到存在的目录
  if (config) {
    const skillgraphAbs = path.isAbsolute(config.skillgraph_jsons_root)
      ? config.skillgraph_jsons_root
      : path.join(projectRoot, config.skillgraph_jsons_root);
    if (pathExists(skillgraphAbs, 'dir')) {
      checks.push({ id: 2, status: 'pass', msg: `skillgraph_jsons_root 存在: ${config.skillgraph_jsons_root}` });
    } else {
      checks.push({ id: 2, status: 'warn', msg: `skillgraph_jsons_root 目录不存在: ${skillgraphAbs} (可能 Unity 工程未导入)` });
    }
  }

  // [3] skill_excel_path 解析到存在的文件
  if (config) {
    if (pathExists(config.skill_excel_path, 'file')) {
      checks.push({ id: 3, status: 'pass', msg: `skill_excel_path 存在: ${config.skill_excel_path}` });
    } else {
      checks.push({ id: 3, status: 'warn', msg: `skill_excel_path 文件不存在: ${config.skill_excel_path}` });
    }
  }

  // [4] .claude/agents/ 4 个 fengshen agent 齐全
  const agentsDir = path.join(projectRoot, '.claude', 'agents');
  const expectedAgents = ['skill-designer.md', 'skill-reviewer.md', 'skill-knowledge-curator.md', 'skill-knowledge-auditor.md'];
  const missingAgents = [];
  for (const a of expectedAgents) {
    if (!await fs.pathExists(path.join(agentsDir, a))) {
      missingAgents.push(a);
    }
  }
  if (missingAgents.length === 0) {
    checks.push({ id: 4, status: 'pass', msg: '.claude/agents/ 4 个 fengshen agent 齐全' });
  } else {
    checks.push({ id: 4, status: 'fail', msg: `.claude/agents/ 缺少: ${missingAgents.join(', ')}` });
  }

  // [5] .claude/skills/skill-design + skill-review SKILL.md 存在
  const skillsDir = path.join(projectRoot, '.claude', 'skills');
  const expectedSkills = ['skill-design/SKILL.md', 'skill-review/SKILL.md'];
  const missingSkills = expectedSkills.filter((s) => !pathExists(path.join(skillsDir, s), 'file'));
  if (missingSkills.length === 0) {
    checks.push({ id: 5, status: 'pass', msg: '.claude/skills/{skill-design,skill-review} 完整' });
  } else {
    checks.push({ id: 5, status: 'fail', msg: `缺少 skill: ${missingSkills.join(', ')}` });
  }

  // [6] mental_model/README.md 存在且版本号
  const mmReadme = path.join(projectRoot, 'doc', 'SkillAI', 'mental_model', 'README.md');
  if (await fs.pathExists(mmReadme)) {
    const content = await fs.readFile(mmReadme, 'utf8');
    const versionMatch = content.match(/mental_model_version[:：]\s*(v[\d.]+)/);
    if (versionMatch) {
      checks.push({ id: 6, status: 'pass', msg: `mental_model 版本: ${versionMatch[1]}` });
    } else {
      checks.push({ id: 6, status: 'warn', msg: 'mental_model/README.md 存在但未识别版本号' });
    }
  } else {
    checks.push({ id: 6, status: 'fail', msg: 'doc/SkillAI/mental_model/README.md 不存在' });
  }

  // [7a] Python 本身是否装了
  const pyExec = config?.python_executable || 'python';
  let pythonInstalled = false;
  try {
    const { stdout } = await exec(`${pyExec} --version`);
    pythonInstalled = true;
    const pyVersion = stdout.trim();
    checks.push({ id: '7a', status: 'pass', msg: `Python 已安装: ${pyVersion}` });
  } catch (err) {
    checks.push({
      id: '7a',
      status: 'fail',
      msg: `Python 未安装或不在 PATH (运行 \`${pyExec} --version\` 失败) — 去 https://www.python.org/downloads/ 装 Python 3.10+ / Windows 装时勾 "Add Python to PATH"`
    });
  }

  // [7b] Python 依赖 (仅在 Python 装好时检查)
  if (pythonInstalled) {
    try {
      await exec(`${pyExec} -c "import yaml, jsonschema, openpyxl"`);
      checks.push({ id: '7b', status: 'pass', msg: 'Python 依赖齐全 (pyyaml, jsonschema, openpyxl)' });
    } catch (err) {
      checks.push({
        id: '7b',
        status: 'warn',
        msg: `Python 依赖缺失 (运行: pip install -r doc/SkillAI/tools/requirements.txt)`
      });
    }
  } else {
    checks.push({
      id: '7b',
      status: 'warn',
      msg: 'Python 依赖检查跳过 (Python 未装 / 先看 7a)'
    });
  }

  // [8] user_config.json
  const userConfigPath = path.join(projectRoot, 'doc', 'SkillAI', 'tools', 'user_config.json');
  const userConfigExample = path.join(projectRoot, 'doc', 'SkillAI', 'tools', 'user_config.json.example');
  if (await fs.pathExists(userConfigPath)) {
    checks.push({ id: 8, status: 'pass', msg: 'tools/user_config.json 存在' });
  } else if (await fs.pathExists(userConfigExample)) {
    checks.push({
      id: 8,
      status: 'warn',
      msg: 'tools/user_config.json 缺失 (运行 cp tools/user_config.json.example tools/user_config.json)'
    });
  } else {
    checks.push({ id: 8, status: 'warn', msg: 'tools/user_config.json 缺失' });
  }

  // [9] CLAUDE.md 含 fengshen 段 (兼容旧版 CLAUDE.local.md)
  const claudeMd = path.join(projectRoot, 'CLAUDE.md');
  const claudeLocalMd = path.join(projectRoot, 'CLAUDE.local.md');
  let claudeFile = null;
  if (await fs.pathExists(claudeMd)) claudeFile = claudeMd;
  else if (await fs.pathExists(claudeLocalMd)) claudeFile = claudeLocalMd;

  if (claudeFile) {
    const content = await fs.readFile(claudeFile, 'utf8');
    const name = path.basename(claudeFile);
    if (content.includes('<!-- fengshen-skillai begin')) {
      checks.push({ id: 9, status: 'pass', msg: `${name} 含 fengshen-skillai 段` });
    } else {
      checks.push({ id: 9, status: 'warn', msg: `${name} 不含 fengshen-skillai 段标记` });
    }
  } else {
    checks.push({ id: 9, status: 'fail', msg: 'CLAUDE.md / CLAUDE.local.md 都不存在' });
  }

  // [9.5] Claude Code CLI 是否装了
  try {
    const { stdout } = await exec('claude --version');
    checks.push({ id: '9.5', status: 'pass', msg: `Claude Code CLI: ${stdout.trim().split('\n')[0]}` });
  } catch (err) {
    checks.push({
      id: '9.5',
      status: 'fail',
      msg: 'Claude Code CLI 未装 / 跑: npm install -g @anthropic-ai/claude-code (国内慢用 npm config set registry https://registry.npmmirror.com)'
    });
  }

  // [10] install manifest
  const manifest = await readInstallManifest(projectRoot);
  if (manifest) {
    const fileCount = Object.keys(manifest.files || {}).length;
    checks.push({
      id: 10,
      status: 'pass',
      msg: `安装 manifest: v${manifest.fengshen_skillai_version} / mental_model ${manifest.mental_model_version} / ${fileCount} 文件`
    });
  } else {
    checks.push({ id: 10, status: 'warn', msg: '.fengshen-skillai/install.json 不存在 (可能旧版本安装)' });
  }

  // 输出
  if (options.json) {
    console.log(JSON.stringify({ projectRoot, version: pkg.version, mentalModel: pkg.fengshenMentalModelVersion, checks }, null, 2));
    return;
  }

  log.section(`检查结果 (${checks.length}/${checks.length})`);
  let passCount = 0, warnCount = 0, failCount = 0;
  for (const c of checks) {
    if (c.status === 'pass') {
      if (!options.quiet) log.success(`[${c.id}/${checks.length}] ${c.msg}`);
      passCount++;
    } else if (c.status === 'warn') {
      log.warn(`[${c.id}/${checks.length}] ${c.msg}`);
      warnCount++;
    } else {
      log.error(`[${c.id}/${checks.length}] ${c.msg}`);
      failCount++;
    }
  }

  console.log();
  log.bold(`总结: ${passCount} pass / ${warnCount} warn / ${failCount} fail`);

  if (failCount > 0) {
    process.exit(2);
  } else if (warnCount > 0) {
    process.exit(1);
  }
}
