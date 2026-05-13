// chalk wrapper / 统一日志风格
import chalk from 'chalk';

export const log = {
  info(msg) {
    console.log(msg);
  },
  success(msg) {
    console.log(chalk.green('✓ ') + msg);
  },
  warn(msg) {
    console.log(chalk.yellow('⚠ ') + msg);
  },
  error(msg) {
    console.error(chalk.red('✗ ') + msg);
  },
  dim(msg) {
    console.log(chalk.dim(msg));
  },
  bold(msg) {
    console.log(chalk.bold(msg));
  },
  hero(title) {
    const line = '═'.repeat(56);
    console.log(chalk.cyan(`╔${line}╗`));
    console.log(chalk.cyan(`║`) + chalk.bold.cyan(`  ${title.padEnd(53)}`) + chalk.cyan(`║`));
    console.log(chalk.cyan(`╚${line}╝`));
  },
  section(title) {
    console.log('\n' + chalk.bold.cyan(`▎ ${title}`));
  },
  list(items, prefix = '  •') {
    for (const item of items) {
      console.log(`${prefix} ${item}`);
    }
  }
};
