#!/opt/venv/bin/python3
"""
顺序运行所有baseline任务（简化版）
"""

import subprocess
import os
from datetime import datetime

# 配置
BACKBONES = ['llama-3.1-8B-Instruct', 'Qwen3-4B-Instruct']
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 40

def get_backbone_suffix(backbone):
    if 'llama' in backbone.lower():
        return 'llama'
    elif 'qwen' in backbone.lower():
        return 'qwen'
    else:
        return 'gpt'

def update_tasa_config(tutor_model):
    """更新tasa_config.py的TUTOR_MODEL"""
    config_file = '/mnt/localssd/tasa_config.py'
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('TUTOR_MODEL = '):
            lines[i] = f'TUTOR_MODEL = "{tutor_model}"'
    
    with open(config_file, 'w') as f:
        f.write('\n'.join(lines))

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🚀 Baseline评估：Llama + Qwen (10人样本, 顺序执行)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

total_tasks = len(BACKBONES) * len(DATASETS) * len(METHODS)
print(f"总任务数: {total_tasks}")
print()

start_time = datetime.now()
completed = 0
failed = 0

for backbone in BACKBONES:
    backbone_suffix = get_backbone_suffix(backbone)
    print(f"\n{'#'*80}")
    print(f"# Backbone: {backbone}")
    print(f"{'#'*80}\n")
    
    # 更新配置
    update_tasa_config(backbone)
    
    for dataset in DATASETS:
        print(f"\n{'='*80}")
        print(f"= Dataset: {dataset}")
        print(f"{'='*80}\n")
        
        for method in METHODS:
            print(f"\n{'-'*80}")
            print(f"Running: {method} on {dataset} with {backbone}")
            print(f"{'-'*80}")
            
            students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
            
            # 构建命令
            cmd = [
                '/opt/venv/bin/python3', '-u',
                '/mnt/localssd/baseline_evaluation_conservative.py',
                '--method', method,
                '--dataset', dataset,
                '--students-file', students_file,
                '--max-workers', str(MAX_WORKERS),
                '--backbone-suffix', f'-{backbone_suffix}'  # 作为一个参数值
            ]
            
            log_file = f'/mnt/localssd/logs/baseline_{method}_{backbone_suffix}_{dataset}.log'
            
            print(f"📝 Log: {log_file}")
            print(f"💾 Output: /bank/evaluation_results/{method}-conservative-{backbone_suffix}/{dataset}/")
            
            # 运行
            with open(log_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
            
            if result.returncode == 0:
                print(f"✅ 成功")
                completed += 1
            else:
                print(f"❌ 失败 (code {result.returncode})")
                failed += 1
            
            print(f"进度: {completed + failed}/{total_tasks} ({completed}成功, {failed}失败)")

end_time = datetime.now()
duration = end_time - start_time

print("\n" + "━"*80)
print("📊 最终统计")
print("━"*80)
print(f"总任务数: {total_tasks}")
print(f"成功: {completed}")
print(f"失败: {failed}")
print(f"总耗时: {duration}")
print("━"*80)

