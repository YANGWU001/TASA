#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime

print("=" * 80)
print("正在运行的任务检查")
print("=" * 80)
print()

# 检查 Python 进程
print("📊 正在运行的 Python 进程:")
print("-" * 80)
try:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    
    python_procs = []
    for line in lines:
        if 'python' in line.lower() and '.py' in line and 'grep' not in line:
            python_procs.append(line)
    
    if python_procs:
        for proc in python_procs:
            parts = proc.split()
            if len(parts) >= 11:
                pid = parts[1]
                cpu = parts[2]
                mem = parts[3]
                cmd = ' '.join(parts[10:])
                print(f"PID: {pid:8s} CPU: {cpu:5s}% MEM: {mem:5s}% CMD: {cmd[:80]}")
    else:
        print("  没有找到正在运行的 Python 进程")
except Exception as e:
    print(f"  ⚠️  无法获取进程信息: {e}")

print()
print("📝 最近的日志文件:")
print("-" * 80)

# 检查关键日志文件
log_files = [
    '/mnt/localssd/logs/regen_nips_memory.log',
    '/mnt/localssd/logs/regen_nips_persona.log',
    '/mnt/localssd/logs/recompute_persona_embeddings.log',
    '/mnt/localssd/logs/memory_regen/nips_task34.log',
]

for log_file in log_files:
    if os.path.exists(log_file):
        stat = os.stat(log_file)
        size_mb = stat.st_size / 1024 / 1024
        mtime = datetime.fromtimestamp(stat.st_mtime)
        print(f"\n{os.path.basename(log_file)}:")
        print(f"  大小: {size_mb:.2f} MB")
        print(f"  最后更新: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 读取最后几行
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                last_lines = lines[-5:] if len(lines) >= 5 else lines
                print(f"  最后几行:")
                for line in last_lines:
                    print(f"    {line.rstrip()}")
        except:
            pass

print()
print("=" * 80)

