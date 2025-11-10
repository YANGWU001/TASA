#!/opt/venv/bin/python3
"""
运行Llama和Qwen的baseline评估 (10人样本)
支持并行运行多个任务
"""

import subprocess
import os
import time
from datetime import datetime

# 配置
BACKBONES = ['llama-3.1-8B-Instruct', 'Qwen3-4B-Instruct']
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 40  # 10人样本，可以用更高的并行度

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
    
    print(f"✅ Updated TUTOR_MODEL to: {tutor_model}")

def get_backbone_suffix(backbone):
    """获取backbone的后缀标识"""
    if 'llama' in backbone.lower():
        return 'llama'
    elif 'qwen' in backbone.lower():
        return 'qwen'
    else:
        return 'gpt'

def run_baseline(method, dataset, backbone, max_workers):
    """运行单个baseline评估"""
    print(f"\n{'='*80}")
    print(f"Running: {method} on {dataset} with {backbone}")
    print(f"{'='*80}\n")
    
    # 更新配置
    update_tasa_config(backbone)
    
    # 构建命令
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    
    # 获取backbone后缀
    backbone_suffix = get_backbone_suffix(backbone)
    
    # 调用baseline_evaluation_conservative.py（传递backbone-suffix参数）
    cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/baseline_evaluation_conservative.py --method {method} --dataset {dataset} --students-file {students_file} --max-workers {max_workers} --backbone-suffix=-{backbone_suffix}"
    
    # 日志文件
    log_file = f'/mnt/localssd/logs/baseline_{method}_{backbone_suffix}_{dataset}.log'
    
    print(f"📝 Log file: {log_file}")
    print(f"💾 Results will save to: /bank/evaluation_results/{method}-conservative-{backbone_suffix}/{dataset}/")
    
    # 运行
    with open(log_file, 'w') as f:
        result = subprocess.run(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
    
    if result.returncode == 0:
        print(f"✅ {method} on {dataset} completed successfully")
        return True
    else:
        print(f"❌ {method} on {dataset} failed with return code {result.returncode}")
        return False

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 Baseline评估：Llama + Qwen (10人样本)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    print(f"⚙️  配置:")
    print(f"   • Backbones: {BACKBONES}")
    print(f"   • Datasets: {DATASETS}")
    print(f"   • Methods: {METHODS}")
    print(f"   • Max Workers: {MAX_WORKERS}")
    print(f"   • 样本量: 每个数据集10人")
    print()
    
    # 计算总任务数
    total_tasks = len(BACKBONES) * len(DATASETS) * len(METHODS)
    print(f"📊 总任务数: {total_tasks} (2 backbones × 4 datasets × 4 methods)")
    print()
    
    start_time = datetime.now()
    completed = 0
    failed = 0
    
    # 顺序执行（避免资源竞争）
    for backbone in BACKBONES:
        backbone_suffix = get_backbone_suffix(backbone)
        print(f"\n{'#'*80}")
        print(f"# Backbone: {backbone} ({backbone_suffix})")
        print(f"{'#'*80}\n")
        
        for dataset in DATASETS:
            print(f"\n{'='*80}")
            print(f"= Dataset: {dataset}")
            print(f"{'='*80}\n")
            
            for method in METHODS:
                success = run_baseline(method, dataset, backbone, MAX_WORKERS)
                
                if success:
                    completed += 1
                else:
                    failed += 1
                
                print(f"\n进度: {completed + failed}/{total_tasks} ({completed}成功, {failed}失败)")
                print()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "━"*80)
    print("📊 最终统计")
    print("━"*80 + "\n")
    print(f"   总任务数: {total_tasks}")
    print(f"   成功: {completed}")
    print(f"   失败: {failed}")
    print(f"   总耗时: {duration}")
    print()
    print("━"*80)
    print("✅ Baseline评估完成！")
    print("━"*80)

if __name__ == '__main__':
    main()

