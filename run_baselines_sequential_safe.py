#!/opt/venv/bin/python3
"""
顺序运行Baseline评估 - 避免配置文件冲突
先运行Llama（16任务），再运行Qwen（16任务）
"""

import subprocess
import os
from datetime import datetime

# 配置
BACKBONES = [
    ('llama', 'llama-3.1-8B-Instruct'),
    ('qwen', 'Qwen3-4B-Instruct')
]
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 10

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
    print(f"   ✅ TUTOR_MODEL 设置为: {tutor_model}")

def run_baseline(method, dataset, backbone_suffix):
    """运行单个baseline任务"""
    try:
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
                return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 Baseline评估：顺序执行（Llama → Qwen）")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    start_time = datetime.now()
    total_tasks = len(BACKBONES) * len(DATASETS) * len(METHODS)
    completed = 0
    failed = 0
    
    # 顺序处理每个backbone
    for backbone_suffix, backbone_model in BACKBONES:
        print(f"\n{'='*80}")
        print(f"[{backbone_suffix.upper()}] 开始运行: {backbone_model}")
        print(f"{'='*80}\n")
        
        # 更新配置
        update_tasa_config(backbone_model)
        
        # 顺序运行16个任务
        for dataset in DATASETS:
            print(f"\n[{backbone_suffix.upper()}] Dataset: {dataset}")
            print(f"-" * 80)
            
            for method in METHODS:
                task_name = f"{method} on {dataset}"
                print(f"[{backbone_suffix.upper()}] 运行: {task_name}...")
                
                success = run_baseline(method, dataset, backbone_suffix)
                
                if success:
                    completed += 1
                    print(f"[{backbone_suffix.upper()}] ✅ {task_name} 完成 ({completed}/{total_tasks})")
                else:
                    failed += 1
                    print(f"[{backbone_suffix.upper()}] ❌ {task_name} 失败 ({failed}个失败)")
        
        print(f"\n{'='*80}")
        print(f"[{backbone_suffix.upper()}] 完成！")
        print(f"{'='*80}\n")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 打印结果
    print("\n" + "━"*80)
    print("📊 最终统计")
    print("━"*80)
    print(f"总任务数: {total_tasks}")
    print(f"成功: {completed}")
    print(f"失败: {failed}")
    print(f"总耗时: {duration}")
    print("━"*80)

if __name__ == '__main__':
    main()

