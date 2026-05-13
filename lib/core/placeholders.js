// handlebars context builder + Python 自定义 placeholder 处理
import Handlebars from 'handlebars';
import path from 'node:path';
import { posix, windows } from './path-utils.js';

/**
 * 构建 handlebars 渲染上下文
 * @param {Object} config - fengshen.config.json 内容
 * @param {string} projectRoot - 目标工程绝对路径
 * @returns {Object}
 */
export function buildContext(config, projectRoot) {
  const root = path.resolve(projectRoot);
  const skillgraphRel = config.skillgraph_jsons_root || 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/';
  const skillgraphAbs = path.isAbsolute(skillgraphRel)
    ? skillgraphRel
    : path.join(root, skillgraphRel);

  const excelPath = config.skill_excel_path || '';
  // SKILL_EXCEL_DIR derived 自 skill_excel_path 的 dirname (用户不需要单独填)
  // 例：F:/MyTeam/Design/Excel/excel/1SkillEditor.xlsx → F:/MyTeam/Design/Excel/excel
  const excelDir = excelPath ? path.dirname(excelPath) : '';

  return {
    PROJECT_ROOT: posix(root),
    PROJECT_ROOT_WIN: windows(root),
    SKILLGRAPH_JSONS_ROOT: posix(skillgraphRel).replace(/\/$/, '') + '/',
    SKILLGRAPH_JSONS_ROOT_ABS: posix(skillgraphAbs).replace(/\/$/, '') + '/',
    SKILLGRAPH_JSONS_ROOT_WIN: windows(skillgraphRel),
    SKILL_EXCEL_PATH: posix(excelPath),
    SKILL_EXCEL_PATH_WIN: windows(excelPath),
    SKILL_EXCEL_DIR: posix(excelDir),
    SKILL_EXCEL_DIR_WIN: windows(excelDir),
    AI_ID_SEGMENT: config.ai_id_segment || 250,
    DEFAULT_SKILL_SAVE_DIR: posix(config.default_skill_save_dir || 'Assets/Thirds/NodeEditor/SkillEditor/Saves/Jsons/宗门技能/AIGen/'),
    FENGSHEN_VERSION: config.fengshen_skillai_version || '',
    MENTAL_MODEL_VERSION: config.mental_model_version || 'v0.16.40',
    INSTALL_TIMESTAMP: new Date().toISOString(),
    PYTHON_EXEC: config.python_executable || 'python'
  };
}

// 注册 handlebars helpers
Handlebars.registerHelper('quote', (str) => `"${str}"`);
Handlebars.registerHelper('posix', (str) => posix(str));
Handlebars.registerHelper('windows', (str) => windows(str));
Handlebars.registerHelper('json', (obj) => JSON.stringify(obj, null, 2));

/**
 * 渲染 handlebars 模板字符串
 * @param {string} content - 模板源
 * @param {Object} context - 渲染上下文
 * @returns {string}
 */
export function renderHandlebars(content, context) {
  const template = Handlebars.compile(content, { noEscape: true });
  return template(context);
}

/**
 * 渲染 Python 自定义 placeholder
 * Python 文件用 `<<PROJECT_ROOT>>` 避开 dict `{{}}` 冲突
 * @param {string} content
 * @param {Object} context
 * @returns {string}
 */
export function renderPythonPlaceholders(content, context) {
  let result = content;
  for (const [key, value] of Object.entries(context)) {
    const placeholder = `<<${key}>>`;
    if (result.includes(placeholder)) {
      // Python 字符串中可能含 backslash / 需 escape
      const escaped = String(value).replace(/\\/g, '/');
      result = result.split(placeholder).join(escaped);
    }
  }
  return result;
}

/**
 * 智能渲染 (按文件名自动选择 handlebars 还是 Python placeholder)
 */
export function renderTemplate(filename, content, context) {
  if (filename.endsWith('.py') || filename.endsWith('.py.hbs')) {
    return renderPythonPlaceholders(content, context);
  }
  return renderHandlebars(content, context);
}

/**
 * 检测内容中残留的占位符 (verification 用)
 * @param {string} content
 * @returns {Array<string>} 残留占位符列表
 */
export function findUnresolvedPlaceholders(content) {
  const unresolved = [];
  // handlebars
  const hbsMatch = content.match(/\{\{[A-Z_]+\}\}/g);
  if (hbsMatch) unresolved.push(...hbsMatch);
  // python custom
  const pyMatch = content.match(/<<[A-Z_]+>>/g);
  if (pyMatch) unresolved.push(...pyMatch);
  return [...new Set(unresolved)];
}
