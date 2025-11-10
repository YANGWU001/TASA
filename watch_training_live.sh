#!/bin/bash
# 实时查看训练进度脚本

echo "📊 选择要查看的训练日志："
echo "1) EdNet (GPU 0)"
echo "2) ASSISTments2017 (GPU 1)"
echo "3) 同时查看两个（分屏）"
echo "4) 查看训练状态摘要"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "📈 正在查看EdNet训练实时日志..."
        echo "按 Ctrl+C 退出"
        sleep 2
        tail -f /tmp/lpkt_ednet_live.log
        ;;
    2)
        echo "📈 正在查看ASSISTments2017训练实时日志..."
        echo "按 Ctrl+C 退出"
        sleep 2
        tail -f /tmp/lpkt_assist2017_live.log
        ;;
    3)
        echo "📈 正在同时查看两个训练的实时日志..."
        echo "按 Ctrl+C 退出"
        sleep 2
        # 使用multitail或者分屏显示
        if command -v multitail &> /dev/null; then
            multitail /tmp/lpkt_ednet_live.log /tmp/lpkt_assist2017_live.log
        else
            # 如果没有multitail，使用tail -f同时显示
            tail -f /tmp/lpkt_ednet_live.log /tmp/lpkt_assist2017_live.log
        fi
        ;;
    4)
        while true; do
            clear
            echo "🔄 训练状态摘要 (每10秒刷新)"
            echo "================================"
            date
            echo ""
            
            echo "📍 训练进程:"
            ps aux | grep "python.*wandb_lpkt_train" | grep -v grep | awk '{printf "  PID: %-6s CPU: %4s%% 命令: %s\n", $2, $3, substr($0, index($0,$11))}'
            echo ""
            
            echo "🖥️  GPU使用:"
            nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader,nounits | head -2 | awk -F', ' '{printf "  GPU %s: 使用率=%s%%, 显存=%sMB\n", $1, $2, $3}'
            echo ""
            
            echo "📝 EdNet最新3行:"
            tail -3 /tmp/lpkt_ednet_live.log 2>/dev/null | sed 's/^/  /'
            echo ""
            
            echo "📝 ASSISTments2017最新3行:"
            tail -3 /tmp/lpkt_assist2017_live.log 2>/dev/null | sed 's/^/  /'
            echo ""
            
            echo "按 Ctrl+C 退出"
            sleep 10
        done
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

