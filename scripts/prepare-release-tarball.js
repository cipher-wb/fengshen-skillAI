#!/usr/bin/env node
// scripts/prepare-release-tarball.js
// 准备 GitHub Release 资产 (完整 batch_buffer + samples) tar.gz
//
// 用法：
//   node scripts/prepare-release-tarball.js [--source <path>] [--out <path>]

import fs from 'fs-extra';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { argv } from 'node:process';
import { createReadStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
import * as tar from 'tar';

import pkg from '../package.json' with { type: 'json' };

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(__dirname, '..');

function parseArgs() {
  const args = {
    source: 'F:/DreamRivakes2/ClientPublish/DreamRivakes2_U3DProj',
    out: path.join(REPO_ROOT, `fengshen-learning-history-${pkg.fengshenMentalModelVersion}.tar.gz`)
  };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--source') args.source = argv[++i];
    else if (argv[i] === '--out') args.out = argv[++i];
  }
  return args;
}

async function fileSha256(filePath) {
  const hash = crypto.createHash('sha256');
  await pipeline(createReadStream(filePath), hash);
  return hash.digest('hex');
}

async function main() {
  const args = parseArgs();
  console.log('═'.repeat(60));
  console.log('  prepare-release-tarball.js');
  console.log('═'.repeat(60));
  console.log(`  Source: ${args.source}`);
  console.log(`  Out:    ${args.out}`);
  console.log(`  Mental model: ${pkg.fengshenMentalModelVersion}\n`);

  const srcDoc = path.join(args.source, 'doc', 'SkillAI');
  if (!await fs.pathExists(srcDoc)) {
    console.error(`✗ 源 doc/SkillAI/ 不存在: ${srcDoc}`);
    process.exit(1);
  }

  // 暂存目录
  const stagingDir = path.join(REPO_ROOT, '.release-staging', 'full');
  await fs.emptyDir(stagingDir);

  // 复制完整 batch_buffer (不排除 B-* 学习痕迹)
  console.log('复制 mental_model/batch_buffer/ ...');
  await fs.copy(
    path.join(srcDoc, 'mental_model', 'batch_buffer'),
    path.join(stagingDir, 'mental_model', 'batch_buffer'),
    {
      filter: (s) => !s.includes('__pycache__') && !s.endsWith('.pyc')
    }
  );

  // 复制完整 samples/
  console.log('复制 samples/ ...');
  await fs.copy(
    path.join(srcDoc, 'samples'),
    path.join(stagingDir, 'samples'),
    {
      filter: (s) => !s.includes('_archive_v08_failed')
    }
  );

  // 打 tar.gz
  console.log(`\n打包 ${args.out}...`);
  await tar.c(
    {
      gzip: true,
      file: args.out,
      cwd: stagingDir,
      portable: true
    },
    ['.']
  );

  // sha256
  const sha = await fileSha256(args.out);
  const shaPath = args.out + '.sha256';
  await fs.writeFile(shaPath, sha + '  ' + path.basename(args.out) + '\n', 'utf8');

  const stats = await fs.stat(args.out);

  console.log('\n═'.repeat(60));
  console.log('完成 ✓');
  console.log(`  Tarball: ${args.out}`);
  console.log(`  Size:    ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  SHA256:  ${sha}`);
  console.log(`  ${shaPath}`);
  console.log('═'.repeat(60));

  console.log('\n下一步：');
  console.log(`  1. 把 ${sha} 填到 package.json#fengshenLearningHistorySha256`);
  console.log(`  2. gh release create v${pkg.version} --notes-file CHANGELOG.md ${args.out} ${shaPath}`);

  // 清理 staging
  await fs.remove(path.join(REPO_ROOT, '.release-staging'));
}

main().catch((err) => {
  console.error('✗ 失败:', err.message);
  console.error(err.stack);
  process.exit(1);
});
