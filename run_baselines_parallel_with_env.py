#!/opt/venv/bin/python3
"""
并行运行Baseline评估 - 使用独立配置文件
- Llama线程使用 tasa_config_llama.py
- Qwen线程使用 tasa_config_qwen.py
"""

import subprocess
import os
import threading
from datetime import datetime
import time

# 配置
BACKBONES = {
    #'gpt': ('gpt-oss-120b', 'tasa_config_gpt'),
    'llama': ('llama-3.1-8B-Instruct', 'tasa_config_llama'),
    'qwen': ('Qwen3-4B-Instruct', 'tasa_config_qwen')
}
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 10

results_lock = threading.Lock()
results = {'completed': 0, 'failed': 0, 'total': 0}

def run_single_backbone(backbone_suffix, backbone_model, config_module):
    """运行单个backbone的所有任务（顺序执行）"""
    print(f"\n{'='*80}")
    print(f"[{backbone_suffix.upper()}] 开始运行 {backbone_model}")
    print(f"[{backbone_suffix.upper()}] 使用配置: {config_module}")
    print(f"{'='*80}\n")
    
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
                
                # 设置环境变量
                env = os.environ.copy()
                env['TASA_CONFIG'] = config_module
                
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
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
                
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
    print("🚀 Baseline评估：3个Backbone真正并行执行（独立配置文件）")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    print("⚙️  执行策略:")
    print("   • GPT线程:   使用 tasa_config_gpt.py (独立配置)")
    print("   • Llama线程: 使用 tasa_config_llama.py (独立配置)")
    print("   • Qwen线程:  使用 tasa_config_qwen.py (独立配置)")
    print("   • 三个线程真正并行，不会互相干扰")
    print("   • 每个线程内部: 顺序执行16个任务，max_workers=10")
    print()
    
    results['total'] = len(BACKBONES) * len(DATASETS) * len(METHODS)
    print(f"📊 总任务数: {results['total']}")
    print()
    
    start_time = datetime.now()
    
    # 创建2个线程（每个backbone一个）
    threads = []
    for backbone_suffix, (backbone_model, config_module) in BACKBONES.items():
        t = threading.Thread(
            target=run_single_backbone, 
            args=(backbone_suffix, backbone_model, config_module)
        )
        t.start()
        threads.append(t)
        time.sleep(2)  # 错开启动时间
    
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

