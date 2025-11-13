#!/usr/bin/env python3
"""监控LPKT/DKT/AKT重新生成进度"""

import os
import json
import time
from datetime import datetime

datasets = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
models = ['lpkt', 'dkt', 'akt']

def check_progress():
    print("="*100)
    print(f"LPKT/DKT/AKT重新生成进度检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    print()
    
    # 检查运行中的进程
    stream = os.popen("ps aux | grep calc_fs_all_data_simple | grep -v grep | wc -l")
    running_count = int(stream.read().strip())
    print(f"🔄 运行中的任务: {running_count}/12")
    print()
    
    # 检查每个文件
    completed = 0
    failed = 0
    
    print(f"{'数据集':<20} {'LPKT':<12} {'DKT':<12} {'AKT':<12}")
    print(f"{'-'*60}")
    
    for dataset in datasets:
        row = f"{dataset:<20}"
        
        for model in models:
            file_path = f'/mnt/localssd/bank/forgetting/{dataset}/{model}.json'
            log_path = f'/mnt/localssd/logs/regen_{dataset}_{model}.log'
            
            if os.path.exists(file_path):
                # 检查文件大小和学生数
                file_size = os.path.getsize(file_path)
                try:
                    with open(file_path) as f:
                        data = json.load(f)
                        n_students = len(data)
                        
                        # 检查是否包含新字段
                        first_student = list(data.keys())[0]
                        first_concept = list(data[first_student].keys())[0]
                        has_delta_t = 'delta_t' in data[first_student][first_concept]
                        has_tau = 'tau' in data[first_student][first_concept]
                        
                        if has_delta_t and has_tau:
                            row += f" ✅{n_students:<10}"
                            completed += 1
                        else:
                            row += f" ⚠️{n_students:<10}"
                            completed += 1
                except:
                    row += f" ❌ (损坏)   "
                    failed += 1
            else:
                # 检查日志文件判断状态
                if os.path.exists(log_path):
                    # 检查日志最后几行
                    with open(log_path) as f:
                        lines = f.readlines()
                        if len(lines) > 0:
                            last_line = lines[-1].strip()
                            if '完成' in last_line or '✅' in last_line:
                                row += " 🔄生成中   "
                            elif '❌' in last_line or 'Error' in last_line or 'Traceback' in last_line:
                                row += " ❌失败     "
                                failed += 1
                            else:
                                row += " 🔄运行中   "
                        else:
                            row += " 🔄启动中   "
                else:
                    row += " ⏳等待     "
        
        print(row)
    
    print()
    print("="*100)
    print(f"📊 统计: ✅完成 {completed}/12  |  ❌失败 {failed}/12  |  🔄运行中 {running_count}/12")
    print("="*100)
    print()
    
    # 显示最新的几个日志文件的最后几行
    if failed > 0 or running_count > 0:
        print("最近的日志输出:")
        print("-"*100)
        for dataset in datasets[:2]:  # 只显示前2个数据集
            for model in models[:2]:  # 只显示前2个模型
                log_path = f'/mnt/localssd/logs/regen_{dataset}_{model}.log'
                if os.path.exists(log_path):
                    print(f"\n📄 {dataset}_{model}:")
                    with open(log_path) as f:
                        lines = f.readlines()
                        if len(lines) > 0:
                            print("   " + lines[-1].strip())

if __name__ == '__main__':
    check_progress()

