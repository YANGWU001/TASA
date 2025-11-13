#!/usr/bin/env python3
"""
运行TASA-Llama在nips_task34数据集上的所有FS methods测试
"""
import os
import subprocess
import time

# 只运行nips_task34
DATASET = 'nips_task34'

# 所有6种FS methods
FS_METHODS = ['simple_time', 'history', 'lpkt', 'dkt', 'akt', 'simplekt']

# 设置max_workers
MAX_WORKERS = 10

def run_fs_method(dataset, fs_method):
    """运行单个FS method的TASA测试"""
    print(f"\n{'='*100}")
    print(f"🚀 Running TASA-Llama on {dataset} with {fs_method}")
    print(f"{'='*100}\n")
    
    start_time = time.time()
    
    # 设置环境变量
    env = os.environ.copy()
    env['TASA_CONFIG'] = 'tasa_config_llama'
    env['FORGETTING_SCORE_METHOD'] = fs_method
    
    # 学生采样文件
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    
    # 运行命令
    cmd = [
        '/opt/venv/bin/python3',
        '/mnt/localssd/run_tasa_batch_best_of_two.py',
        '--dataset', dataset,
        '--students-file', students_file,
        '--max-workers', str(MAX_WORKERS)
    ]
    
    log_file = f'/mnt/localssd/logs/tasa_llama_{dataset}_{fs_method}.log'
    
    with open(log_file, 'w') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ {dataset}/{fs_method} completed (耗时: {elapsed/60:.1f}分钟)")
        return True
    else:
        print(f"❌ {dataset}/{fs_method} failed")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║          🚀 TASA-Llama FS Methods测试 (nips_task34 only)                   ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"📊 配置:")
    print(f"  • Dataset: {DATASET}")
    print(f"  • FS Methods: {len(FS_METHODS)} 个")
    print(f"  • Max workers: {MAX_WORKERS}")
    print(f"  • 学生数: 10")
    print(f"  • API: https://2d96013eaaf0.ngrok-free.app")
    print()
    print(f"📝 待运行的Methods:")
    for i, method in enumerate(FS_METHODS, 1):
        print(f"  {i}. {method}")
    print()
    print("="*100)
    print()
    
    total_start = time.time()
    success_count = 0
    failed_methods = []
    
    for fs_method in FS_METHODS:
        if run_fs_method(DATASET, fs_method):
            success_count += 1
        else:
            failed_methods.append(fs_method)
    
    total_elapsed = time.time() - total_start
    
    print("\n" + "="*100)
    print("📊 最终统计")
    print("="*100)
    print(f"✅ 成功: {success_count}/{len(FS_METHODS)}")
    if failed_methods:
        print(f"❌ 失败: {len(failed_methods)} 个")
        print(f"   失败的methods: {', '.join(failed_methods)}")
    print(f"⏱️  总耗时: {total_elapsed/60:.1f}分钟")
    print("="*100)

if __name__ == '__main__':
    main()

