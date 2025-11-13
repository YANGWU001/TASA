#!/usr/bin/env python3
"""
Master脚本：运行所有backbone的TASA和Baseline实验
1. 备份旧的gpt-oss-120b结果
2. 测试不同FS method (llama)
3. 用最好的FS method运行所有实验
4. 运行llama和qwen的TASA和Baselines
"""
import subprocess
import os
import shutil
import json
from datetime import datetime

# 配置
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
BASELINE_METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
BACKBONES = ['gpt-oss-120b', 'llama-3.1-8b', 'qwen3-4b']
TASA_MAX_WORKERS = 30
BASELINE_MAX_WORKERS = 40

def backup_gpt_results():
    """备份旧的gpt-oss-120b TASA结果"""
    print("="*80)
    print("📦 Backing up old GPT-OSS-120B results...")
    print("="*80)
    
    old_dir = '/mnt/localssd/bank/evaluation_results/TASA-best-of-2'
    backup_dir = f'/mnt/localssd/bank/evaluation_results/TASA-best-of-2_OLD_simple_time_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    if os.path.exists(old_dir):
        shutil.copytree(old_dir, backup_dir)
        print(f"✅ Backed up to: {backup_dir}")
    else:
        print(f"⚠️  No old results found at: {old_dir}")

def get_best_fs_method():
    """获取最好的FS method"""
    best_method_file = '/mnt/localssd/best_forgetting_method.txt'
    
    if os.path.exists(best_method_file):
        with open(best_method_file, 'r') as f:
            best_method = f.read().strip()
        print(f"📊 Using best FS method: {best_method}")
        return best_method
    else:
        print("⚠️  Best FS method not found, using 'history' as default")
        return 'history'

def update_config_for_backbone(backbone, fs_method):
    """更新配置文件"""
    config_file = '/mnt/localssd/tasa_config.py'
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # 更新TUTOR_MODEL
    import re
    content = re.sub(
        r'TUTOR_MODEL = ".*?"',
        f'TUTOR_MODEL = "{backbone}"',
        content
    )
    
    # 更新FORGETTING_SCORE_METHOD
    content = re.sub(
        r'FORGETTING_SCORE_METHOD = ".*?"',
        f'FORGETTING_SCORE_METHOD = "{fs_method}"',
        content
    )
    
    with open(config_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Config updated: backbone={backbone}, fs_method={fs_method}")

def run_tasa_all_datasets(backbone, fs_method):
    """运行所有数据集的TASA实验"""
    print(f"\n{'='*80}")
    print(f"🚀 Running TASA: {backbone} + {fs_method}")
    print(f"{'='*80}\n")
    
    update_config_for_backbone(backbone, fs_method)
    
    for dataset in DATASETS:
        print(f"\n### Dataset: {dataset} ###")
        
        if dataset == 'nips_task34':
            students_file = '/mnt/localssd/qualified_students_nips_task34_150sampled.json'
            cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/run_tasa_with_backbone.py --dataset {dataset} --backbone {backbone} --students-file {students_file} --all --max-workers {TASA_MAX_WORKERS}"
        else:
            cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/run_tasa_with_backbone.py --dataset {dataset} --backbone {backbone} --range20to60 --all --max-workers {TASA_MAX_WORKERS}"
        
        log_file = f'/mnt/localssd/logs/TASA_{backbone}_{fs_method}_{dataset}.log'
        
        print(f"  Running: {cmd}")
        print(f"  Log: {log_file}")
        
        with open(log_file, 'w') as f:
            result = subprocess.run(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
        
        if result.returncode == 0:
            print(f"  ✅ Completed")
        else:
            print(f"  ❌ Failed")

def run_baselines_all_datasets(backbone):
    """运行所有数据集的Baseline实验"""
    print(f"\n{'='*80}")
    print(f"🚀 Running Baselines: {backbone}")
    print(f"{'='*80}\n")
    
    # Baseline不需要FS method，但需要更新TUTOR_MODEL
    # 需要修改baseline相关代码来支持不同backbone
    # 这里先创建命令框架
    
    for method in BASELINE_METHODS:
        for dataset in DATASETS:
            print(f"\n### {method} on {dataset} ###")
            
            cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/baseline_evaluation_with_backbone.py --method {method} --dataset {dataset} --backbone {backbone} --max-workers {BASELINE_MAX_WORKERS}"
            
            log_file = f'/mnt/localssd/logs/{method}_{backbone}_{dataset}.log'
            
            print(f"  Running: {cmd}")
            print(f"  Log: {log_file}")
            
            with open(log_file, 'w') as f:
                result = subprocess.run(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
            
            if result.returncode == 0:
                print(f"  ✅ Completed")
            else:
                print(f"  ❌ Failed")

def generate_summary_report():
    """生成总结报告"""
    print("\n" + "="*80)
    print("📊 Generating Summary Report")
    print("="*80)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "backbones": BACKBONES,
        "datasets": DATASETS,
        "results": {}
    }
    
    # 收集所有结果
    for backbone in BACKBONES:
        summary["results"][backbone] = {
            "TASA": {},
            "Baselines": {}
        }
        
        # TASA results
        for dataset in DATASETS:
            if backbone == 'gpt-oss-120b':
                result_dir = f'/mnt/localssd/bank/evaluation_results/TASA-best-of-2/{dataset}'
            elif backbone == 'llama-3.1-8b':
                result_dir = f'/mnt/localssd/bank/evaluation_results/TASA-llama-best-of-2/{dataset}'
            elif backbone == 'qwen3-4b':
                result_dir = f'/mnt/localssd/bank/evaluation_results/TASA-qwen-best-of-2/{dataset}'
            
            overall_file = f'{result_dir}/overall.json'
            if os.path.exists(overall_file):
                with open(overall_file, 'r') as f:
                    data = json.load(f)
                summary["results"][backbone]["TASA"][dataset] = data['overall']['avg_learning_gain']
        
        # Baseline results
        for method in BASELINE_METHODS:
            if method not in summary["results"][backbone]["Baselines"]:
                summary["results"][backbone]["Baselines"][method] = {}
            
            for dataset in DATASETS:
                result_dir = f'/mnt/localssd/bank/evaluation_results/{method}-{backbone}-conservative/{dataset}'
                overall_file = f'{result_dir}/overall.json'
                
                if os.path.exists(overall_file):
                    with open(overall_file, 'r') as f:
                        data = json.load(f)
                    summary["results"][backbone]["Baselines"][method][dataset] = {
                        "max": data['strategy_max']['avg_learning_gain'],
                        "avg": data['strategy_avg']['avg_learning_gain'],
                        "min": data['strategy_min']['avg_learning_gain']
                    }
    
    # 保存报告
    report_file = f'/mnt/localssd/backbone_comparison_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Report saved to: {report_file}")
    
    # 打印简要总结
    print("\n" + "="*80)
    print("📈 Quick Summary")
    print("="*80)
    
    for backbone in BACKBONES:
        print(f"\n{backbone}:")
        if "TASA" in summary["results"][backbone]:
            tasa_results = summary["results"][backbone]["TASA"]
            if tasa_results:
                avg_gain = sum(tasa_results.values()) / len(tasa_results)
                print(f"  TASA Average: {avg_gain*100:.2f}%")

def main():
    print("="*80)
    print("🚀 Running All Experiments with Different Backbones")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backbones: {BACKBONES}")
    print(f"Datasets: {DATASETS}")
    print("="*80)
    
    # Step 1: 备份旧结果
    backup_gpt_results()
    
    # Step 2: 测试不同FS method (on llama)
    print("\n" + "="*80)
    print("Step 1: Testing different FS methods on llama...")
    print("="*80)
    subprocess.run("python3 /mnt/localssd/test_forgetting_methods.py", shell=True)
    
    # Step 3: 获取最好的FS method
    best_fs_method = get_best_fs_method()
    
    # Step 4: 运行所有backbone的TASA实验
    for backbone in BACKBONES:
        print(f"\n{'#'*80}")
        print(f"# Backbone: {backbone}")
        print(f"{'#'*80}")
        
        run_tasa_all_datasets(backbone, best_fs_method)
        run_baselines_all_datasets(backbone)
    
    # Step 5: 生成报告
    generate_summary_report()
    
    print("\n" + "="*80)
    print("✅ All Experiments Completed!")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == '__main__':
    main()

