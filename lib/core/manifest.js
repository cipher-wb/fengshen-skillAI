// 读取 templates/manifest.json + 跟踪文件 hash (用于 update 三方 merge)
import fs from 'fs-extra';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * templates/manifest.json 路径
 */
export function templatesManifestPath() {
  return path.join(__dirname, '..', '..', 'templates', 'manifest.json');
}

/**
 * 读 templates/manifest.json (在 npm 包内)
 */
export async function readTemplatesManifest() {
  const p = templatesManifestPath();
  if (!(await fs.pathExists(p))) {
    return { version: 1, files: {} };
  }
  return await fs.readJson(p);
}

/**
 * 目标工程的 install manifest 路径 (记录本次 scaffold 落盘了什么 / hash 是多少)
 */
export function installManifestPath(projectRoot) {
  return path.join(projectRoot, '.fengshen-skillai', 'install.json');
}

/**
 * 读 install manifest (用户工程内 / .fengshen-skillai/install.json)
 */
export async function readInstallManifest(projectRoot) {
  const p = installManifestPath(projectRoot);
  if (!(await fs.pathExists(p))) {
    return null;
  }
  return await fs.readJson(p);
}

/**
 * 写 install manifest
 */
export async function writeInstallManifest(projectRoot, manifest) {
  const p = installManifestPath(projectRoot);
  await fs.ensureDir(path.dirname(p));
  await fs.writeJson(p, manifest, { spaces: 2 });
}

/**
 * 计算文件 sha256
 */
export async function sha256OfFile(filePath) {
  if (!(await fs.pathExists(filePath))) return null;
  const content = await fs.readFile(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

/**
 * 计算字符串 sha256
 */
export function sha256OfString(s) {
  return crypto.createHash('sha256').update(s).digest('hex');
}

/**
 * 比较两个 hash (用于判断"用户改没改过")
 */
export function hashEquals(a, b) {
  if (!a || !b) return false;
  return a === b;
}

/**
 * 初始化空 install manifest
 */
export function newInstallManifest(version, mentalModelVersion) {
  return {
    version: 1,
    fengshen_skillai_version: version,
    mental_model_version: mentalModelVersion,
    installed_at: new Date().toISOString(),
    files: {} // path → { sha256, owner, source_hash }
  };
}
