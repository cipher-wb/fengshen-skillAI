// fengshen-skillai update [path] — 更新已 scaffold 的工程到新版本 (v1.1 / stub)
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';

import { log } from '../utils/logger.js';
import { normalize } from '../core/path-utils.js';
import { readConfig } from '../core/config.js';
import { readInstallManifest } from '../core/manifest.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(readFileSync(path.join(__dirname, '..', '..', 'package.json'), 'utf8'));

export async function updateCommand(targetPath, options) {
  const projectRoot = normalize(targetPath || '.');
  log.hero(`fengshen-skillai update v${pkg.version}`);

  const config = await readConfig(projectRoot);
  if (!config) {
    log.error('未找到 fengshen.config.json / 请先运行 npx fengshen-skillai init');
    process.exit(1);
  }

  const manifest = await readInstallManifest(projectRoot);
  log.dim(`  当前安装版本: ${config.fengshen_skillai_version} (mental_model ${config.mental_model_version})`);
  log.dim(`  最新可用版本: ${pkg.version} (mental_model ${pkg.fengshenMentalModelVersion})`);

  if (config.fengshen_skillai_version === pkg.version &&
      config.mental_model_version === pkg.fengshenMentalModelVersion) {
    log.success('已是最新版本 / 无需更新');
    return;
  }

  log.warn(`\n  ⚠ update 命令在 v1.1 完整实现 (三方 merge / 保护用户本地改动)`);
  log.info(`\n  v1.0 临时方案：备份当前工程 + 重新跑 init`);
  log.info(`\n  推荐流程：`);
  log.dim(`    1. cp -r ${projectRoot}/.claude  ${projectRoot}/.claude.bak.$(date +%s)`);
  log.dim(`    2. cp -r ${projectRoot}/doc/SkillAI  ${projectRoot}/doc/SkillAI.bak.$(date +%s)`);
  log.dim(`    3. npx fengshen-skillai@latest init ${projectRoot} --force`);
  log.dim(`    4. 手动 diff 备份 vs 新版 / 把你的本地改动 merge 回来`);
  log.dim(`    5. 删备份`);

  log.info(`\n  自动 update 计划于 v1.1 发布 (T+3 weeks 后)`);
}
