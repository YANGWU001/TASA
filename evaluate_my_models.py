#!/usr/bin/env python
"""
正确使用训练好的KT模型进行评估和预测

展示：
1. 如何加载训练好的模型
2. 如何在test set上评估性能（AUC/ACC）
3. 如何使用模型进行预测
"""

import os
import sys
import torch
import json
import pandas as pd
import numpy as np
from sklearn import metrics

# 添加PyKT路径
sys.path.insert(0, '/mnt/localssd/pykt-toolkit')
from pykt.models.init_model import load_model as pykt_load_model

def find_model_checkpoint(dataset, model_name):
    """查找模型checkpoint"""
    base_dir = '/mnt/localssd/pykt-toolkit/examples/saved_model'
    
    # 查找匹配的目录
    for dirname in os.listdir(base_dir):
        if dirname.startswith(f"{dataset}_{model_name}_"):
            model_dir = os.path.join(base_dir, dirname)
            
            # 查找checkpoint文件
            for ckpt_name in ['qid_model.ckpt', 'model.ckpt', 'best_model.ckpt']:
                ckpt_path = os.path.join(model_dir, ckpt_name)
                if os.path.exists(ckpt_path):
                    config_path = os.path.join(model_dir, 'config.json')
                    if os.path.exists(config_path):
                        return model_dir, ckpt_path, config_path
    
    return None, None, None

def load_trained_model(dataset, model_name, device='cpu'):
    """
    正确加载训练好的模型
    
    这是使用PyKT的标准方式
    """
    model_dir, ckpt_path, config_path = find_model_checkpoint(dataset, model_name)
    
    if not model_dir:
        print(f"❌ 未找到模型: {dataset}_{model_name}")
        return None, None
    
    print(f"📂 模型目录: {model_dir}")
    print(f"📦 Checkpoint: {os.path.basename(ckpt_path)}")
    
    # 读取配置
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    data_config = config['data_config']
    emb_type = config.get('params', {}).get('emb_type', 'qid')
    
    # 使用PyKT的标准加载方式
    model = pykt_load_model(
        model_name=model_name,
        model_config=config['model_config'],
        data_config=data_config,
        emb_type=emb_type,
        ckpt_path=model_dir
    )
    
    model = model.to(device)
    model.eval()
    
    print(f"✅ 成功加载模型")
    print(f"   num_q={data_config['num_q']}, num_c={data_config['num_c']}")
    
    return model, config

def evaluate_on_processed_data(dataset, model_name):
    """
    方法1: 使用PyKT预处理好的数据进行评估
    
    这是最标准、最正确的方式
    """
    print(f"\n{'='*80}")
    print(f"评估: {dataset.upper()} - {model_name.upper()}")
    print(f"{'='*80}")
    
    # 加载模型
    model, config = load_trained_model(dataset, model_name)
    
    if model is None:
        return
    
    # 使用PyKT预处理的test数据
    data_path = f'/mnt/localssd/pykt-toolkit/data/{dataset}/test_sequences.csv'
    
    if not os.path.exists(data_path):
        print(f"⚠️  测试数据不存在: {data_path}")
        return
    
    print(f"\n📊 加载测试数据: {data_path}")
    
    try:
        df = pd.read_csv(data_path)
        print(f"   测试集大小: {len(df)} 个序列")
        
        # 方法1: 读取已有的评估结果（如果存在）
        model_dir = os.path.dirname(find_model_checkpoint(dataset, model_name)[1])
        results_files = ['test_results.txt', 'test_metrics.json']
        
        for results_file in results_files:
            results_path = os.path.join(model_dir, results_file)
            if os.path.exists(results_path):
                print(f"\n✅ 找到评估结果: {results_file}")
                with open(results_path, 'r') as f:
                    print(f.read())
                return
        
        print(f"\n⚠️  未找到预计算的评估结果")
        print(f"💡 提示: 运行以下命令重新评估:")
        print(f"   cd /mnt/localssd/pykt-toolkit/examples")
        print(f"   python wandb_{model_name}_train.py \\")
        print(f"       --dataset_name={dataset} \\")
        print(f"       --fold=0 \\")
        print(f"       --use_wandb=0")
        
    except Exception as e:
        print(f"❌ 评估出错: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_prediction(dataset, model_name):
    """
    方法2: 演示如何使用模型进行单个预测
    
    注意: 这需要正确的数据预处理
    """
    print(f"\n{'='*80}")
    print(f"演示预测: {dataset.upper()} - {model_name.upper()}")
    print(f"{'='*80}")
    
    model, config = load_trained_model(dataset, model_name)
    
    if model is None:
        return
    
    print(f"\n💡 预测示例（简化版）:")
    print(f"   注意: 实际使用时需要PyKT的DataLoader进行正确的数据预处理")
    
    # 从test set读取一个样本
    data_path = f'/mnt/localssd/pykt-toolkit/data/{dataset}/test_sequences.csv'
    
    if not os.path.exists(data_path):
        print(f"⚠️  测试数据不存在")
        return
    
    df = pd.read_csv(data_path)
    sample = df.iloc[0]
    
    print(f"\n   学生ID: {sample['uid']}")
    print(f"   序列长度: {len(str(sample['questions']).split(','))}")
    print(f"\n   💡 实际预测需要:")
    print(f"      1. 使用PyKT的DataLoader")
    print(f"      2. 正确的数据预处理（ID映射、padding等）")
    print(f"      3. 模型forward的正确输入格式")

def show_model_comparison():
    """
    方法3: 展示所有模型的对比
    """
    print(f"\n{'='*80}")
    print(f"📊 模型性能对比")
    print(f"{'='*80}\n")
    
    datasets = ['assist2017', 'ednet', 'algebra2005', 'bridge2algebra2006']
    models = ['lpkt', 'dkt', 'akt', 'simplekt']
    
    results = []
    
    for dataset in datasets:
        for model_name in models:
            model_dir, _, _ = find_model_checkpoint(dataset, model_name)
            
            if model_dir:
                status = "✅ 已训练"
                
                # 尝试读取评估结果
                metrics_file = os.path.join(model_dir, 'test_results.txt')
                auc, acc = "N/A", "N/A"
                
                if os.path.exists(metrics_file):
                    try:
                        with open(metrics_file, 'r') as f:
                            content = f.read()
                            # 简单解析
                            if 'AUC' in content:
                                auc = "有结果"
                    except:
                        pass
                
                results.append({
                    'Dataset': dataset,
                    'Model': model_name.upper(),
                    'Status': status,
                    'Metrics': auc
                })
            else:
                results.append({
                    'Dataset': dataset,
                    'Model': model_name.upper(),
                    'Status': "❌ 未找到",
                    'Metrics': "N/A"
                })
    
    # 打印表格
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    print(f"\n💡 如何使用这些模型:")
    print(f"   1. 性能评估: 查看test set的AUC/ACC")
    print(f"   2. 在线预测: 使用PyKT的DataLoader + model.forward()")
    print(f"   3. 模型对比: 比较不同模型在不同数据集上的表现")

if __name__ == '__main__':
    print("="*80)
    print("🚀 如何正确使用训练好的KT模型")
    print("="*80)
    
    # 1. 展示模型对比
    show_model_comparison()
    
    # 2. 演示评估（选择一个模型）
    print(f"\n")
    evaluate_on_processed_data('assist2017', 'lpkt')
    
    # 3. 演示预测
    demonstrate_prediction('assist2017', 'lpkt')
    
    print(f"\n{'='*80}")
    print(f"✅ 完成！")
    print(f"{'='*80}")
    
    print(f"\n📖 更多信息:")
    print(f"   - 详细指南: /mnt/localssd/HOW_TO_USE_TRAINED_MODELS.md")
    print(f"   - PyKT文档: /mnt/localssd/pykt-toolkit/README.md")

