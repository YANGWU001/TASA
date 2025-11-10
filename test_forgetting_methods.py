#!/usr/bin/env python3
"""
测试不同Forgetting Score Method的效果
在llama-3.1-8B-Instruct backbone上测试6种method，找出最好的
改进：外层循环dataset，内层循环method，快速确定每个dataset的最佳method
"""
import subprocess
import os
import json
import numpy as np
from datetime import datetime

# 配置（优先测试algebra2005，因为学生最少）
DATASETS = ['algebra2005', 'assist2017', 'bridge2006', 'nips_task34']
FS_METHODS = ['simple_time', 'history', 'lpkt', 'dkt', 'akt', 'simplekt']
BACKBONE = 'llama-3.1-8B-Instruct'
MAX_WORKERS = 30

def update_tasa_config(fs_method, backbone):
    """更新tasa_config.py的配置"""
    config_file = '/mnt/localssd/tasa_config.py'
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # 更新TUTOR_MODEL
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('TUTOR_MODEL = '):
            lines[i] = f'TUTOR_MODEL = "{backbone}"'
        elif line.startswith('FORGETTING_SCORE_METHOD = '):
            lines[i] = f'FORGETTING_SCORE_METHOD = "{fs_method}"'
    content = '\n'.join(lines)
    
    with open(config_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated config: TUTOR_MODEL={backbone}, FS_METHOD={fs_method}")

def run_tasa_experiment(fs_method, dataset, backbone):
    """运行单个TASA实验"""
    print(f"\n{'='*80}")
    print(f"Running TASA: {backbone} + {fs_method} on {dataset}")
    print(f"{'='*80}\n")
    
    # 更新配置
    update_tasa_config(fs_method, backbone)
    
    # 构建命令
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/run_tasa_batch_best_of_two.py --dataset {dataset} --students-file {students_file} --all --max-workers {MAX_WORKERS}"
    
    # 运行
    log_file = f'/mnt/localssd/logs/TASA_{backbone}_{fs_method}_{dataset}.log'
    with open(log_file, 'w') as f:
        result = subprocess.run(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
    
    return result.returncode == 0

def get_learning_gain(dataset, fs_method, backbone='llama-3.1-8B-Instruct'):
    """获取learning gain结果（新路径结构：包含method子目录）"""
    # 根据backbone确定目录后缀
    if 'llama' in backbone.lower():
        suffix = '-llama'
    elif 'qwen' in backbone.lower():
        suffix = '-qwen'
    else:
        suffix = ''  # GPT
    
    # 新路径结构：包含method子目录
    result_dir = f'/mnt/localssd/bank/evaluation_results/TASA{suffix}-best-of-2/{dataset}/{fs_method}'
    overall_file = f'{result_dir}/overall.json'
    
    if not os.path.exists(overall_file):
        print(f"   ⚠️  Overall file not found: {overall_file}")
        return None
    
    with open(overall_file, 'r') as f:
        data = json.load(f)
    
    return data['overall']['avg_learning_gain']

def main():
    print("="*80)
    print("🔬 Testing Different Forgetting Score Methods")
    print("="*80)
    print(f"Backbone: {BACKBONE}")
    print(f"Datasets: {DATASETS} (优先测试algebra2005-最少学生)")
    print(f"Methods: {FS_METHODS}")
    print(f"Max Workers: {MAX_WORKERS}")
    print(f"Loop Order: 外层Dataset → 内层Method (快速确定每个dataset最佳method)")
    print("="*80)
    
    all_results = {}
    dataset_best_methods = {}
    
    # 外层循环：Dataset（优先algebra2005）
    for dataset in DATASETS:
        print(f"\n\n{'#'*80}")
        print(f"# Testing Dataset: {dataset}")
        print(f"{'#'*80}\n")
        
        all_results[dataset] = {}
        
        # 内层循环：Method
        for fs_method in FS_METHODS:
            success = run_tasa_experiment(fs_method, dataset, BACKBONE)
            
            if success:
                gain = get_learning_gain(dataset, fs_method, BACKBONE)
                if gain is not None:
                    all_results[dataset][fs_method] = gain
                    print(f"✅ {fs_method}: Learning Gain = {gain*100:.1f}%")
                else:
                    print(f"⚠️  {fs_method}: Completed but no results found")
            else:
                print(f"❌ {fs_method}: Failed")
        
        # 找出当前dataset的最佳method
        if all_results[dataset]:
            best_method = max(all_results[dataset], key=all_results[dataset].get)
            best_gain = all_results[dataset][best_method]
            dataset_best_methods[dataset] = {
                'method': best_method,
                'gain': best_gain
            }
            print(f"\n🏆 {dataset} Best Method: {best_method} ({best_gain*100:.1f}%)")
    
    # 保存完整结果
    results_file = f'/mnt/localssd/forgetting_method_comparison_{BACKBONE}.json'
    with open(results_file, 'w') as f:
        json.dump({
            'all_results': all_results,
            'dataset_best_methods': dataset_best_methods,
            'backbone': BACKBONE,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n\n{'='*80}")
    print("📊 Final Results Summary")
    print(f"{'='*80}\n")
    
    # 显示每个dataset的最佳method
    print("每个Dataset的最佳Method:")
    print("-" * 60)
    for dataset, info in dataset_best_methods.items():
        print(f"  {dataset:20s}: {info['method']:15s} ({info['gain']*100:.1f}%)")
    
    # 计算每个method的跨dataset平均表现
    print(f"\n各Method的平均表现（跨{len(DATASETS)}个datasets）:")
    print("-" * 60)
    method_averages = {}
    for method in FS_METHODS:
        gains = [all_results[ds].get(method) for ds in DATASETS if method in all_results[ds]]
        if gains:
            avg = np.mean([g for g in gains if g is not None])
            method_averages[method] = avg
            print(f"  {method:15s}: {avg*100:.1f}% (across {len(gains)} datasets)")
    
    # 找出全局最佳method
    if method_averages:
        best_overall_method = max(method_averages, key=method_averages.get)
        print(f"\n🏆 Overall Best Method: {best_overall_method} ({method_averages[best_overall_method]*100:.1f}%)")
        
        # 保存最佳method
        with open('/mnt/localssd/best_forgetting_method.txt', 'w') as f:
            f.write(best_overall_method)
        
        print(f"✅ Best method saved to: best_forgetting_method.txt")
    
    print(f"\n✅ Results saved to: {results_file}")

if __name__ == '__main__':
    main()
