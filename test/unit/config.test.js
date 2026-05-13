import { describe, it } from 'node:test';
import assert from 'node:assert';
import { defaultConfig, validateConfig, mergeConfig } from '../../lib/core/config.js';

describe('config.js', () => {
  describe('defaultConfig()', () => {
    it('生成完整默认配置', () => {
      const cfg = defaultConfig('/tmp/test');
      assert.strictEqual(cfg.version, 1);
      assert.strictEqual(cfg.project_root, '.');
      assert.ok(cfg.skillgraph_jsons_root.includes('SkillEditor/Saves/Jsons'));
      assert.strictEqual(cfg.skill_excel_path, '');
      assert.strictEqual(cfg.ai_id_segment, 250);
    });
  });

  describe('validateConfig()', () => {
    it('合法配置 0 error', () => {
      const cfg = defaultConfig();
      cfg.skill_excel_path = 'F:/test/1SkillEditor.xlsx';
      const errors = validateConfig(cfg);
      assert.strictEqual(errors.length, 0);
    });

    it('缺 skill_excel_path 报错', () => {
      const cfg = defaultConfig();
      // skill_excel_path 默认空
      const errors = validateConfig(cfg);
      assert.ok(errors.length > 0);
      assert.ok(errors.some((e) => e.includes('skill_excel_path')));
    });

    it('skill_excel_path 不是 .xlsx 报错', () => {
      const cfg = defaultConfig();
      cfg.skill_excel_path = '/path/to/wrong.txt';
      const errors = validateConfig(cfg);
      assert.ok(errors.some((e) => e.includes('.xlsx')));
    });

    it('ai_id_segment 超范围报错', () => {
      const cfg = defaultConfig();
      cfg.skill_excel_path = '/x/y.xlsx';
      cfg.ai_id_segment = 50;
      const errors = validateConfig(cfg);
      assert.ok(errors.some((e) => e.includes('ai_id_segment')));
    });

    it('null 配置报错', () => {
      const errors = validateConfig(null);
      assert.ok(errors.length > 0);
    });
  });

  describe('mergeConfig()', () => {
    it('用户字段优先', () => {
      const oldCfg = { project_root: '/user/path', skill_excel_path: '/user/excel.xlsx', ai_id_segment: 300 };
      const newDef = defaultConfig();
      const merged = mergeConfig(oldCfg, newDef);
      assert.strictEqual(merged.project_root, '/user/path');
      assert.strictEqual(merged.skill_excel_path, '/user/excel.xlsx');
      assert.strictEqual(merged.ai_id_segment, 300);
    });

    it('null oldConfig 用 defaults', () => {
      const newDef = defaultConfig();
      const merged = mergeConfig(null, newDef);
      assert.strictEqual(merged.project_root, newDef.project_root);
    });
  });
});
