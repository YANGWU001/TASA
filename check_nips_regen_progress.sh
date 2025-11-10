#!/bin/bash

echo "=========================================="
echo "NIPS_TASK34 重建进度监控"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# 检查进程
memory_pid=$(ps aux | grep "regenerate_memory_full.py.*nips_task34" | grep -v grep | awk '{print $2}')
persona_pid=$(ps aux | grep "create_student_bank_final.py.*nips_task34" | grep -v grep | awk '{print $2}')

echo "📊 任务状态:"
if [ -n "$memory_pid" ]; then
    echo "  ✅ Memory 重建运行中 (PID: $memory_pid)"
else
    echo "  ⚠️  Memory 重建已完成或未运行"
fi

if [ -n "$persona_pid" ]; then
    echo "  ✅ Persona 重建运行中 (PID: $persona_pid)"
else
    echo "  ⚠️  Persona 重建已完成或未运行"
fi
echo ""

# Memory 日志
if [ -f "/mnt/localssd/logs/regen_nips_memory.log" ]; then
    echo "📝 Memory 重建进度:"
    echo "----------------------------------------"
    tail -20 /mnt/localssd/logs/regen_nips_memory.log | grep -E "生成Memory|处理学生|完成"
    echo "----------------------------------------"
    echo ""
fi

# Persona 日志
if [ -f "/mnt/localssd/logs/regen_nips_persona.log" ]; then
    echo "👤 Persona 重建进度:"
    echo "----------------------------------------"
    tail -20 /mnt/localssd/logs/regen_nips_persona.log | grep -E "处理进度|学生|完成"
    echo "----------------------------------------"
    echo ""
fi

echo "💡 使用提示:"
echo "  查看 Memory 日志: tail -f /mnt/localssd/logs/regen_nips_memory.log"
echo "  查看 Persona 日志: tail -f /mnt/localssd/logs/regen_nips_persona.log"
echo ""

