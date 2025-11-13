#!/opt/venv/bin/python3
"""
正确的Baseline并行运行策略：
- 2个backbone并行（Llama和Qwen各一个线程）
- 每个backbone内部顺序执行（4 datasets × 4 methods = 16个任务）
"""

import subprocess
import os
import threading
from datetime import datetime
import time

# 配置
BACKBONES = {
    'llama': 'llama-3.1-8B-Instruct',
    'qwen': 'Qwen3-4B-Instruct'
}
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 10  # 每个backbone并行时使用10 workers

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

def run_single_backbone(backbone, backbone_suffix):
    """运行单个backbone的所有任务（顺序执行）"""
    print(f"\n{'='*80}")
    print(f"[{backbone_suffix.upper()}] 开始运行 {backbone}")
    print(f"{'='*80}\n")
    
    # 更新配置（每个backbone线程只更新一次）
    update_tasa_config(backbone)
    time.sleep(1)  # 确保配置写入
    
    local_completed = 0
    local_failed = 0
    
    # 顺序执行16个任务
    for dataset in DATASETS:
        print(f"\n[{backbone_suffix.upper()}] Dataset: {dataset}")
        print(f"-" * 80)
        
        for method in METHODS:
            try:
                task_name = f"{method} on {dataset}"
                print(f"[{backbone_suffix.upper()}] 运行: {task_name}...")
                
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
                        
                        local_completed += 1
                        print(f"[{backbone_suffix.upper()}] ✅ {task_name} 完成")
                    else:
                        local_failed += 1
                        print(f"[{backbone_suffix.upper()}] ❌ {task_name} 失败（结果目录不存在）")
                else:
                    local_failed += 1
                    print(f"[{backbone_suffix.upper()}] ❌ {task_name} 失败（返回码 {result.returncode}）")
                    
            except Exception as e:
                local_failed += 1
                print(f"[{backbone_suffix.upper()}] ❌ {task_name} 异常: {e}")
    
    # 更新全局结果
    with results_lock:
        results['completed'] += local_completed
        results['failed'] += local_failed
    
    print(f"\n{'='*80}")
    print(f"[{backbone_suffix.upper()}] 完成！成功: {local_completed}/16, 失败: {local_failed}/16")
    print(f"{'='*80}\n")

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 Baseline评估：2个Backbone并行执行")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    print("⚙️  执行策略:")
    print("   • Llama线程: 顺序执行16个任务 (4 datasets × 4 methods)")
    print("   • Qwen线程:  顺序执行16个任务 (4 datasets × 4 methods)")
    print("   • 两个线程并行运行")
    print("   • 每个任务内部: 40 workers并行处理10个学生")
    print()
    
    results['total'] = len(BACKBONES) * len(DATASETS) * len(METHODS)
    print(f"📊 总任务数: {results['total']}")
    print()
    
    start_time = datetime.now()
    
    # 创建2个线程（每个backbone一个）
    threads = []
    for backbone_suffix, backbone in BACKBONES.items():
        t = threading.Thread(target=run_single_backbone, args=(backbone, backbone_suffix))
        t.start()
        threads.append(t)
    
    # 等待两个线程完成
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

