# 贡献指南 (Contributing)

> 欢迎贡献！本项目源自《封神》MOBA 项目实战 6 个月 / 50+ 批 Bootstrap 学习沉淀。

## 开发环境

- Node.js >= 18 (推荐 18.18.0 / `.nvmrc` 已指定)
- Python >= 3.10 (跑测试 doctor 验证用)
- Git
- Claude Code (测试 plugin 模式用)

## 本地开发

```bash
git clone https://github.com/cipher-wb/fengshen-skillAI.git
cd fengshen-skillAI
npm install

# 链接到全局 (这样你可以在任何工程跑 npx fengshen-skillai)
npm link

# 在测试工程跑
mkdir /tmp/test-fengshen
cd /tmp/test-fengshen
fengshen-skillai init . --non-interactive

# 改代码后无需重新 link / 直接生效
```

## 项目结构

详见 [ARCHITECTURE.md](ARCHITECTURE.md)。

简版：

```
bin/cli.js                 CLI 入口 (commander)
lib/commands/              5 个子命令
lib/core/                  核心库 (config / placeholders / template-engine / ...)
lib/utils/                 chalk + @inquirer 包装
templates/                 模板树 (handlebars + 自定义)
schemas/                   JSON Schema
scripts/                   抽源 / e2e / release 脚本
test/                      单测 + e2e + fixtures
docs/                      开发者文档
```

## 加新功能流程

### 添加新 CLI 子命令

1. 在 `lib/commands/<name>.js` 写 handler
2. 在 `bin/cli.js` 注册子命令
3. 在 `lib/index.js` 导出 (programmatic API)
4. 加测试 `test/unit/<name>.test.js`
5. 更新 README + CHANGELOG

### 添加新占位符

详见 [PLACEHOLDER_REFERENCE.md#新增占位符流程](PLACEHOLDER_REFERENCE.md)。

### 添加新 mental_model 子系统

mental_model 不是 fengshen-skillai 本身维护的 / 在源工程 (`F:/DreamRivakes2/...`) 维护。

升级流程：
1. 在源工程加新子系统页 (如 `doc/SkillAI/mental_model/新系统.md`)
2. 升级 `mental_model_version`
3. 在 fengshen-skillai 仓库跑 `node scripts/extract-from-source.js`
4. 更新 `package.json#fengshenMentalModelVersion`
5. 发新 minor 版本

## Commit 规范

```
<type>: <subject>

<body>

<footer>
```

`type` 可选值：
- `feat`: 新功能
- `fix`: bug fix
- `docs`: 仅文档
- `refactor`: 重构 / 不改行为
- `test`: 加测试
- `chore`: 杂项 (依赖升级 / CI / 等)
- `release`: 版本发布

## PR 流程

1. Fork → 新建 feature branch (`feat/add-<name>`)
2. 改代码 + 加测试
3. 跑 `npm test` + `npm run test:e2e` 全绿
4. 跑 `npm run format` + `npm run lint`
5. 提交 PR / 描述清楚动机 + 测试覆盖

## 测试

```bash
# 单测
npm test

# e2e (干净工程跑 init + 验证)
npm run test:e2e

# 抽源校验 (要求 F:/DreamRivakes2/... 可访问)
node scripts/extract-from-source.js --validate
```

## 问题反馈

[GitHub Issues](https://github.com/cipher-wb/fengshen-skillAI/issues)

## 行为准则

[Contributor Covenant](https://www.contributor-covenant.org/zh-cn/version/2/1/code_of_conduct/)
