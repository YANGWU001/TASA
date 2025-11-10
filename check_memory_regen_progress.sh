#!/bin/bash

echo "========================================"
echo "Memory重建进度监控"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 检查进程状态
echo "📊 进程状态:"
RUNNING_COUNT=0
for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
    if pgrep -f "regenerate_memory_full.py --dataset $dataset" > /dev/null; then
        PID=$(pgrep -f "regenerate_memory_full.py --dataset $dataset")
        echo "  ✅ $dataset (PID: $PID) - 运行中"
        RUNNING_COUNT=$((RUNNING_COUNT + 1))
    else
        echo "  ⏹️  $dataset - 已完成/未运行"
    fi
done
echo ""
echo "  运行中: $RUNNING_COUNT/4"
echo ""

# 检查各数据集的进度
echo "📈 各数据集详细进度:"
echo ""

for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
    LOG_FILE="/mnt/localssd/logs/memory_regen/$dataset.log"
    
    echo "【$dataset】:"
    
    if [ ! -f "$LOG_FILE" ]; then
        echo "  ⚠️  日志文件不存在"
        echo ""
        continue
    fi
    
    # 提取进度条信息（最后一行包含%的行）
    PROGRESS=$(grep -o '[0-9]*%' "$LOG_FILE" | tail -1)
    
    # 提取学生总数
    TOTAL_STUDENTS=$(grep "将处理" "$LOG_FILE" | tail -1 | grep -o '[0-9]* 个学生' | grep -o '[0-9]*')
    
    # 提取成功/跳过/错误信息（如果已完成）
    if grep -q "处理结果:" "$LOG_FILE"; then
        SUCCESS=$(grep "成功:" "$LOG_FILE" | tail -1 | grep -o '[0-9]*' | head -1)
        SKIPPED=$(grep "跳过:" "$LOG_FILE" | tail -1 | grep -o '[0-9]*' | head -1)
        ERROR=$(grep "错误:" "$LOG_FILE" | tail -1 | grep -o '[0-9]*' | head -1)
        
        echo "  进度: 100% (已完成)"
        echo "  学生总数: $TOTAL_STUDENTS"
        echo "  成功: $SUCCESS, 跳过: $SKIPPED, 错误: $ERROR"
        
        # 统计memory记录数
        if grep -q "Memory统计:" "$LOG_FILE"; then
            TOTAL_MEM=$(grep "总记录数:" "$LOG_FILE" | tail -1 | grep -o '[0-9]*')
            AVG_MEM=$(grep "平均每学生:" "$LOG_FILE" | tail -1 | grep -o '[0-9.]*' | head -1)
            echo "  Memory总数: $TOTAL_MEM 条 (平均 $AVG_MEM 条/学生)"
        fi
    else
        if [ -n "$PROGRESS" ]; then
            echo "  进度: $PROGRESS"
            echo "  学生总数: $TOTAL_STUDENTS"
        else
            echo "  状态: 初始化中..."
        fi
    fi
    
    # 显示最新的几行日志（排除进度条）
    RECENT_LOG=$(tail -5 "$LOG_FILE" | grep -v "生成Memory" | grep -v "Inference Embeddings" | tail -2)
    if [ -n "$RECENT_LOG" ]; then
        echo "  最近日志: $(echo "$RECENT_LOG" | head -1 | cut -c1-60)..."
    fi
    
    echo ""
done

echo "========================================"
echo ""
echo "💡 使用提示:"
echo "  查看实时日志: tail -f /mnt/localssd/logs/memory_regen/<dataset>.log"
echo "  查看所有日志: tail -f /mnt/localssd/logs/memory_regen/*.log"
echo "  再次检查进度: bash $0"
echo ""
echo "========================================"

