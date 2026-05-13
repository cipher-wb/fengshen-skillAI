import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  buildContext,
  renderHandlebars,
  renderPythonPlaceholders,
  renderTemplate,
  findUnresolvedPlaceholders
} from '../../lib/core/placeholders.js';

describe('placeholders.js', () => {
  describe('buildContext()', () => {
    it('生成完整 context', () => {
      const cfg = {
        skillgraph_jsons_root: 'Assets/Test/Jsons/',
        skill_excel_path: 'F:/test/1SkillEditor.xlsx',
        ai_id_segment: 250
      };
      const ctx = buildContext(cfg, '/tmp/myproject');
      assert.ok(ctx.PROJECT_ROOT.endsWith('myproject'));
      assert.strictEqual(ctx.SKILLGRAPH_JSONS_ROOT, 'Assets/Test/Jsons/');
      assert.strictEqual(ctx.SKILL_EXCEL_PATH, 'F:/test/1SkillEditor.xlsx');
      assert.strictEqual(ctx.AI_ID_SEGMENT, 250);
    });

    it('Windows 风格变量', () => {
      const cfg = { skill_excel_path: 'F:/test/x.xlsx' };
      const ctx = buildContext(cfg, '/tmp/x');
      assert.ok(ctx.SKILL_EXCEL_PATH_WIN.includes('\\'));
      assert.ok(!ctx.SKILL_EXCEL_PATH.includes('\\'));
    });
  });

  describe('renderHandlebars()', () => {
    it('替换 {{X}} 占位符', () => {
      const tpl = '工作目录: {{PROJECT_ROOT}}';
      const result = renderHandlebars(tpl, { PROJECT_ROOT: '/tmp/test' });
      assert.strictEqual(result, '工作目录: /tmp/test');
    });

    it('Excel path 替换', () => {
      const tpl = 'Excel: {{SKILL_EXCEL_PATH}}';
      const result = renderHandlebars(tpl, { SKILL_EXCEL_PATH: 'F:/x.xlsx' });
      assert.strictEqual(result, 'Excel: F:/x.xlsx');
    });
  });

  describe('renderPythonPlaceholders()', () => {
    it('替换 <<X>> 占位符', () => {
      const tpl = 'ROOT = Path("<<PROJECT_ROOT>>")';
      const result = renderPythonPlaceholders(tpl, { PROJECT_ROOT: '/tmp/test' });
      assert.strictEqual(result, 'ROOT = Path("/tmp/test")');
    });

    it('保留 Python dict {{}} 不动', () => {
      const tpl = 'd = {{"a": 1}, "b": 2}';
      const result = renderPythonPlaceholders(tpl, { PROJECT_ROOT: '/x' });
      assert.strictEqual(result, 'd = {{"a": 1}, "b": 2}');
    });
  });

  describe('renderTemplate()', () => {
    it('.py 文件用 Python 风格', () => {
      const tpl = 'import os\nROOT = "<<PROJECT_ROOT>>"';
      const result = renderTemplate('foo.py', tpl, { PROJECT_ROOT: '/x' });
      assert.ok(result.includes('"/x"'));
    });

    it('.md 文件用 handlebars', () => {
      const tpl = '# {{PROJECT_ROOT}}';
      const result = renderTemplate('foo.md', tpl, { PROJECT_ROOT: '/x' });
      assert.strictEqual(result, '# /x');
    });
  });

  describe('findUnresolvedPlaceholders()', () => {
    it('找 {{X}} 残留', () => {
      const content = 'foo {{UNRESOLVED}} bar';
      const found = findUnresolvedPlaceholders(content);
      assert.ok(found.includes('{{UNRESOLVED}}'));
    });

    it('找 <<X>> 残留', () => {
      const content = 'foo <<UNRESOLVED>> bar';
      const found = findUnresolvedPlaceholders(content);
      assert.ok(found.includes('<<UNRESOLVED>>'));
    });

    it('已渲染 0 残留', () => {
      const content = 'foo bar';
      const found = findUnresolvedPlaceholders(content);
      assert.strictEqual(found.length, 0);
    });
  });
});
