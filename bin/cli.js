#!/usr/bin/env node
// fengshen-skillai CLI 入口 / commander 注册 5 子命令
import { Command } from 'commander';
import chalk from 'chalk';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync } from 'node:fs';

import { initCommand } from '../lib/commands/init.js';
import { doctorCommand } from '../lib/commands/doctor.js';
import { downloadHistoryCommand } from '../lib/commands/download-history.js';
import { updateCommand } from '../lib/commands/update.js';
import { versionCommand } from '../lib/commands/version.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pkg = JSON.parse(readFileSync(join(__dirname, '..', 'package.json'), 'utf8'));

const program = new Command();

program
  .name('fengshen-skillai')
  .description('Claude Code SkillAI 系统 for Unity SkillEditor — 自然语言 → mermaid → IR YAML → JSON 全流程')
  .version(`${pkg.version} (mental_model ${pkg.fengshenMentalModelVersion})`, '-v, --version', '打印版本信息');

// init
program
  .command('init')
  .description('Scaffold SkillAI 系统到目标 Unity 工程')
  .argument('[path]', '目标工程根路径', '.')
  .option('--skillgraph-root <p>', '自定义 SkillGraph_*.json 根目录路径', 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/')
  .option('--excel-path <p>', 'SkillEditor Excel 导出文件绝对路径')
  .option('--ai-id-segment <n>', 'AI 生成技能 ID 段位 (100-999)', '250')
  .option('--non-interactive', '跳过 prompts / 用默认 + flag 值')
  .option('--skip-config', '不生成 fengshen.config.json')
  .option('--no-plugin', '不安装 .claude-plugin/plugin.json')
  .option('--force', '已有 .claude/ 时直接覆盖 (默认 backup)')
  .option('--dry-run', '只打印将做的事 / 不实际写盘')
  .action(initCommand);

// update
program
  .command('update')
  .description('更新已 scaffold 的工程到最新模板版本')
  .argument('[path]', '目标工程根路径', '.')
  .option('--to-version <v>', '指定升级到的版本 (default: 最新)')
  .option('--dry-run', '只 show diff / 不写盘')
  .option('--auto-merge', '三方 merge 失败时默认 keep mine')
  .action(updateCommand);

// doctor
program
  .command('doctor')
  .description('健康检查 / scaffold 完整性 + 配置正确性')
  .argument('[path]', '目标工程根路径', '.')
  .option('--quiet', '只打印 fail / 不打印 pass')
  .option('--json', 'JSON 格式输出')
  .action(doctorCommand);

// download-history
program
  .command('download-history')
  .description('下载完整 batch_buffer 学习痕迹 (GitHub Release / ~44MB)')
  .argument('[path]', '目标工程根路径', '.')
  .option('--version <v>', '指定 mental_model 版本')
  .option('--url <u>', '手动覆盖 release asset URL')
  .option('--no-verify', '跳过 sha256 校验')
  .action(downloadHistoryCommand);

// version / info
program
  .command('version')
  .description('打印 fengshen-skillai + mental_model 详细版本信息')
  .alias('info')
  .action(versionCommand);

// hero (默认无参数显示帮助 + 推荐 init)
program.addHelpText('after', `
${chalk.cyan('快速开始')}：

  ${chalk.dim('# 在 Unity 工程根执行：')}
  $ npx fengshen-skillai init

  ${chalk.dim('# 指定路径：')}
  $ npx fengshen-skillai init D:/MyUnityProject

  ${chalk.dim('# 健康检查：')}
  $ npx fengshen-skillai doctor

  ${chalk.dim('# 下载完整学习痕迹 (可选)：')}
  $ npx fengshen-skillai download-history

${chalk.cyan('文档')}：
  https://github.com/cipher-wb/fengshen-skillAI

${chalk.dim(`mental_model: ${pkg.fengshenMentalModelVersion} / npm package: ${pkg.version}`)}
`);

program.parseAsync(process.argv).catch((err) => {
  console.error(chalk.red('\n✗ fengshen-skillai 执行失败:'));
  console.error(chalk.red(err.message || err));
  if (process.env.FENGSHEN_DEBUG === '1') {
    console.error(err.stack);
  }
  process.exit(1);
});
