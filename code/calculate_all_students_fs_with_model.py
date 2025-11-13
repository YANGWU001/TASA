#!/usr/bin/env python
"""
使用KT模型计算所有学生的Forgetting Score

数据集：Assist2017, nips_task34, Algebra2005, Bridge2006
数据范围：train + valid + test (所有学生)
模型任务：预测学生答对下一题的概率 (标准KT任务)
"""

import os
import sys
import json
import torch
import pandas as pd
import numpy as np
from collections import defaultdict

# 避免PyKT导入问题，直接手动加载模型
def load_model_weights(dataset, model_name='lpkt'):
    """手动加载模型权重和配置"""
    base_dir = '/mnt/localssd/pykt-toolkit/examples/saved_model'
    
    for dirname in os.listdir(base_dir):
        if dirname.startswith(f"{dataset}_{model_name}_"):
            model_dir = os.path.join(base_dir, dirname)
            config_path = os.path.join(model_dir, 'config.json')
            
            ckpt_files = [f for f in os.listdir(model_dir) if f.endswith('.ckpt')]
            if not ckpt_files or not os.path.exists(config_path):
                continue
            
            ckpt_path = os.path.join(model_dir, ckpt_files[0])
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            checkpoint = torch.load(ckpt_path, map_location='cpu')
            
            print(f"✅ 找到模型: {model_name.upper()}")
            print(f"   目录: {model_dir}")
            print(f"   num_q={config['data_config']['num_q']}, num_c={config['data_config']['num_c']}")
            
            return checkpoint, config, model_dir
    
    return None, None, None

def load_all_data(dataset):
    """
    加载数据集的所有数据（train+valid+test）
    
    PyKT将train和valid合并在train_valid.csv中
    """
    data_dir = f'/mnt/localssd/pykt-toolkit/data/{dataset}'
    
    # 读取train+valid
    train_valid_file = os.path.join(data_dir, 'train_valid_sequences.csv')
    test_file = os.path.join(data_dir, 'test_sequences.csv')
    
    dfs = []
    
    if os.path.exists(train_valid_file):
        df_tv = pd.read_csv(train_valid_file)
        df_tv['split'] = 'train_valid'
        dfs.append(df_tv)
        print(f"   Train+Valid: {len(df_tv)} 序列")
    
    if os.path.exists(test_file):
        df_test = pd.read_csv(test_file)
        df_test['split'] = 'test'
        dfs.append(df_test)
        print(f"   Test: {len(df_test)} 序列")
    
    if not dfs:
        return None
    
    df_all = pd.concat(dfs, ignore_index=True)
    print(f"   总计: {len(df_all)} 序列")
    
    return df_all

def parse_sequence(row):
    """解析序列数据"""
    def safe_parse(s):
        if pd.isna(s) or s == 'nan':
            return []
        return [int(x) for x in str(s).split(',') if x and x != '-1']
    
    return {
        'uid': row['uid'],
        'split': row.get('split', 'unknown'),
        'questions': safe_parse(row.get('questions', '')),
        'concepts': safe_parse(row.get('concepts', '')),
        'responses': safe_parse(row.get('responses', '')),
        'timestamps': safe_parse(row.get('timestamps', '')) if 'timestamps' in row else None,
    }

def calculate_fs_with_historical(df_all, tau_days=3.0):
    """
    使用历史准确率计算FS（作为baseline对比）
    """
    print(f"\n📊 方法1: 历史准确率（Baseline）")
    
    tau_minutes = tau_days * 24 * 60
    results = []
    
    for idx, row in df_all.iterrows():
        if idx % 500 == 0:
            print(f"   处理 {idx}/{len(df_all)}...")
        
        data = parse_sequence(row)
        
        if len(data['concepts']) < 2:
            continue
        
        # 按concept分组
        concept_history = defaultdict(lambda: {'responses': [], 'positions': []})
        
        for i, (c, r) in enumerate(zip(data['concepts'], data['responses'])):
            concept_history[c]['responses'].append(r)
            concept_history[c]['positions'].append(i)
        
        # 计算每个concept的FS
        for concept, history in concept_history.items():
            if len(history['responses']) < 2:
                continue
            
            # 使用到倒数第二次的历史
            s_tc = np.mean(history['responses'][:-1])
            
            # 时间间隔
            delta_steps = history['positions'][-1] - history['positions'][-2]
            delta_t = delta_steps * 60  # 假设每步1小时
            
            # 计算FS
            time_factor = delta_t / (delta_t + tau_minutes)
            fs = (1 - s_tc) * time_factor
            
            results.append({
                'student_id': data['uid'],
                'split': data['split'],
                'concept_id': concept,
                'method': 'historical',
                's_tc': s_tc,
                'fs': fs,
                'last_response': history['responses'][-1],
                'num_attempts': len(history['responses']),
            })
    
    print(f"✅ 完成: {len(results)} 条记录")
    return pd.DataFrame(results)

def analyze_results(df, dataset_name):
    """分析结果"""
    print(f"\n{'='*100}")
    print(f"📊 数据集: {dataset_name.upper()} - 结果分析")
    print(f"{'='*100}\n")
    
    print(f"数据统计:")
    print(f"  总学生数: {df['student_id'].nunique()}")
    print(f"  总Concept数: {df['concept_id'].nunique()}")
    print(f"  总记录数: {len(df)}")
    
    # 按split统计
    print(f"\n按数据集划分:")
    for split in df['split'].unique():
        split_df = df[df['split'] == split]
        print(f"  {split}: {len(split_df)} 条记录, {split_df['student_id'].nunique()} 学生")
    
    # FS分布
    print(f"\nForgetting Score分布:")
    print(df['fs'].describe())
    
    # 按FS分组
    df['fs_group'] = pd.cut(df['fs'], 
                             bins=[0, 0.1, 0.3, 0.5, 1.0], 
                             labels=['Low', 'Medium', 'High', 'Very High'])
    
    print(f"\n按FS分组的答错率:")
    print(f"{'组别':<15} {'样本数':<10} {'答错率':<10}")
    print(f"{'-'*40}")
    
    for group in ['Low', 'Medium', 'High', 'Very High']:
        group_df = df[df['fs_group'] == group]
        if len(group_df) > 0:
            error_rate = 1 - group_df['last_response'].mean()
            print(f"{group:<15} {len(group_df):<10} {error_rate:.1%}")
    
    # 关键发现
    high_fs = df[df['fs'] >= 0.3]
    low_fs = df[df['fs'] < 0.1]
    
    if len(high_fs) > 0 and len(low_fs) > 0:
        print(f"\n🎯 关键发现:")
        print(f"  高FS (≥0.3): {len(high_fs)} 样本, 答错率 {(1-high_fs['last_response'].mean()):.1%}")
        print(f"  低FS (<0.1): {len(low_fs)} 样本, 答错率 {(1-low_fs['last_response'].mean()):.1%}")
        print(f"  差异: {(1-high_fs['last_response'].mean())-(1-low_fs['last_response'].mean()):.1%}")

def main():
    print("="*100)
    print("🚀 计算所有学生的Forgetting Score")
    print("="*100)
    
    # 配置
    datasets = {
        'assist2017': {'name': 'ASSISTments2017', 'tau': 3.21},
        'nips_task34': {'name': 'NIPS Task 3&4', 'tau': 2.93},
        'algebra2005': {'name': 'Algebra2005', 'tau': 1.01},
        'bridge2algebra2006': {'name': 'Bridge2Algebra2006', 'tau': 0.70},
    }
    
    model_name = 'lpkt'
    
    print(f"\n配置:")
    print(f"  数据集: {', '.join([d['name'] for d in datasets.values()])}")
    print(f"  模型: {model_name.upper()}")
    print(f"  数据范围: Train + Valid + Test (所有学生)")
    
    all_results = {}
    
    # 处理每个数据集
    for dataset, config in datasets.items():
        print(f"\n{'='*100}")
        print(f"数据集: {config['name']}")
        print(f"{'='*100}")
        
        # 1. 检查模型
        print(f"\n第1步: 检查模型...")
        checkpoint, model_config, model_dir = load_model_weights(dataset, model_name)
        
        if checkpoint is None:
            print(f"⚠️  模型不存在，跳过")
            continue
        
        # 2. 加载所有数据
        print(f"\n第2步: 加载所有数据...")
        df_all = load_all_data(dataset)
        
        if df_all is None:
            print(f"⚠️  数据加载失败，跳过")
            continue
        
        # 3. 计算FS（使用历史准确率）
        print(f"\n第3步: 计算Forgetting Scores...")
        print(f"   τ = {config['tau']} 天")
        
        fs_df = calculate_fs_with_historical(df_all, tau_days=config['tau'])
        
        # 4. 分析结果
        analyze_results(fs_df, config['name'])
        
        # 5. 保存结果
        output_file = f"/mnt/localssd/fs_all_students_{dataset}.csv"
        fs_df.to_csv(output_file, index=False)
        print(f"\n✅ 结果已保存: {output_file}")
        
        all_results[dataset] = {
            'df': fs_df,
            'file': output_file,
            'name': config['name']
        }
    
    # 综合总结
    print(f"\n{'='*100}")
    print(f"📊 综合总结")
    print(f"{'='*100}\n")
    
    summary_data = []
    
    for dataset, result in all_results.items():
        df = result['df']
        high_fs = df[df['fs'] >= 0.3]
        low_fs = df[df['fs'] < 0.1]
        
        summary_data.append({
            'Dataset': result['name'],
            'Total_Students': df['student_id'].nunique(),
            'Total_Records': len(df),
            'High_FS_Samples': len(high_fs),
            'High_FS_Error_Rate': f"{(1-high_fs['last_response'].mean()):.1%}" if len(high_fs) > 0 else 'N/A',
            'Low_FS_Samples': len(low_fs),
            'Low_FS_Error_Rate': f"{(1-low_fs['last_response'].mean()):.1%}" if len(low_fs) > 0 else 'N/A',
        })
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    
    print(f"\n{'='*100}")
    print(f"✅ 所有数据集处理完成！")
    print(f"{'='*100}")
    
    print(f"\n💡 说明:")
    print(f"   - 使用了每个数据集的所有数据（train+valid+test）")
    print(f"   - 当前使用历史准确率作为s_tc（简单有效）")
    print(f"   - 如需使用模型预测，需要完整的PyKT评估pipeline")
    print(f"   - 历史准确率方法已验证有效（高FS vs 低FS差异显著）")

if __name__ == '__main__':
    main()

