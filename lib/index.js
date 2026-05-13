// fengshen-skillai 主入口 (programmatic API)
// 用户也可以 import { initCommand, doctorCommand } from 'fengshen-skillai' 调用
export { initCommand } from './commands/init.js';
export { doctorCommand } from './commands/doctor.js';
export { downloadHistoryCommand } from './commands/download-history.js';
export { updateCommand } from './commands/update.js';
export { versionCommand } from './commands/version.js';

export { readConfig, writeConfig, validateConfig, defaultConfig } from './core/config.js';
export { buildContext, renderTemplate, findUnresolvedPlaceholders } from './core/placeholders.js';
export { posix, windows, normalize, detectUnityProject } from './core/path-utils.js';
