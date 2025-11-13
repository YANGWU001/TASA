#!/opt/venv/bin/python3
"""
续跑TASA Llama KT Methods测试
从bridge2006的akt和simplekt开始，然后nips_task34全部
"""

import subprocess
import os
import json

BACKBONE = 'llama-3.1-8B-Instruct'
FS_METHODS = ['simple_time', 'history', 'lpkt', 'dkt', 'akt', 'simplekt']

# 需要运行的任务
TASKS = [
    ('bridge2006', ['akt', 'simplekt']),  # bridge2006只需要跑最后两个
    ('nips_task34', FS_METHODS)  # nips_task34全部
]

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
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        gain = get_learning_gain(dataset, fs_method)
        if gain is not None:
            print(f"✅ {fs_method}: Learning Gain = {gain*100:.1f}%")
        else:
            print(f"⚠️  {fs_method}: 完成但未找到结果文件")
    else:
        print(f"❌ {fs_method}: 失败 (返回码 {result.returncode})")

def main():
    print("="*80)
    print("🚀 续跑TASA Llama KT Methods测试")
    print("="*80)
    print(f"\n📋 待运行任务:")
    for dataset, methods in TASKS:
        print(f"  • {dataset}: {', '.join(methods)}")
    print()
    
    # 运行所有任务
    for dataset, methods in TASKS:
        print(f"\n{'#'*80}")
        print(f"# Testing Dataset: {dataset}")
        print(f"{'#'*80}\n")
        
        for fs_method in methods:
            run_tasa_experiment(dataset, fs_method)
        
        # 输出该dataset的最佳方法
        print(f"\n{'='*80}")
        gains = {}
        for fs_method in FS_METHODS:
            gain = get_learning_gain(dataset, fs_method)
            if gain is not None:
                gains[fs_method] = gain
        
        if gains:
            best_method = max(gains, key=gains.get)
            print(f"🏆 {dataset} Best Method: {best_method} ({gains[best_method]*100:.1f}%)")
        print(f"{'='*80}\n")
    
    print("\n" + "="*80)
    print("✅ 续跑完成！")
    print("="*80)

if __name__ == '__main__':
    main()

