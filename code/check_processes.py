#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查正在运行的进程"""

import os
import glob

print("=" * 80)
print("检查正在运行的 Python 进程")
print("=" * 80)
print()

# 方法1: 检查 /proc 目录
print("📋 方法1: 检查 /proc 目录")
print()

proc_dirs = glob.glob('/proc/[0-9]*')
python_processes = []

for proc_dir in proc_dirs:
    try:
        with open(f'{proc_dir}/cmdline', 'r') as f:
            cmdline = f.read().replace('\x00', ' ').strip()
            
        if 'python' in cmdline.lower() and ('fix_persona' in cmdline or 'regenerate_memory' in cmdline):
            pid = os.path.basename(proc_dir)
            python_processes.append((pid, cmdline))
    except:
        pass

if python_processes:
    print(f"✅ 找到 {len(python_processes)} 个相关进程:")
    for pid, cmd in python_processes:
        print(f"  PID {pid}:")
        print(f"    {cmd[:150]}")
        print()
else:
    print("❌ 没有找到相关的 Python 进程")

print()
print("=" * 80)
print("检查日志文件的最近修改时间")
print("=" * 80)
print()

log_files = [
    '/mnt/localssd/logs/fix_persona_concepts.log',
    '/mnt/localssd/logs/regenerate_memory_algebra2005.log',
    '/mnt/localssd/logs/regenerate_memory_assist2017.log',
    '/mnt/localssd/logs/regenerate_memory_nips_task34.log',
    '/mnt/localssd/logs/regenerate_memory_bridge2006.log',
]

for log_file in log_files:
    if os.path.exists(log_file):
        mtime = os.path.getmtime(log_file)
        import datetime
        mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        size = os.path.getsize(log_file)
        print(f"{os.path.basename(log_file)}:")
        print(f"  最后修改: {mtime_str}")
        print(f"  文件大小: {size:,} bytes")
        print()

