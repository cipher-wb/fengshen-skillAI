// 读写 fengshen.config.json + schema 验证
import fs from 'fs-extra';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { posix, normalize } from './path-utils.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * 默认配置 (init 时生成)
 */
export function defaultConfig(projectRoot) {
  return {
    $schema: 'https://github.com/cipher-wb/fengshen-skillAI/raw/main/schemas/config.schema.json',
    _comment: 'fengshen-skillai 用户工程配置 / scaffold 落盘 / 每次 init 生成 / 后续 update 不覆盖用户字段',
    version: 1,
    project_root: '.',
    skillgraph_jsons_root: 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/',
    skill_excel_path: '',
    fengshen_skillai_version: '',
    mental_model_version: 'v0.16.41',
    installed_at: '',
    installed_by_cli: '',
    ai_id_segment: 250,
    default_skill_save_dir: 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/宗门技能/AIGen/',
    python_executable: 'python',
    update_strategy: 'backup-and-merge',
    auto_doctor_on_init: true,
    claude_plugin_mode: true
  };
}

/**
 * 读取 fengshen.config.json (如不存在 → 返回 null)
 */
export async function readConfig(projectRoot) {
  const configPath = path.join(projectRoot, 'fengshen.config.json');
  if (!(await fs.pathExists(configPath))) {
    return null;
  }
  const raw = await fs.readFile(configPath, 'utf8');
  return JSON.parse(raw);
}

/**
 * 写 fengshen.config.json
 */
export async function writeConfig(projectRoot, config) {
  const configPath = path.join(projectRoot, 'fengshen.config.json');
  // 路径字段 normalize 为 POSIX
  if (config.skillgraph_jsons_root) {
    config.skillgraph_jsons_root = posix(config.skillgraph_jsons_root);
  }
  if (config.skill_excel_path) {
    config.skill_excel_path = posix(config.skill_excel_path);
  }
  if (config.default_skill_save_dir) {
    config.default_skill_save_dir = posix(config.default_skill_save_dir);
  }
  await fs.writeFile(configPath, JSON.stringify(config, null, 2) + '\n', 'utf8');
}

/**
 * 验证配置 schema (轻量 / 不依赖 ajv)
 */
export function validateConfig(config) {
  const errors = [];
  if (!config) {
    errors.push('config 为 null');
    return errors;
  }
  if (config.version !== 1) {
    errors.push(`version 字段缺失或不等于 1 (当前: ${config.version})`);
  }
  const requiredFields = ['project_root', 'skillgraph_jsons_root', 'skill_excel_path'];
  for (const f of requiredFields) {
    if (!config[f] || config[f] === '') {
      errors.push(`必填字段 ${f} 缺失`);
    }
  }
  if (config.skill_excel_path && !config.skill_excel_path.toLowerCase().endsWith('.xlsx')) {
    errors.push(`skill_excel_path 必须指向 .xlsx 文件 (当前: ${config.skill_excel_path})`);
  }
  if (config.ai_id_segment !== undefined) {
    const n = Number(config.ai_id_segment);
    if (!Number.isInteger(n) || n < 100 || n > 999) {
      errors.push(`ai_id_segment 必须是 100-999 整数 (当前: ${config.ai_id_segment})`);
    }
  }
  return errors;
}

/**
 * 合并 update 时的配置 (保留用户字段)
 */
export function mergeConfig(oldConfig, newDefaults) {
  if (!oldConfig) return newDefaults;
  // 用户字段优先 / 仅更新 metadata
  return {
    ...newDefaults,
    project_root: oldConfig.project_root || newDefaults.project_root,
    skillgraph_jsons_root: oldConfig.skillgraph_jsons_root || newDefaults.skillgraph_jsons_root,
    skill_excel_path: oldConfig.skill_excel_path || newDefaults.skill_excel_path,
    ai_id_segment: oldConfig.ai_id_segment || newDefaults.ai_id_segment,
    default_skill_save_dir: oldConfig.default_skill_save_dir || newDefaults.default_skill_save_dir,
    python_executable: oldConfig.python_executable || newDefaults.python_executable,
    update_strategy: oldConfig.update_strategy || newDefaults.update_strategy,
    claude_plugin_mode: oldConfig.claude_plugin_mode !== undefined ? oldConfig.claude_plugin_mode : newDefaults.claude_plugin_mode,
    // metadata 强制更新
    fengshen_skillai_version: newDefaults.fengshen_skillai_version,
    mental_model_version: newDefaults.mental_model_version,
    installed_at: oldConfig.installed_at || newDefaults.installed_at, // 保留首次安装时间
    last_updated_at: newDefaults.installed_at,
    installed_by_cli: newDefaults.installed_by_cli
  };
}
