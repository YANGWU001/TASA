#!/usr/bin/env python3
"""
串行处理所有数据集的完整流程：
1. 生成Pre-test
2. 筛选学生（历史vs Pre-test差距≤10%）
3. 过滤（Pre-test在20%-60%）
"""

import os
import sys
import json
import subprocess
import time

def run_command(cmd, description):
    """运行命令并显示进度"""
    print(f"\n{'='*80}")
    print(f"🚀 {description}")
    print(f"{'='*80}")
    print(f"命令: {cmd}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=False)
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  用时: {elapsed/60:.1f}分钟")
    
    if result.returncode == 0:
        print(f"✅ {description} 完成")
        return True
    else:
        print(f"❌ {description} 失败 (exit code: {result.returncode})")
        return False

def filter_students(dataset):
    """筛选和过滤学生"""
    print(f"\n{'='*80}")
    print(f"🔍 筛选 {dataset} 的学生")
    print(f"{'='*80}")
    
    # 读取所有session
    session_dir = f'/mnt/localssd/bank/session/{dataset}'
    session_files = [f for f in os.listdir(session_dir) if f.endswith('.json')]
    
    qualified_students = []
    
    for session_file in session_files:
        student_id = int(session_file.replace('.json', ''))
        
        # 加载session
        with open(f'{session_dir}/{session_file}') as f:
            session = json.load(f)
        
        concept_id = str(session['concept_id'])
        concept_text = session['concept_text']
        
        # 计算历史准确率
        original_accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total']
        
        # 读取pre-test结果
        pretest_file = f"/mnt/localssd/bank/evaluation_results/pre-test/{dataset}/student_{student_id}_concept_{concept_id}.json"
        
        if not os.path.exists(pretest_file):
            continue
        
        with open(pretest_file) as f:
            pretest_data = json.load(f)
        
        pre_test_accuracy = pretest_data['roleplay_accuracy']
        deviation = abs(original_accuracy - pre_test_accuracy)
        
        # 条件1: 历史vs Pre-test差距≤10%
        if deviation <= 0.1:
            qualified_students.append({
                'student_id': student_id,
                'concept_id': concept_id,
                'concept_text': concept_text,
                'original_accuracy': original_accuracy,
                'pre_test_accuracy': pre_test_accuracy,
                'accuracy_deviation': deviation
            })
    
    print(f"  ✅ 符合条件1（差距≤10%）: {len(qualified_students)}个学生")
    
    # 保存第一次筛选结果
    qualified_file = f'/mnt/localssd/qualified_students_{dataset}.json'
    with open(qualified_file, 'w') as f:
        json.dump({
            'dataset': dataset,
            'qualified_count': len(qualified_students),
            'max_deviation': 0.1,
            'students': qualified_students
        }, f, indent=2)
    
    # 进一步过滤: Pre-test在20%-60%
    filtered_students = [s for s in qualified_students if 0.2 < s['pre_test_accuracy'] < 0.6]
    
    print(f"  ✅ 进一步过滤（Pre 20-60%）: {len(filtered_students)}个学生")
    
    # 按Pre-test分布统计
    pre_20_30 = len([s for s in filtered_students if 0.2 < s['pre_test_accuracy'] <= 0.3])
    pre_30_40 = len([s for s in filtered_students if 0.3 < s['pre_test_accuracy'] <= 0.4])
    pre_40_50 = len([s for s in filtered_students if 0.4 < s['pre_test_accuracy'] <= 0.5])
    pre_50_60 = len([s for s in filtered_students if 0.5 < s['pre_test_accuracy'] < 0.6])
    
    print(f"\n  📊 Pre-test分布:")
    print(f"     20-30%: {pre_20_30}个")
    print(f"     30-40%: {pre_30_40}个")
    print(f"     40-50%: {pre_40_50}个")
    print(f"     50-60%: {pre_50_60}个")
    
    # 保存过滤后的结果
    filtered_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
    with open(filtered_file, 'w') as f:
        json.dump({
            'dataset': dataset,
            'total_qualified': len(qualified_students),
            'filtered_count': len(filtered_students),
            'max_deviation': 0.1,
            'min_pre_test': 0.2,
            'max_pre_test': 0.6,
            'filter_reason': 'Pre-test accuracy between 20% and 60%',
            'students': filtered_students
        }, f, indent=2)
    
    print(f"\n  💾 已保存: {qualified_file}")
    print(f"  💾 已保存: {filtered_file}")
    
    return len(qualified_students), len(filtered_students)

def process_dataset(dataset):
    """处理单个数据集"""
    print(f"\n\n{'#'*80}")
    print(f"# 处理数据集: {dataset}")
    print(f"{'#'*80}\n")
    
    # Step 1: 生成Pre-test
    pretest_dir = f'/mnt/localssd/bank/evaluation_results/pre-test/{dataset}'
    
    if os.path.exists(pretest_dir) and os.path.exists(f'{pretest_dir}/overall.json'):
        print(f"✅ Pre-test结果已存在，跳过生成")
    else:
        cmd = f"/opt/venv/bin/python3 /mnt/localssd/evaluate_all_students.py --dataset {dataset} --max-workers 10"
        success = run_command(cmd, f"生成 {dataset} 的Pre-test")
        
        if not success:
            print(f"❌ {dataset} Pre-test生成失败，跳过该数据集")
            return False
    
    # Step 2 & 3: 筛选和过滤学生
    total, filtered = filter_students(dataset)
    
    print(f"\n{'='*80}")
    print(f"✅ {dataset} 处理完成")
    print(f"{'='*80}")
    print(f"  符合条件学生: {total}个")
    print(f"  过滤后学生: {filtered}个 (Pre 20-60%)")
    
    return True

def main():
    """主函数"""
    datasets = ['algebra2005', 'bridge2006', 'nips_task34']
    
    print("="*80)
    print("🚀 开始处理所有数据集")
    print("="*80)
    print(f"数据集: {', '.join(datasets)}")
    print(f"并行度: max_workers=10")
    print(f"处理模式: 串行")
    
    overall_start = time.time()
    results = {}
    
    for dataset in datasets:
        success = process_dataset(dataset)
        results[dataset] = success
        
        if not success:
            print(f"\n⚠️  {dataset} 处理失败，继续处理下一个数据集")
    
    # 总结
    overall_time = time.time() - overall_start
    
    print(f"\n\n{'='*80}")
    print("📊 处理总结")
    print(f"{'='*80}")
    print(f"总用时: {overall_time/60:.1f}分钟")
    
    for dataset in datasets:
        status = "✅ 成功" if results.get(dataset) else "❌ 失败"
        print(f"  {dataset}: {status}")
        
        # 显示最终筛选结果
        filtered_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
        if os.path.exists(filtered_file):
            with open(filtered_file) as f:
                data = json.load(f)
            print(f"     → {data['filtered_count']}个学生待评估")
    
    print(f"\n{'='*80}")
    print("✅ 所有数据集处理完成！")
    print(f"{'='*80}")
    
    # 显示下一步
    print("\n🎯 下一步: 运行TASA评估")
    print("   使用脚本: run_tasa_all_datasets.py")

if __name__ == "__main__":
    main()

