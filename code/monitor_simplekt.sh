#!/bin/bash
# 监控SimpleKT任务进度

echo "======================================================================================================"
echo "                         SimpleKT 任务监控"
echo "======================================================================================================"
echo ""

while true; do
    clear
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 检查Python进程
    echo "=== Python进程状态 ==="
    ps aux | grep "calc_fs_all_data_simple.py" | grep -v grep | awk '{printf "  PID: %s | CPU: %s%% | MEM: %s%% | Time: %s | Dataset: ", $2, $3, $4, $10; for(i=11;i<=NF;i++){if($i~"--dataset"){print $(i+1); break}}}'
    
    if [ -z "$(ps aux | grep 'calc_fs_all_data_simple.py' | grep -v grep)" ]; then
        echo "  没有运行中的进程"
    fi
    
    echo ""
    
    # 检查生成的文件
    echo "=== 已生成的文件 ==="
    
    datasets=("assist2017" "nips_task34" "algebra2005" "bridge2006")
    count=0
    
    for dataset in "${datasets[@]}"; do
        file="/mnt/localssd/bank/forgetting/${dataset}/simplekt.json"
        if [ -f "$file" ]; then
            size=$(ls -lh "$file" | awk '{print $5}')
            echo "  ✅ ${dataset}/simplekt.json ($size)"
            ((count++))
        else
            echo "  ⏳ ${dataset}/simplekt.json (待生成)"
        fi
    done
    
    echo ""
    echo "完成进度: $count/4 ($(echo "scale=1; $count*100/4" | bc)%)"
    echo ""
    
    if [ $count -eq 4 ]; then
        echo "======================================================================================================"
        echo "  🎉 所有SimpleKT任务完成！"
        echo "======================================================================================================"
        break
    fi
    
    echo "按 Ctrl+C 退出监控"
    echo ""
    echo "最近的日志（最后20行）:"
    tail -20 /mnt/localssd/pykt-toolkit/examples/log_simplekt_all.txt 2>/dev/null | sed 's/^/  /'
    
    sleep 10
done

