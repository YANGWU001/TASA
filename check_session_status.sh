#!/bin/bash

echo "========================================"
echo "Session生成进度监控"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

echo "📊 实时进度:"
echo ""

for dataset in "${DATASETS[@]}"; do
    if [ -d "/mnt/localssd/bank/session/$dataset" ]; then
        count=$(ls -1 /mnt/localssd/bank/session/$dataset/*.json 2>/dev/null | wc -l)
        size=$(du -sh /mnt/localssd/bank/session/$dataset 2>/dev/null | awk '{print $1}')
        echo "  ✅ $dataset: $count sessions, $size"
    else
        echo "  ⏳ $dataset: 正在初始化..."
    fi
done

echo ""
echo "🔄 运行中的进程:"
ps aux | grep "generate_student_sessions.py" | grep -v grep | awk '{print "  进程 " $2 ": " $NF}' | head -4

echo ""
echo "查看实时日志: tail -f /mnt/localssd/logs/sessions/*.log"

