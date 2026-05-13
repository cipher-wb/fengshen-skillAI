#!/usr/bin/env node
// scripts/test-init.js — e2e 测试 / 干净工程跑 init + 验证
import fs from 'fs-extra';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { posix } from '../lib/core/path-utils.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(__dirname, '..');
const TEST_DIR = path.join(REPO_ROOT, 'test', '.tmp', 'e2e-init');

async function cleanTestDir() {
  if (await fs.pathExists(TEST_DIR)) {
    await fs.remove(TEST_DIR);
  }
  await fs.ensureDir(path.join(TEST_DIR, 'Assets', 'Thirds', 'NodeEditor', 'SkillEditor', 'Saves', 'Jsons', '宗门技能'));
  // 创建一个 fake SkillGraph 让 detect 不报警
  await fs.writeFile(
    path.join(TEST_DIR, 'Assets', 'Thirds', 'NodeEditor', 'SkillEditor', 'Saves', 'Jsons', '宗门技能', 'SkillGraph_30122001_test.json'),
    '{"test": true}',
    'utf8'
  );
}

function runCli(args, cwd) {
  return new Promise((resolve, reject) => {
    const cliPath = path.join(REPO_ROOT, 'bin', 'cli.js');
    const proc = spawn('node', [cliPath, ...args], {
      cwd: cwd || REPO_ROOT,
      stdio: 'inherit'
    });
    proc.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`CLI exit code ${code}`));
    });
    proc.on('error', reject);
  });
}

async function fileExists(rel) {
  return await fs.pathExists(path.join(TEST_DIR, rel));
}

async function fileContains(rel, str) {
  const content = await fs.readFile(path.join(TEST_DIR, rel), 'utf8').catch(() => '');
  return content.includes(str);
}

async function fileNotContains(rel, str) {
  return !(await fileContains(rel, str));
}

async function assert(cond, msg) {
  if (cond) {
    console.log(`  ✓ ${msg}`);
  } else {
    console.error(`  ✗ ${msg}`);
    process.exitCode = 1;
  }
}

async function main() {
  console.log('═'.repeat(60));
  console.log('  fengshen-skillai e2e test');
  console.log('═'.repeat(60));

  console.log('\n[1/4] 准备干净测试工程...');
  await cleanTestDir();
  console.log(`  ✓ ${TEST_DIR}`);

  console.log('\n[2/4] 跑 init (non-interactive)...');
  await runCli([
    'init',
    TEST_DIR,
    '--non-interactive',
    '--skillgraph-root=Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/',
    '--excel-path=' + posix(path.join(TEST_DIR, 'fake.xlsx'))
  ]);

  console.log('\n[3/4] 验证 scaffold 产物...');

  // 必备文件
  await assert(await fileExists('fengshen.config.json'), 'fengshen.config.json 存在');
  await assert(await fileExists('.claude/agents/skill-designer.md'), '.claude/agents/skill-designer.md');
  await assert(await fileExists('.claude/agents/skill-reviewer.md'), '.claude/agents/skill-reviewer.md');
  await assert(await fileExists('.claude/agents/skill-knowledge-curator.md'), '.claude/agents/skill-knowledge-curator.md');
  await assert(await fileExists('.claude/agents/skill-knowledge-auditor.md'), '.claude/agents/skill-knowledge-auditor.md');
  await assert(await fileExists('.claude/skills/skill-design/SKILL.md'), '.claude/skills/skill-design/SKILL.md');
  await assert(await fileExists('.claude/skills/skill-review/SKILL.md'), '.claude/skills/skill-review/SKILL.md');
  await assert(await fileExists('.claude-plugin/plugin.json'), '.claude-plugin/plugin.json');
  await assert(await fileExists('doc/SkillAI/mental_model/README.md'), 'doc/SkillAI/mental_model/README.md');
  // CLAUDE.md (新命名) 或 CLAUDE.local.md (旧兼容)
  const hasClaudeMd = await fileExists('CLAUDE.md') || await fileExists('CLAUDE.local.md');
  await assert(hasClaudeMd, 'CLAUDE.md (或 CLAUDE.local.md)');
  await assert(await fileExists('.fengshen-skillai/install.json'), '.fengshen-skillai/install.json');

  // 占位符不残留
  await assert(await fileNotContains('.claude/agents/skill-designer.md', 'F:/DreamRivakes2/ClientPublish'), 'skill-designer.md 不含 F:/DreamRivakes2/ClientPublish');
  await assert(await fileNotContains('.claude/agents/skill-designer.md', '{{PROJECT_ROOT}}'), 'skill-designer.md 不含 {{PROJECT_ROOT}}');
  await assert(await fileNotContains('doc/SkillAI/mental_model/README.md', 'F:/DreamRivakes2'), 'mental_model/README.md 不含 F:/DreamRivakes2');

  // CLAUDE.md 含 fengshen 标记
  const claudeFile = await fs.pathExists(path.join(TEST_DIR, 'CLAUDE.md')) ? 'CLAUDE.md' : 'CLAUDE.local.md';
  await assert(await fileContains(claudeFile, '<!-- fengshen-skillai begin'), `${claudeFile} 含 fengshen-skillai begin 标记`);

  // fengshen.config.json 含正确路径
  const config = await fs.readJson(path.join(TEST_DIR, 'fengshen.config.json'));
  await assert(config.skill_excel_path.endsWith('fake.xlsx'), 'config.skill_excel_path 正确');
  await assert(config.skillgraph_jsons_root === 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/', 'config.skillgraph_jsons_root 正确');

  console.log('\n[4/4] 跑 doctor...');
  await runCli(['doctor', TEST_DIR, '--quiet']).catch((err) => {
    // doctor 退出码 1/2 是 warn/fail / 但这里 quiet 模式下我们只关注实际错误
    console.log('  (doctor 返回非 0 码 / 预期 / fake.xlsx 不存在 + Python deps 可能缺)');
  });

  console.log('\n' + '═'.repeat(60));
  if (process.exitCode) {
    console.error('  e2e 测试失败 ✗');
  } else {
    console.log('  e2e 测试通过 ✓');
  }
  console.log('═'.repeat(60));
}

main().catch((err) => {
  console.error('e2e 测试异常:', err.message);
  console.error(err.stack);
  process.exit(1);
});
