#!/usr/bin/env bash
# scripts/quick-release.sh
# 一键发版脚本 (macOS / Linux / Git Bash)
#
# 用法：
#   ./scripts/quick-release.sh                # patch bump (默认)
#   ./scripts/quick-release.sh minor          # minor bump
#   ./scripts/quick-release.sh --dry-run      # 只 show 不真发

set -e

BUMP_TYPE="${1:-patch}"
DRY_RUN=0
COMMIT_MESSAGE=""

# 参数解析
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        -m|--message) COMMIT_MESSAGE="$2"; shift ;;
        patch|minor|major) BUMP_TYPE="$1" ;;
    esac
    shift || true
done

step() { echo -e "\n\033[36m[$1] $2\033[0m"; }
run() {
    echo -e "  \033[2m$1\033[0m"
    if [ "$DRY_RUN" -eq 0 ]; then
        eval "$1"
    fi
}

echo "═════════════════════════════════════════════════════"
echo "  fengshen-skillai quick-release"
echo "  Bump: $BUMP_TYPE / Dry-run: $DRY_RUN"
echo "═════════════════════════════════════════════════════"

step 1 "抽源 (extract templates from F:/DreamRivakes2/...)"
run "node scripts/extract-from-source.js"

step 2 "跑 e2e 测试"
run "node scripts/test-init.js"

step 3 "跑 unit 测试"
run "npm test"

step 4 "$BUMP_TYPE bump version"
if [ "$DRY_RUN" -eq 0 ]; then
    npm version "$BUMP_TYPE" --no-git-tag-version
    NEW_VERSION=$(node -p "require('./package.json').version")
    echo -e "  \033[32m新版本: $NEW_VERSION\033[0m"
else
    NEW_VERSION="X.Y.Z (dry-run)"
fi

if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="v$NEW_VERSION: mental_model 学习更新"
fi

step 5 "Git commit + tag + push"
run "git add ."
run "git commit -m \"$COMMIT_MESSAGE\""
run "git tag v$NEW_VERSION"
run "git push origin main --tags"

step 6 "GitHub Release"
run "gh release create v$NEW_VERSION --title \"v$NEW_VERSION\" --notes-file CHANGELOG.md"

step 7 "npm publish"
run "npm publish"

step 8 "验证"
run "npx fengshen-skillai@latest version"

echo -e "\n\033[32m═════════════════════════════════════════════════════\033[0m"
echo -e "\033[32m  发版完成 ✓  v$NEW_VERSION\033[0m"
echo -e "\033[32m═════════════════════════════════════════════════════\033[0m"
echo "用户安装："
echo "  npx fengshen-skillai@latest init <path>"
