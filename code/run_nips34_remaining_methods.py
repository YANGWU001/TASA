#!/opt/venv/bin/python3
"""
续跑TASA-Llama在nips_task34上的剩余FS methods
"""

import subprocess
import os
import json
import time
from datetime import datetime

BACKBONE = 'llama-3.1-8B-Instruct'
DATASET = 'nips_task34'

# 已完成的方法（从evaluation_results验证）
COMPLETED = ['simple_time', 'history']

# 需要运行的剩余方法
REMAINING_METHODS = ['lpkt', 'dkt', 'akt', 'simplekt']

def update_config(fs_method):
    """更新tasa_config.py中的TUTOR_MODEL和FORGETTING_SCORE_METHOD"""
    config_file = '/mnt/localssd/tasa_config.py'
    with open(config_file, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('TUTOR_MODEL = '):
            lines[i] = f'TUTOR_MODEL = "{BACKBONE}"'
        elif line.startswith('FORGETTING_SCORE_METHOD = '):
            lines[i] = f'FORGETTING_SCORE_METHOD = "{fs_method}"'
    
    with open(config_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Updated config: TUTOR_MODEL={BACKBONE}, FS_METHOD={fs_method}")

def get_learning_gain(dataset, fs_method):
    """读取learning gain"""
    result_dir = f'/mnt/localssd/bank/evaluation_results/TASA-llama-best-of-2/{dataset}/{fs_method}'
    overall_file = f'{result_dir}/overall.json'
    
    if not os.path.exists(overall_file):
        return None
    
    with open(overall_file, 'r') as f:
        data = json.load(f)
    
    return data.get('overall', {}).get('avg_learning_gain', 0)

def run_tasa_experiment(dataset, fs_method):
    """运行单个TASA实验"""
    print(f"\n{'='*80}")
    print(f"Running TASA: {BACKBONE} + {fs_method} on {dataset}")
    print(f"{'='*80}\n")
    
    # 更新配置
    update_config(fs_method)
    
    # 运行TASA
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    cmd = [
        '/opt/venv/bin/python3',
        '/mnt/localssd/run_tasa_batch_best_of_two.py',
        '--dataset', dataset,
        '--students-file', students_file,
        '--max-workers', '10'
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        gain = get_learning_gain(dataset, fs_method)
        if gain is not None:
            print(f"✅ {fs_method}: Learning Gain = {gain*100:.1f}% (耗时: {elapsed/60:.1f}分钟)")
        else:
            print(f"⚠️  {fs_method}: 完成但未找到结果文件")
    else:
        print(f"❌ {fs_method}: 失败 (返回码 {result.returncode})")

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║            🚀 续跑TASA-Llama on nips_task34 剩余方法                         ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"📋 数据集: {DATASET}")
    print(f"🧠 Backbone: {BACKBONE}")
    print(f"✅ 已完成: {', '.join(COMPLETED)}")
    print(f"🔄 待运行: {', '.join(REMAINING_METHODS)}")
    print(f"📊 学生数: 10 (已采样)")
    print(f"⚡ 并行度: 10 workers")
    print()
    
    overall_start = time.time()
    
    # 运行剩余方法
    for fs_method in REMAINING_METHODS:
        run_tasa_experiment(DATASET, fs_method)
    
    # 汇总所有方法的结果
    print(f"\n{'='*80}")
    print(f"📊 nips_task34 所有方法汇总")
    print(f"{'='*80}")
    
    all_methods = COMPLETED + REMAINING_METHODS
    gains = {}
    
    for fs_method in all_methods:
        gain = get_learning_gain(DATASET, fs_method)
        if gain is not None:
            gains[fs_method] = gain
            print(f"  {fs_method:15s}: Learning Gain = {gain*100:.1f}%")
        else:
            print(f"  {fs_method:15s}: ❌ 未找到结果")
    
    if gains:
        best_method = max(gains, key=gains.get)
        worst_method = min(gains, key=gains.get)
        
        print(f"\n🏆 最佳方法: {best_method} ({gains[best_method]*100:.1f}%)")
        print(f"📉 最差方法: {worst_method} ({gains[worst_method]*100:.1f}%)")
        print(f"📊 平均Learning Gain: {sum(gains.values())/len(gains)*100:.1f}%")
    
    overall_time = time.time() - overall_start
    print(f"\n⏱️  总耗时: {overall_time/60:.1f}分钟 ({overall_time/3600:.1f}小时)")
    print("="*80)
    print("✅ nips_task34实验完成！")
    print("="*80)

if __name__ == '__main__':
    main()

