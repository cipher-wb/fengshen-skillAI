import { describe, it } from 'node:test';
import assert from 'node:assert';
import { posix, windows, normalize, joinPosix } from '../../lib/core/path-utils.js';

describe('path-utils.js', () => {
  describe('posix()', () => {
    it('Windows 路径转 POSIX', () => {
      assert.strictEqual(posix('F:\\foo\\bar'), 'F:/foo/bar');
      assert.strictEqual(posix('C:\\Users\\test'), 'C:/Users/test');
    });

    it('已是 POSIX 不动', () => {
      assert.strictEqual(posix('/usr/local/bin'), '/usr/local/bin');
    });

    it('空值处理', () => {
      assert.strictEqual(posix(''), '');
      assert.strictEqual(posix(null), null);
    });
  });

  describe('windows()', () => {
    it('POSIX 转 Windows', () => {
      assert.strictEqual(windows('F:/foo/bar'), 'F:\\foo\\bar');
    });
  });

  describe('normalize()', () => {
    it('展开 ~', () => {
      const result = normalize('~/test');
      assert.ok(!result.startsWith('~'));
    });

    it('resolve 相对路径', () => {
      const result = normalize('./test');
      assert.ok(result.endsWith('test') || result.endsWith('test/'));
    });
  });

  describe('joinPosix()', () => {
    it('用 / 连接', () => {
      assert.strictEqual(joinPosix('a', 'b', 'c'), 'a/b/c');
    });
  });
});
