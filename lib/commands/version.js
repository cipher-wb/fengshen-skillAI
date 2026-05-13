// fengshen-skillai version / info — 打印详细版本信息
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';
import chalk from 'chalk';

import { log } from '../utils/logger.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(readFileSync(path.join(__dirname, '..', '..', 'package.json'), 'utf8'));

export async function versionCommand() {
  log.hero(`fengshen-skillai v${pkg.version}`);
  console.log('');
  console.log(chalk.bold('  组件版本：'));
  console.log(`    fengshen-skillai npm: ${chalk.cyan(pkg.version)}`);
  console.log(`    mental_model:         ${chalk.cyan(pkg.fengshenMentalModelVersion)}`);
  console.log(`    Node.js:              ${chalk.cyan(process.version)}`);
  console.log('');
  console.log(chalk.bold('  系统组件：'));
  console.log(`    4 agent (peer review 闭环)：`);
  console.log(`      • skill-designer (红队 / 配技能)`);
  console.log(`      • skill-reviewer (绿队 / 审技能)`);
  console.log(`      • skill-knowledge-curator (蓝队 / Bootstrap 学习)`);
  console.log(`      • skill-knowledge-auditor (橙队 / 5 维度严审)`);
  console.log(`    2 skill: skill-design / skill-review`);
  console.log(`    16 mental_model 子系统页`);
  console.log(`    38+ PostMortem`);
  console.log(`    13 Python 工具`);
  console.log('');
  console.log(chalk.bold('  心智模型：'));
  console.log(`    15 升正式不变量 (D-5401 NSC 模板族 / D-3801 ET=0 / D-2401 master-flag-any-True / etc.)`);
  console.log(`    7 道防线 enforce (Gate (a)~(g) v3)`);
  console.log(`    rule_2 永不 silent delete`);
  console.log('');
  console.log(chalk.bold('  Links：'));
  console.log(`    Homepage:      ${pkg.homepage}`);
  console.log(`    Repository:    ${pkg.repository.url}`);
  console.log(`    Issues:        ${pkg.bugs.url}`);
  console.log('');
}
