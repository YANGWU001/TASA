#!/usr/bin/env python3
"""
对所有数据集运行TASA评估
每个数据集使用其过滤后的学生列表（Pre-test在20%-60%）
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime

def check_student_list(dataset):
    """检查学生列表是否存在"""
    filtered_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
    
    if not os.path.exists(filtered_file):
        print(f"❌ {dataset} 的学生列表不存在: {filtered_file}")
        return None
    
    with open(filtered_file) as f:
        data = json.load(f)
    
    return data

def run_tasa_for_dataset(dataset, max_workers=10):
    """对单个数据集运行TASA评估"""
    print(f"\n\n{'#'*80}")
    print(f"# TASA评估: {dataset}")
    print(f"{'#'*80}\n")
    
    # 检查学生列表
    data = check_student_list(dataset)
    if not data:
        return False
    
    student_count = data['filtered_count']
    
    print(f"{'='*80}")
    print(f"📊 {dataset} 评估配置")
    print(f"{'='*80}")
    print(f"  学生数: {student_count}个")
    print(f"  条件: Pre-test在20%-60%")
    print(f"  并行度: {max_workers} workers")
    print(f"  方法: TASA-best-of-2")
    
    # 预估时间
    estimated_time = (student_count * 6.5) / max_workers  # 分钟
    print(f"  预计时间: {estimated_time:.0f}分钟 ({estimated_time/60:.1f}小时)")
    
    # 构建命令
    # 需要先创建该数据集的学生列表文件
    cmd = f"""
cd /mnt/localssd && /opt/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/mnt/localssd')

from run_tasa_batch_best_of_two import run_batch_evaluation
import json

# 读取学生列表
with open('qualified_students_{dataset}_20to60.json') as f:
    data = json.load(f)

student_ids = [s['student_id'] for s in data['students']]

print(f'将评估 {{len(student_ids)}} 个学生')

# 运行评估
results = run_batch_evaluation(
    student_ids=student_ids,
    dataset='{dataset}',
    max_workers={max_workers}
)

print(f'\\n✅ {dataset} 评估完成！')
"
"""
    
    # 创建日志文件
    log_file = f'/mnt/localssd/logs/tasa_{dataset}.log'
    print(f"  日志文件: {log_file}")
    
    print(f"\n{'='*80}")
    print(f"🚀 开始评估 {dataset}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # 运行命令
    with open(log_file, 'w') as log:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=log,
            stderr=subprocess.STDOUT
        )
    
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  实际用时: {elapsed/60:.1f}分钟")
    
    if result.returncode == 0:
        print(f"✅ {dataset} 评估完成")
        
        # 读取结果统计
        overall_file = f'/mnt/localssd/bank/evaluation_results/TASA-best-of-2/{dataset}/overall.json'
        if os.path.exists(overall_file):
            with open(overall_file) as f:
                overall = json.load(f)
            
            print(f"\n📊 评估结果:")
            print(f"   学生数: {overall['num_students']}")
            print(f"   平均Gain: {overall['overall']['avg_learning_gain']*100:.1f}%")
            print(f"   中位数: {overall['overall']['median_learning_gain']*100:.1f}%")
        
        return True
    else:
        print(f"❌ {dataset} 评估失败 (exit code: {result.returncode})")
        print(f"   查看日志: {log_file}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='对所有数据集运行TASA评估')
    parser.add_argument('--datasets', nargs='+', 
                       default=['assist2017', 'algebra2005', 'bridge2006', 'nips_task34'],
                       help='要评估的数据集列表')
    parser.add_argument('--max-workers', type=int, default=10,
                       help='每个数据集的并行度')
    parser.add_argument('--skip-assist2017', action='store_true',
                       help='跳过assist2017（如果已经在运行）')
    
    args = parser.parse_args()
    
    datasets = args.datasets
    if args.skip_assist2017 and 'assist2017' in datasets:
        datasets.remove('assist2017')
        print("⏭️  跳过assist2017（假设已在运行）")
    
    print("="*80)
    print("🚀 TASA多数据集评估")
    print("="*80)
    print(f"数据集: {', '.join(datasets)}")
    print(f"并行度: {args.max_workers} workers per dataset")
    print(f"处理模式: 串行（一个接一个）")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    overall_start = time.time()
    results = {}
    
    for i, dataset in enumerate(datasets, 1):
        print(f"\n\n{'='*80}")
        print(f"处理进度: {i}/{len(datasets)}")
        print(f"{'='*80}")
        
        success = run_tasa_for_dataset(dataset, args.max_workers)
        results[dataset] = success
        
        if not success:
            print(f"\n⚠️  {dataset} 评估失败，继续下一个数据集")
    
    # 总结
    overall_time = time.time() - overall_start
    
    print(f"\n\n{'='*80}")
    print("📊 所有数据集评估总结")
    print(f"{'='*80}")
    print(f"总用时: {overall_time/60:.1f}分钟 ({overall_time/3600:.1f}小时)")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n结果:")
    for dataset in datasets:
        status = "✅ 成功" if results.get(dataset) else "❌ 失败"
        print(f"  {dataset}: {status}")
        
        # 显示结果统计
        overall_file = f'/mnt/localssd/bank/evaluation_results/TASA-best-of-2/{dataset}/overall.json'
        if os.path.exists(overall_file):
            with open(overall_file) as f:
                data = json.load(f)
            print(f"     → {data['num_students']}个学生, 平均Gain={data['overall']['avg_learning_gain']*100:.1f}%")
    
    print(f"\n{'='*80}")
    print("✅ 多数据集TASA评估完成！")
    print(f"{'='*80}")
    
    # 保存总结
    summary_file = '/mnt/localssd/tasa_all_datasets_summary.json'
    summary = {
        'datasets': list(results.keys()),
        'start_time': datetime.now().isoformat(),
        'total_time_minutes': overall_time / 60,
        'results': results,
        'max_workers': args.max_workers
    }
    
    # 添加每个数据集的统计
    for dataset in datasets:
        overall_file = f'/mnt/localssd/bank/evaluation_results/TASA-best-of-2/{dataset}/overall.json'
        if os.path.exists(overall_file):
            with open(overall_file) as f:
                data = json.load(f)
            summary[dataset] = {
                'num_students': data['num_students'],
                'avg_learning_gain': data['overall']['avg_learning_gain'],
                'median_learning_gain': data['overall']['median_learning_gain']
            }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 总结已保存: {summary_file}")

if __name__ == "__main__":
    main()

