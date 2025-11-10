#!/usr/bin/env python3
"""
重新运行失败的Baseline评估任务
"""
import subprocess
import os
import sys
import time

# 失败的任务列表
FAILED_TASKS = {
    'llama': [
        ('PSS-MV', 'assist2017'),
        ('PSS-MV', 'algebra2005'),
    ],
    'qwen': [
        ('Vanilla-ICL', 'algebra2005'),
        ('Vanilla-ICL', 'bridge2006'),
        ('MathChat', 'bridge2006'),
        ('TutorLLM', 'nips_task34'),
        ('TutorLLM', 'algebra2005'),
    ]
}

MAX_WORKERS = 10

def run_single_baseline(method, dataset, backbone):
    """运行单个baseline任务"""
    backbone_suffix = f'-{backbone}'
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    log_file = f'/mnt/localssd/logs/baseline_{method}_{backbone_suffix}_{dataset}_RERUN.log'
    
    # 检查students文件
    if not os.path.exists(students_file):
        students_file_alt = f'/mnt/localssd/qualified_students_{dataset}.json'
        if os.path.exists(students_file_alt):
            students_file = students_file_alt
        else:
            print(f"❌ Students file not found for {dataset}")
            return False
    
    # 设置环境变量
    env = os.environ.copy()
    env['TASA_CONFIG'] = f'tasa_config_{backbone}'
    
    print(f"\n{'='*80}")
    print(f"🔄 重新运行: {method} on {dataset} ({backbone.upper()})")
    print(f"{'='*80}")
    print(f"  📂 Students file: {students_file}")
    print(f"  📝 Log file: {log_file}")
    print(f"  ⚙️  Config: tasa_config_{backbone}")
    print(f"  🔧 Max workers: {MAX_WORKERS}")
    
    cmd = [
        '/opt/venv/bin/python3',
        '/mnt/localssd/baseline_evaluation_conservative.py',
        '--method', method,
        '--dataset', dataset,
        '--students-file', students_file,
        '--max-workers', str(MAX_WORKERS),
        f'--backbone-suffix={backbone_suffix}'
    ]
    
    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
        
        if result.returncode == 0:
            # 检查是否真的成功（有overall.json）
            result_file = f'/mnt/localssd/bank/evaluation_results/{method}-conservative-{backbone}/{dataset}/overall.json'
            if os.path.exists(result_file):
                print(f"✅ {method} on {dataset} ({backbone}) 完成")
                return True
            else:
                print(f"⚠️  {method} on {dataset} ({backbone}) 进程完成但无结果文件")
                return False
        else:
            print(f"❌ {method} on {dataset} ({backbone}) 失败 (exit code: {result.returncode})")
            return False
    
    except Exception as e:
        print(f"❌ {method} on {dataset} ({backbone}) 异常: {e}")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                  🔄 重新运行失败的Baseline任务                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    total_llama = len(FAILED_TASKS['llama'])
    total_qwen = len(FAILED_TASKS['qwen'])
    total_tasks = total_llama + total_qwen
    
    print(f"\n📋 任务清单:")
    print(f"  🔵 Llama: {total_llama} 个任务")
    for method, dataset in FAILED_TASKS['llama']:
        print(f"     • {method} on {dataset}")
    
    print(f"  🟣 Qwen: {total_qwen} 个任务")
    for method, dataset in FAILED_TASKS['qwen']:
        print(f"     • {method} on {dataset}")
    
    print(f"\n  🔥 总计: {total_tasks} 个任务")
    print(f"  ⚙️  Max workers: {MAX_WORKERS}")
    print(f"\n⏱️  预计时间: ~{total_tasks * 3}-{total_tasks * 5}分钟")
    print(f"\n{'='*80}\n")
    
    start_time = time.time()
    results = {'llama': [], 'qwen': []}
    
    # 运行Llama任务
    if FAILED_TASKS['llama']:
        print("\n╔══════════════════════════════════════════════════════════════════════════════╗")
        print("║                       🔵 运行 Llama 失败任务                                ║")
        print("╚══════════════════════════════════════════════════════════════════════════════╝\n")
        
        for method, dataset in FAILED_TASKS['llama']:
            success = run_single_baseline(method, dataset, 'llama')
            results['llama'].append((method, dataset, success))
            time.sleep(2)  # 短暂延迟
    
    # 运行Qwen任务
    if FAILED_TASKS['qwen']:
        print("\n╔══════════════════════════════════════════════════════════════════════════════╗")
        print("║                       🟣 运行 Qwen 失败任务                                 ║")
        print("╚══════════════════════════════════════════════════════════════════════════════╝\n")
        
        for method, dataset in FAILED_TASKS['qwen']:
            success = run_single_baseline(method, dataset, 'qwen')
            results['qwen'].append((method, dataset, success))
            time.sleep(2)  # 短暂延迟
    
    elapsed = time.time() - start_time
    
    # 汇总结果
    print("\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                            📊 重跑结果汇总                                   ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝\n")
    
    llama_success = sum(1 for _, _, success in results['llama'] if success)
    qwen_success = sum(1 for _, _, success in results['qwen'] if success)
    total_success = llama_success + qwen_success
    
    print("🔵 Llama 任务:")
    for method, dataset, success in results['llama']:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {status} - {method} on {dataset}")
    
    print(f"\n🟣 Qwen 任务:")
    for method, dataset, success in results['qwen']:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {status} - {method} on {dataset}")
    
    print(f"\n{'='*80}")
    print(f"✅ Llama成功: {llama_success}/{total_llama}")
    print(f"✅ Qwen成功: {qwen_success}/{total_qwen}")
    print(f"✅ 总成功: {total_success}/{total_tasks}")
    print(f"❌ 总失败: {total_tasks - total_success}/{total_tasks}")
    print(f"⏱️  总耗时: {elapsed/60:.1f} 分钟")
    print(f"{'='*80}\n")
    
    # 如果有失败的任务，打印日志文件位置
    if total_success < total_tasks:
        print("💡 失败任务的日志文件:")
        for backbone in ['llama', 'qwen']:
            for method, dataset, success in results[backbone]:
                if not success:
                    log_file = f"logs/baseline_{method}_-{backbone}_{dataset}_RERUN.log"
                    print(f"  📄 {log_file}")
        print()
    
    return total_success == total_tasks

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

