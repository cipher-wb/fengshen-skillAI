// fengshen-skillai download-history [path] — 下载完整 batch_buffer 学习痕迹
import fs from 'fs-extra';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync, createReadStream, createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
import crypto from 'node:crypto';
import * as tar from 'tar';
import ora from 'ora';
import chalk from 'chalk';

import { log } from '../utils/logger.js';
import { normalize } from '../core/path-utils.js';
import { readConfig } from '../core/config.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(readFileSync(path.join(__dirname, '..', '..', 'package.json'), 'utf8'));

export async function downloadHistoryCommand(targetPath, options) {
  const projectRoot = normalize(targetPath || '.');
  const config = await readConfig(projectRoot);
  if (!config) {
    log.error('未找到 fengshen.config.json / 请先运行 npx fengshen-skillai init');
    process.exit(1);
  }

  const mentalModelVersion = options.version || pkg.fengshenMentalModelVersion;
  const cliVersion = pkg.version;

  // 构建 URL
  let url = options.url;
  if (!url) {
    const tpl = pkg.fengshenLearningHistoryUrl ||
      'https://github.com/cipher-wb/fengshen-skillAI/releases/download/v{cliVersion}/fengshen-learning-history-{mentalModelVersion}.tar.gz';
    url = tpl
      .replace('{cliVersion}', cliVersion)
      .replace('{mentalModelVersion}', mentalModelVersion);
  }

  log.hero('fengshen-skillai download-history');
  log.dim(`  URL: ${url}`);
  log.dim(`  Target: ${projectRoot}\n`);

  // 下载到临时文件
  const tmpDir = path.join(projectRoot, '.fengshen-skillai', 'tmp');
  await fs.ensureDir(tmpDir);
  const tarPath = path.join(tmpDir, `fengshen-learning-history-${mentalModelVersion}.tar.gz`);

  const spinner = ora(`下载 ${url}...`).start();
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} ${response.statusText}`);
    }
    const totalSize = Number(response.headers.get('content-length') || 0);
    spinner.text = `下载中... ${totalSize ? `(${(totalSize / 1024 / 1024).toFixed(1)} MB)` : ''}`;

    const fileStream = createWriteStream(tarPath);
    await pipeline(response.body, fileStream);
    spinner.succeed(`下载完成: ${tarPath}`);
  } catch (err) {
    spinner.fail(`下载失败: ${err.message}`);
    log.dim(`\n可能原因：`);
    log.dim(`  - 该版本 release 还未发布 (mental_model ${mentalModelVersion})`);
    log.dim(`  - 网络问题 (尝试 --url 手动指定 mirror)`);
    log.dim(`  - 私有仓库 / 需要 auth (Release asset 应是 public)`);
    process.exit(1);
  }

  // sha256 校验
  if (!options.noVerify && pkg.fengshenLearningHistorySha256) {
    const verifySpinner = ora('校验 sha256...').start();
    const expected = pkg.fengshenLearningHistorySha256;
    const actual = await fileSha256(tarPath);
    if (expected === actual) {
      verifySpinner.succeed(`sha256 校验通过: ${actual.substring(0, 12)}...`);
    } else {
      verifySpinner.fail(`sha256 不匹配 / 期望 ${expected.substring(0, 12)}... / 实际 ${actual.substring(0, 12)}...`);
      log.warn('用 --no-verify 跳过校验');
      process.exit(1);
    }
  }

  // 解压
  const extractSpinner = ora('解压到 doc/SkillAI/mental_model/batch_buffer/ 和 doc/SkillAI/samples/...').start();
  try {
    const docRoot = path.join(projectRoot, 'doc', 'SkillAI');
    await fs.ensureDir(path.join(docRoot, 'mental_model', 'batch_buffer'));
    await fs.ensureDir(path.join(docRoot, 'samples'));

    await tar.x({
      file: tarPath,
      cwd: docRoot,
      filter: (filePath) => {
        // 仅解压 mental_model/batch_buffer/ 和 samples/ 内的
        return filePath.startsWith('mental_model/batch_buffer/') || filePath.startsWith('samples/');
      }
    });

    extractSpinner.succeed('解压完成');
  } catch (err) {
    extractSpinner.fail(`解压失败: ${err.message}`);
    process.exit(1);
  }

  // 清理临时
  await fs.remove(tmpDir).catch(() => {});

  log.section('完成 ✨');
  log.info(`\n  ${chalk.bold('提示：')} 完整学习痕迹已落到:`);
  log.dim(`    - doc/SkillAI/mental_model/batch_buffer/B-001 ~ B-061 (yaml/json/py)`);
  log.dim(`    - doc/SkillAI/samples/  (完整 IR + JSON + markdown 样本)`);
  log.info('\n  现在你可以浏览 v0.16.39 mental_model 完整学习轨迹了\n');
}

async function fileSha256(filePath) {
  const hash = crypto.createHash('sha256');
  await pipeline(createReadStream(filePath), hash);
  return hash.digest('hex');
}
