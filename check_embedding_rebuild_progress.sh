#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              📊 Memory Embeddings重建进度检查                               ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 检查进程状态
if ps -p 301578 > /dev/null 2>&1; then
    echo "✅ 重建进程正在运行 (PID: 301578)"
else
    echo "❌ 重建进程未运行"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 各数据集进度"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total_expected=0
total_completed=0

for dataset in assist2017 algebra2005 bridge2006 nips_task34; do
    data_dir="/mnt/localssd/bank/memory/$dataset/data"
    emb_dir="/mnt/localssd/bank/memory/$dataset/embeddings"
    
    if [ -d "$data_dir" ]; then
        json_count=$(ls -1 "$data_dir"/*.json 2>/dev/null | wc -l)
        
        if [ -d "$emb_dir" ]; then
            desc_count=$(ls -1 "$emb_dir"/*_description.npz 2>/dev/null | wc -l)
            kw_count=$(ls -1 "$emb_dir"/*_keywords.npz 2>/dev/null | wc -l)
        else
            desc_count=0
            kw_count=0
        fi
        
        total_expected=$((total_expected + json_count))
        total_completed=$((total_completed + desc_count))
        
        percentage=0
        if [ $json_count -gt 0 ]; then
            percentage=$((desc_count * 100 / json_count))
        fi
        
        echo ""
        echo "📁 $dataset:"
        echo "   • 目标: $json_count 个学生"
        echo "   • 完成: $desc_count 个 description embeddings"
        echo "   • 完成: $kw_count 个 keywords embeddings"
        echo "   • 进度: $percentage%"
        
        if [ $percentage -eq 100 ]; then
            echo "   ✅ 完成"
        elif [ $percentage -gt 0 ]; then
            echo "   🔄 进行中..."
        else
            echo "   ⏳ 等待中..."
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 总体进度"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total_percentage=0
if [ $total_expected -gt 0 ]; then
    total_percentage=$((total_completed * 100 / total_expected))
fi

echo "  • 总学生数: $total_expected"
echo "  • 已完成: $total_completed"
echo "  • 总进度: $total_percentage%"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 最新日志 (最后20行):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -20 /mnt/localssd/logs/rebuild_memory_embeddings.log

echo ""
