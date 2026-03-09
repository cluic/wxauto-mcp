#!/bin/bash
# Git 仓库初始化脚本

set -e

echo "==================================="
echo "wxauto-mcp Git 仓库初始化"
echo "==================================="
echo ""

# 检查是否已经是Git仓库
if [ -d ".git" ]; then
    echo "⚠  已经是Git仓库"
    read -p "是否重新初始化? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 0
    fi
    rm -rf .git
fi

echo "1. 初始化Git仓库..."
git init
git branch -M main
echo "✓ Git仓库初始化完成"
echo ""

echo "2. 添加所有文件..."
git add .
echo "✓ 文件已添加"
echo ""

echo "3. 创建初始提交..."
git commit -m "Initial commit: wxauto MCP Server v1.0.0

- 实现27个微信自动化MCP工具
- 支持stdio和HTTP/SSE传输模式
- 全局单例机制避免冲突
- 一键安装到AI应用
- 完整的文档和测试

功能特性:
- 消息操作: 发送文本、图片、文件、链接卡片
- 联系人管理: 获取好友列表、切换聊天
- 会话管理: 获取会话列表、筛选未读消息
- 文件传输: 发送单个或批量文件
- 好友管理: 处理好友请求和添加新好友
- 系统管理: 初始化、激活、状态检查
"
echo "✓ 初始提交完成"
echo ""

echo "4. 检查远程仓库..."
read -p "是否添加远程仓库? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "请输入GitHub仓库URL (如: https://github.com/username/wxauto-mcp.git): " REPO_URL
    if [ -n "$REPO_URL" ]; then
        git remote add origin "$REPO_URL"
        echo "✓ 远程仓库已添加"
        echo ""
        echo "5. 推送到GitHub..."
        read -p "立即推送? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push -u origin main
            echo "✓ 代码已推送到GitHub"
        else
            echo "稍后可使用以下命令推送:"
            echo "  git push -u origin main"
        fi
    fi
else
    echo "跳过添加远程仓库"
fi

echo ""
echo "==================================="
echo "初始化完成！"
echo "==================================="
echo ""
echo "接下来的步骤:"
echo ""
echo "1. 如需添加远程仓库:"
echo "   git remote add origin <your-repo-url>"
echo ""
echo "2. 推送代码:"
echo "   git push -u origin main"
echo ""
echo "3. 创建并推送标签 (用于Release):"
echo "   git tag v1.0.0"
echo "   git push origin v1.0.0"
echo ""
echo "4. 在GitHub上启用Actions:"
echo "   - 访问仓库页面"
echo "   - 点击 Settings > Actions > Enable Actions"
echo ""
echo "==================================="
