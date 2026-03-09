#!/bin/bash
# 发布脚本 - 构建并发布 wxauto-mcp

set -e

echo "==================================="
echo "wxauto-mcp 发布脚本"
echo "==================================="
echo ""

# 检查版本
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "//' | sed 's/"//')
echo "当前版本: $VERSION"
echo ""

# 清理旧的构建文件
echo "1. 清理旧的构建文件..."
rm -rf build/ dist/ *.egg-info
echo "✓ 清理完成"
echo ""

# 运行测试
echo "2. 运行测试..."
if [ -d "tests" ]; then
    python -m pytest tests/ -v || echo "⚠ 测试失败，但继续构建"
else
    echo "⚠ 未找到测试目录，跳过测试"
fi
echo ""

# 构建包
echo "3. 构建包..."
python -m build --outdir dist/
echo "✓ 构建完成"
echo ""

# 检查构建结果
echo "4. 检查构建结果..."
ls -lh dist/
echo ""

# 创建Git标签
echo "5. 创建Git标签..."
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    echo "⚠ 标签 v$VERSION 已存在"
    read -p "是否删除旧标签并创建新标签? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d "v$VERSION"
        git tag "v$VERSION"
        echo "✓ 新标签已创建"
    fi
else
    git tag "v$VERSION"
    echo "✓ 标签 v$VERSION 已创建"
fi
echo ""

# 提示发布步骤
echo "==================================="
echo "构建完成！"
echo "==================================="
echo ""
echo "接下来的步骤："
echo ""
echo "1. 推送代码到 GitHub:"
echo "   git push origin main"
echo "   git push origin v$VERSION"
echo ""
echo "2. GitHub Actions 将自动:"
echo "   - 运行 CI 测试"
echo "   - 创建 Release"
echo "   - 上传 whl 和 tar.gz 到 Release"
echo ""
echo "3. 手动发布到 PyPI (可选):"
echo "   twine upload dist/*"
echo ""
echo "==================================="