#!/opt/venv/bin/python3
"""
使用多线程并行运行所有baseline任务
"""

import subprocess
import os
import threading
from queue import Queue
from datetime import datetime
import time

# 配置
BACKBONES = {
    'llama': 'llama-3.1-8B-Instruct',
    'qwen': 'Qwen3-4B-Instruct'
}
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 40
MAX_PARALLEL = 8  # 最多同时运行8个任务

results_lock = threading.Lock()
results = {'completed': 0, 'failed': 0, 'total': 0}

def update_tasa_config(tutor_model):
    """更新tasa_config.py"""
    config_file = '/mnt/localssd/tasa_config.py'
    with open(config_file, 'r') as f:
        content = f.read()
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('TUTOR_MODEL = '):
            lines[i] = f'TUTOR_MODEL = "{tutor_model}"'
    with open(config_file, 'w') as f:
        f.write('\n'.join(lines))

def run_single_baseline(method, dataset, backbone, backbone_suffix, task_id):
    """运行单个baseline任务"""
    try:
        print(f"[任务{task_id}] 开始: {method} on {dataset} with {backbone}")
        
        # 更新配置（需要加锁避免冲突）
        with results_lock:
            update_tasa_config(backbone)
            time.sleep(0.5)  # 等待配置写入
        
        # 构建命令
        students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
        log_file = f'/mnt/localssd/logs/baseline_{method}_{backbone_suffix}_{dataset}.log'
        
        cmd = [
            '/opt/venv/bin/python3', '-u',
            '/mnt/localssd/baseline_evaluation_conservative.py',
            '--method', method,
            '--dataset', dataset,
            '--students-file', students_file,
            '--max-workers', str(MAX_WORKERS)
        ]
        
        # 运行
        with open(log_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
        
        # 移动结果到正确目录
        if result.returncode == 0:
            source_dir = f'/mnt/localssd/bank/evaluation_results/{method}-conservative/{dataset}'
            target_dir = f'/mnt/localssd/bank/evaluation_results/{method}-conservative-{backbone_suffix}/{dataset}'
            
            if os.path.exists(source_dir):
                os.makedirs(os.path.dirname(target_dir), exist_ok=True)
                import shutil
                shutil.move(source_dir, target_dir)
                
                with results_lock:
                    results['completed'] += 1
                print(f"[任务{task_id}] ✅ {method} on {dataset} 完成")
                return True
        
        with results_lock:
            results['failed'] += 1
        print(f"[任务{task_id}] ❌ {method} on {dataset} 失败")
        return False
        
    except Exception as e:
        with results_lock:
            results['failed'] += 1
        print(f"[任务{task_id}] ❌ {method} on {dataset} 异常: {e}")
        return False

def worker(queue):
    """工作线程"""
    while True:
        task = queue.get()
        if task is None:
            break
        
        method, dataset, backbone, backbone_suffix, task_id = task
        run_single_baseline(method, dataset, backbone, backbone_suffix, task_id)
        queue.task_done()

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 并行运行所有Baseline任务 (Llama + Qwen)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # 生成所有任务
    tasks = []
    task_id = 1
    
    for backbone_suffix, backbone in BACKBONES.items():
        for dataset in DATASETS:
            for method in METHODS:
                tasks.append((method, dataset, backbone, backbone_suffix, task_id))
                task_id += 1
    
    results['total'] = len(tasks)
    
    print(f"⚙️  配置:")
    print(f"   • 总任务数: {len(tasks)}")
    print(f"   • 最大并行数: {MAX_PARALLEL}")
    print(f"   • 每任务Workers: {MAX_WORKERS}")
    print(f"   • 样本量: 10人/dataset")
    print()
    
    # 创建任务队列
    queue = Queue()
    for task in tasks:
        queue.put(task)
    
    # 创建工作线程
    threads = []
    for i in range(MAX_PARALLEL):
        t = threading.Thread(target=worker, args=(queue,))
        t.start()
        threads.append(t)
    
    # 等待所有任务完成
    start_time = datetime.now()
    queue.join()
    
    # 停止工作线程
    for i in range(MAX_PARALLEL):
        queue.put(None)
    for t in threads:
        t.join()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 打印结果
    print("\n" + "━"*80)
    print("📊 最终统计")
    print("━"*80)
    print(f"总任务数: {results['total']}")
    print(f"成功: {results['completed']}")
    print(f"失败: {results['failed']}")
    print(f"总耗时: {duration}")
    print("━"*80)

if __name__ == '__main__':
    main()

