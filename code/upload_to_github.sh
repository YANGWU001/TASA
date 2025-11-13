#!/bin/bash
# 快速上传到GitHub的脚本

set -e  # 遇到错误立即退出

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    TASA项目 - GitHub上传助手                              ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "📊 上传内容统计:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  • 总文件: 67,537 个"
echo "  • 包含所有embeddings (16,756 个 .npz 文件)"
echo "  • 总大小: ~4.0 GB"
echo "  • 预估上传时间: 20-40 分钟"
echo ""

# 检查是否已配置git用户
GIT_USER=$(git config --global user.name 2>/dev/null || echo "")
GIT_EMAIL=$(git config --global user.email 2>/dev/null || echo "")

if [ -z "$GIT_USER" ] || [ -z "$GIT_EMAIL" ]; then
    echo -e "${YELLOW}⚠️  检测到Git用户信息未配置${NC}"
    echo ""
    read -p "请输入您的姓名: " name
    read -p "请输入您的邮箱: " email
    
    git config --global user.name "$name"
    git config --global user.email "$email"
    
    echo -e "${GREEN}✅ Git用户信息已配置${NC}"
    echo ""
else
    echo -e "${GREEN}✅ Git用户信息已配置: $GIT_USER <$GIT_EMAIL>${NC}"
    echo ""
fi

# 检查是否有要提交的更改
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  检查Git状态..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CHANGES=$(git status --porcelain | wc -l)

if [ $CHANGES -eq 0 ]; then
    echo -e "${YELLOW}⚠️  没有检测到需要提交的更改${NC}"
    echo "可能已经提交过了，或者文件还未添加到git"
    exit 0
fi

echo -e "${GREEN}✅ 检测到 $CHANGES 个文件需要提交${NC}"
echo ""

# 显示部分文件
echo "将要提交的文件示例（前10个）:"
git status --porcelain | head -10
echo "..."
echo ""

# 确认提交
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  创建提交"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

read -p "是否创建提交? (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "取消操作"
    exit 0
fi

echo ""
echo "正在创建提交..."
git commit -m "Initial commit: TASA project with complete data

- Core TASA implementation with Forgetting Score, Memory, and Persona
- Complete bank data (dialogue, evaluation, forgetting, persona, memory)
- All embeddings included (16,756 files, 1.1GB)
- Four baselines: MathChat, PSS-MV, TutorLLM, Vanilla-ICL
- Ablation studies (woForgetting, woMemory, woPersona)
- Complete evaluation system with LLM as Judge
- Comprehensive documentation and analysis reports

Total: 67,537 files, ~4.0GB"

echo -e "${GREEN}✅ 提交创建成功！${NC}"
echo ""

# 配置远程仓库
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  配置GitHub远程仓库"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查是否已有远程仓库
REMOTE=$(git remote -v | grep origin || echo "")

if [ -n "$REMOTE" ]; then
    echo -e "${GREEN}✅ 已配置远程仓库:${NC}"
    git remote -v
    echo ""
    read -p "是否更改远程仓库地址? (y/n): " change_remote
    
    if [ "$change_remote" == "y" ] || [ "$change_remote" == "Y" ]; then
        git remote remove origin
        read -p "请输入新的GitHub仓库地址: " repo_url
        git remote add origin "$repo_url"
        echo -e "${GREEN}✅ 远程仓库已更新${NC}"
    fi
else
    echo "请输入您的GitHub仓库地址"
    echo "格式1: https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    echo "格式2: git@github.com:YOUR_USERNAME/YOUR_REPO.git"
    echo ""
    read -p "GitHub仓库地址: " repo_url
    
    if [ -z "$repo_url" ]; then
        echo -e "${RED}❌ 未输入仓库地址${NC}"
        exit 1
    fi
    
    git remote add origin "$repo_url"
    echo -e "${GREEN}✅ 远程仓库已配置${NC}"
fi

echo ""

# 推送到GitHub
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  推送到GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}⚠️  即将推送 ~4.0GB 数据到GitHub${NC}"
echo "   这可能需要 20-40 分钟，请确保:"
echo "   • 网络连接稳定"
echo "   • 有足够时间等待"
echo "   • 不要中断进程"
echo ""
read -p "确认开始推送? (y/n): " confirm_push

if [ "$confirm_push" != "y" ] && [ "$confirm_push" != "Y" ]; then
    echo "取消推送"
    echo ""
    echo "您可以稍后手动推送:"
    echo "  git push -u origin main"
    exit 0
fi

echo ""
echo "开始推送..."
echo -e "${YELLOW}这可能需要较长时间，请耐心等待...${NC}"
echo ""

# 推送
if git push -u origin main; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}✅ 上传成功！${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "您的TASA项目已成功上传到GitHub！"
    echo ""
    echo "仓库地址: $(git remote get-url origin)"
    echo ""
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${RED}❌ 推送失败${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "可能的原因:"
    echo "  • 网络连接问题"
    echo "  • GitHub认证问题"
    echo "  • 仓库地址错误"
    echo ""
    echo "您可以稍后重试:"
    echo "  git push -u origin main"
    echo ""
fi

