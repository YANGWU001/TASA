#!/bin/bash
# 选择.gitignore方案的辅助脚本

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    选择 Git 上传方案                                       ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "请选择一个方案："
echo ""
echo "  1) 方案1：推荐方案 (~800MB) 🌟"
echo "     - 快速上传，包含核心实验数据"
echo "     - 排除 persona 和 memory 原始数据"
echo ""
echo "  2) 方案2：最大化方案 (~2.47GB) 💪"
echo "     - 保留所有JSON数据，只排除embeddings"
echo "     - 数据最完整"
echo ""
echo "  3) 查看两个方案的差异"
echo ""
echo "  4) 测试文件大小（不实际复制）"
echo ""
echo "  0) 退出"
echo ""
read -p "请输入选项 (0-4): " choice

case $choice in
    1)
        echo ""
        echo "📋 选择了方案1..."
        cp .gitignore_option1 .gitignore
        echo "✅ .gitignore 已更新为方案1"
        echo ""
        echo "现在可以执行:"
        echo "  git add ."
        echo "  git status"
        ;;
    2)
        echo ""
        echo "📋 选择了方案2..."
        cp .gitignore_option2 .gitignore
        echo "✅ .gitignore 已更新为方案2"
        echo ""
        echo "现在可以执行:"
        echo "  git add ."
        echo "  git status"
        ;;
    3)
        echo ""
        echo "📊 两个方案的差异:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        diff -u .gitignore_option1 .gitignore_option2 | head -50
        ;;
    4)
        echo ""
        echo "🔍 测试各方案的文件大小..."
        echo ""
        
        # 备份当前.gitignore
        if [ -f .gitignore ]; then
            cp .gitignore .gitignore.bak
        fi
        
        # 测试方案1
        cp .gitignore_option1 .gitignore
        git add -n . > /tmp/git_test1.txt 2>&1
        count1=$(git status --porcelain | wc -l)
        echo "方案1: 约 $count1 个文件会被添加"
        
        # 测试方案2
        cp .gitignore_option2 .gitignore
        git add -n . > /tmp/git_test2.txt 2>&1
        count2=$(git status --porcelain | wc -l)
        echo "方案2: 约 $count2 个文件会被添加"
        
        # 恢复
        if [ -f .gitignore.bak ]; then
            mv .gitignore.bak .gitignore
        fi
        
        echo ""
        echo "详细文件列表已保存到 /tmp/git_test1.txt 和 /tmp/git_test2.txt"
        ;;
    0)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效的选项"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 提示："
echo "  - 可以用 'git status' 查看将要上传的文件"
echo "  - 可以用 'git add -n .' 预览（不实际添加）"
echo "  - 两个原始方案文件保留在:"
echo "    .gitignore_option1 和 .gitignore_option2"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

