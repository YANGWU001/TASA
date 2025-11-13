#!/usr/bin/env python3
"""
分析delta_t分布并推荐合理的tau值
"""

import os
import json
import numpy as np
import pandas as pd
from collections import defaultdict

def load_and_analyze_delta_t(dataset_name):
    """加载数据并分析delta_t分布"""
    print(f"\n{'='*80}")
    print(f"📊 分析 {dataset_name.upper()}")
    print('='*80)
    
    data_dir = f'/mnt/localssd/pykt-toolkit/data/{dataset_name}'
    
    all_data = []
    
    # 加载train+valid
    train_valid_file = os.path.join(data_dir, 'train_valid_sequences.csv')
    if os.path.exists(train_valid_file):
        df_tv = pd.read_csv(train_valid_file)
        all_data.append(df_tv)
    
    # 加载test
    test_file = os.path.join(data_dir, 'test_sequences.csv')
    if os.path.exists(test_file):
        df_test = pd.read_csv(test_file)
        all_data.append(df_test)
    
    if not all_data:
        print(f"❌ 没有找到数据文件")
        return None
    
    df_all = pd.concat(all_data, ignore_index=True)
    
    # 收集所有的delta_t
    all_delta_t = []
    
    for idx, row in df_all.iterrows():
        # 解析timestamps
        if 'timestamps' in row and pd.notna(row['timestamps']):
            timestamps = [int(t) for t in str(row['timestamps']).split(',')]
            
            if len(timestamps) >= 2:
                # 计算相邻timestamps的差值
                for i in range(1, len(timestamps)):
                    delta = timestamps[i] - timestamps[i-1]
                    if delta > 0:
                        all_delta_t.append(delta)
    
    if not all_delta_t:
        print(f"❌ 没有有效的delta_t数据")
        return None
    
    # 统计分析
    all_delta_t = np.array(all_delta_t)
    
    print(f"\n📈 Delta_t 统计 (原始值):")
    print(f"  样本数: {len(all_delta_t):,}")
    print(f"  Min: {np.min(all_delta_t):.2f}")
    print(f"  Max: {np.max(all_delta_t):.2f}")
    print(f"  Mean: {np.mean(all_delta_t):.2f}")
    print(f"  Median (P50): {np.median(all_delta_t):.2f}")
    print(f"  P25: {np.percentile(all_delta_t, 25):.2f}")
    print(f"  P75: {np.percentile(all_delta_t, 75):.2f}")
    print(f"  P90: {np.percentile(all_delta_t, 90):.2f}")
    print(f"  P95: {np.percentile(all_delta_t, 95):.2f}")
    
    # 判断时间戳的单位
    max_val = np.max(all_delta_t)
    if max_val > 1e9:
        unit = "毫秒"
        scale = 1000 * 60  # ms -> minutes
    elif max_val > 1e6:
        unit = "秒"
        scale = 60  # seconds -> minutes
    else:
        unit = "序列索引或分钟"
        scale = 1
    
    print(f"\n🔍 推断时间单位: {unit}")
    
    # 转换为分钟
    delta_t_minutes = all_delta_t / scale
    
    print(f"\n📈 Delta_t 统计 (分钟):")
    print(f"  Mean: {np.mean(delta_t_minutes):.2f} 分钟 = {np.mean(delta_t_minutes)/60:.2f} 小时")
    print(f"  Median (P50): {np.median(delta_t_minutes):.2f} 分钟 = {np.median(delta_t_minutes)/60:.2f} 小时")
    print(f"  P75: {np.percentile(delta_t_minutes, 75):.2f} 分钟 = {np.percentile(delta_t_minutes, 75)/60:.2f} 小时")
    print(f"  P90: {np.percentile(delta_t_minutes, 90):.2f} 分钟 = {np.percentile(delta_t_minutes, 90)/60:.2f} 小时")
    
    # 推荐tau值（使用P50或P75）
    tau_p50 = np.median(delta_t_minutes)
    tau_p75 = np.percentile(delta_t_minutes, 75)
    
    print(f"\n💡 推荐的Tau值:")
    print(f"  保守选择 (P50): {tau_p50:.2f} 分钟 = {tau_p50/60:.2f} 小时 = {tau_p50/60/24:.4f} 天")
    print(f"  宽松选择 (P75): {tau_p75:.2f} 分钟 = {tau_p75/60:.2f} 小时 = {tau_p75/60/24:.4f} 天")
    
    return {
        'dataset': dataset_name,
        'n_samples': len(all_delta_t),
        'unit': unit,
        'scale': scale,
        'mean_minutes': np.mean(delta_t_minutes),
        'median_minutes': np.median(delta_t_minutes),
        'p75_minutes': np.percentile(delta_t_minutes, 75),
        'p90_minutes': np.percentile(delta_t_minutes, 90),
        'tau_p50': tau_p50,
        'tau_p75': tau_p75,
        'tau_p50_days': tau_p50 / 60 / 24,
        'tau_p75_days': tau_p75 / 60 / 24
    }

def main():
    print("="*80)
    print("📊 分析所有数据集的Delta_t分布并推荐Tau值")
    print("="*80)
    
    datasets = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2algebra2006']
    
    results = []
    for dataset in datasets:
        result = load_and_analyze_delta_t(dataset)
        if result:
            results.append(result)
    
    # 汇总推荐
    print(f"\n\n{'='*80}")
    print("📋 推荐Tau值汇总 (建议使用P50作为保守估计)")
    print("="*80)
    print()
    print(f"{'数据集':<20} {'Tau (P50分钟)':<20} {'Tau (P50天)':<20}")
    print("-"*80)
    
    for r in results:
        dataset_display = r['dataset'].replace('bridge2algebra2006', 'bridge2006')
        print(f"{dataset_display:<20} {r['tau_p50']:<20.2f} {r['tau_p50_days']:<20.6f}")
    
    print()
    print("="*80)
    print("💡 建议:")
    print("  1. 使用P50 (中位数) 作为tau，使得一半的间隔会有显著的遗忘分数")
    print("  2. 如果想要更敏感的遗忘检测，可以使用更小的tau")
    print("  3. 如果当前FS太小，说明tau太大了")
    print("="*80)

if __name__ == '__main__':
    main()

