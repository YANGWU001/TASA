#!/usr/bin/env python
"""
使用训练好的KT模型批量预测并计算Forgetting Score

思路：
1. 使用PyKT的DataLoader加载test set（已经处理好ID映射）
2. 模型对整个test set进行预测
3. 提取每个学生每个concept的预测概率
4. 计算forgetting scores
"""

import os
import sys
import json
import torch
import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime

# 添加PyKT路径
sys.path.insert(0, '/mnt/localssd/pykt-toolkit')
from pykt.models.init_model import load_model
from pykt.datasets.lpkt_dataloader import KTQueDataset
from torch.utils.data import DataLoader

def load_trained_model(dataset, model_name='lpkt', device='cpu'):
    """加载训练好的模型"""
    base_dir = '/mnt/localssd/pykt-toolkit/examples/saved_model'
    
    # 查找模型目录
    for dirname in os.listdir(base_dir):
        if dirname.startswith(f"{dataset}_{model_name}_"):
            model_dir = os.path.join(base_dir, dirname)
            config_path = os.path.join(model_dir, 'config.json')
            
            if not os.path.exists(config_path):
                continue
            
            # 读取配置
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # 使用PyKT的标准加载方式
            model = load_model(
                model_name=model_name,
                model_config=config['model_config'],
                data_config=config['data_config'],
                emb_type=config.get('params', {}).get('emb_type', 'qid'),
                ckpt_path=model_dir
            )
            
            model = model.to(device)
            model.eval()
            
            print(f"✅ 成功加载模型: {model_name.upper()} on {dataset.upper()}")
            print(f"   num_q={config['data_config']['num_q']}, num_c={config['data_config']['num_c']}")
            
            return model, config
    
    print(f"❌ 未找到模型: {dataset}_{model_name}")
    return None, None

def create_dataloader(dataset, config, batch_size=64):
    """创建DataLoader（使用PyKT的标准方式）"""
    data_config = config['data_config']
    
    # 使用test set
    test_file = os.path.join(data_config['dpath'], 'test_sequences.csv')
    
    if not os.path.exists(test_file):
        print(f"⚠️  测试文件不存在: {test_file}")
        return None
    
    print(f"📂 加载数据: {test_file}")
    
    # 使用PyKT的Dataset
    test_dataset = KTQueDataset(
        test_file,
        input_type=data_config.get('input_type', ['questions']),
        folds=[-1],  # test set
        qtest=False,
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0
    )
    
    print(f"✅ DataLoader创建成功，batch数: {len(test_loader)}")
    
    return test_loader

def predict_all_students(model, model_name, test_loader, device='cpu'):
    """
    对所有学生进行预测
    
    返回：每个学生每个时间步的预测概率
    """
    print(f"\n🔮 开始预测...")
    
    all_predictions = []
    
    model.eval()
    with torch.no_grad():
        for batch_idx, dcur in enumerate(test_loader):
            if batch_idx % 10 == 0:
                print(f"   处理批次 {batch_idx+1}/{len(test_loader)}...")
            
            # 将数据移到设备
            for key in dcur:
                if isinstance(dcur[key], torch.Tensor):
                    dcur[key] = dcur[key].to(device)
            
            # 根据模型类型调用forward
            try:
                if model_name == 'lpkt':
                    # LPKT的输入格式
                    q = dcur["qseqs"]
                    c = dcur["cseqs"]
                    r = dcur["rseqs"]
                    qshft = dcur["shft_qseqs"]
                    cshft = dcur["shft_cseqs"]
                    rshft = dcur["shft_rseqs"]
                    
                    cq = torch.cat([q[:, 0:1], qshft], dim=1)
                    cr = torch.cat([r[:, 0:1], rshft], dim=1)
                    cit = torch.cat([dcur["itseqs"][:, 0:1], dcur["shft_itseqs"]], dim=1)
                    
                    y = model(cq.long(), cr.long(), cit.long())
                    
                elif model_name == 'dkt':
                    # DKT的输入格式
                    q = dcur["qseqs"]
                    c = dcur["cseqs"]
                    r = dcur["rseqs"]
                    qshft = dcur["shft_qseqs"]
                    cshft = dcur["shft_cseqs"]
                    rshft = dcur["shft_rseqs"]
                    
                    cq = torch.cat([q[:, 0:1], qshft], dim=1)
                    cc = torch.cat([c[:, 0:1], cshft], dim=1)
                    cr = torch.cat([r[:, 0:1], rshft], dim=1)
                    
                    y = model(cc.long(), cr.long(), cq.long())
                    
                elif model_name == 'akt':
                    # AKT的输入格式
                    q = dcur["qseqs"]
                    c = dcur["cseqs"]
                    r = dcur["rseqs"]
                    qshft = dcur["shft_qseqs"]
                    cshft = dcur["shft_cseqs"]
                    rshft = dcur["shft_rseqs"]
                    
                    cq = torch.cat([q[:, 0:1], qshft], dim=1)
                    cc = torch.cat([c[:, 0:1], cshft], dim=1)
                    cr = torch.cat([r[:, 0:1], rshft], dim=1)
                    
                    y, _ = model(cc.long(), cr.long(), cq.long())
                    
                elif model_name == 'simplekt':
                    # simpleKT的输入格式
                    y = model(dcur)
                    
                else:
                    print(f"⚠️  不支持的模型: {model_name}")
                    continue
                
                # 跳过第一个预测（shift的结果）
                y = y[:, 1:]
                
                # 转换为概率
                probs = torch.sigmoid(y)
                
                # 保存结果（移到CPU）
                batch_result = {
                    'probs': probs.cpu(),
                    'concepts': dcur["cseqs"].cpu(),
                    'responses': dcur["rseqs"].cpu(),
                    'questions': dcur["qseqs"].cpu(),
                    'masks': dcur["masks"].cpu(),
                    'uids': dcur.get("uid", None),
                }
                
                all_predictions.append(batch_result)
                
            except Exception as e:
                print(f"   ⚠️  批次 {batch_idx} 预测失败: {e}")
                continue
    
    print(f"✅ 预测完成！")
    
    return all_predictions

def extract_concept_predictions(all_predictions):
    """
    从批量预测结果中提取每个学生每个concept的预测
    
    返回：{student_id: {concept_id: [predictions]}}
    """
    print(f"\n📊 提取concept级别的预测...")
    
    student_concept_preds = defaultdict(lambda: defaultdict(list))
    
    total_samples = 0
    for batch_result in all_predictions:
        probs = batch_result['probs']
        concepts = batch_result['concepts']
        responses = batch_result['responses']
        masks = batch_result['masks']
        
        batch_size, seq_len = probs.shape
        
        for i in range(batch_size):
            student_id = total_samples + i
            
            for j in range(seq_len):
                if masks[i, j] == 0:  # padding
                    continue
                
                concept = int(concepts[i, j])
                pred_prob = float(probs[i, j])
                response = int(responses[i, j])
                
                student_concept_preds[student_id][concept].append({
                    'pred_prob': pred_prob,
                    'response': response,
                    'position': j,
                })
        
        total_samples += batch_size
    
    print(f"✅ 提取完成: {len(student_concept_preds)} 个学生")
    
    return student_concept_preds

def calculate_forgetting_scores(student_concept_preds, tau_days=3.0):
    """
    计算每个学生每个concept的forgetting score
    
    使用最后一次的预测概率作为s_t,c
    """
    print(f"\n📈 计算Forgetting Scores (τ={tau_days} 天)...")
    
    tau_minutes = tau_days * 24 * 60
    
    results = []
    
    for student_id, concepts in student_concept_preds.items():
        for concept_id, predictions in concepts.items():
            if len(predictions) < 2:
                continue
            
            # 使用倒数第二次的预测作为s_t,c（预测最后一次的表现）
            s_tc = predictions[-2]['pred_prob']
            
            # 使用位置差作为时间差的代理
            # 实际应用中应该使用真实时间戳
            delta_steps = predictions[-1]['position'] - predictions[-2]['position']
            
            # 假设每步平均间隔1天（可以根据实际数据调整）
            delta_t = delta_steps * 24 * 60  # 转换为分钟
            
            # 计算FS
            time_factor = delta_t / (delta_t + tau_minutes)
            fs = (1 - s_tc) * time_factor
            
            # 记录结果
            results.append({
                'student_id': student_id,
                'concept_id': concept_id,
                'num_attempts': len(predictions),
                's_tc_model': s_tc,
                's_tc_historical': np.mean([p['response'] for p in predictions[:-1]]),
                'delta_steps': delta_steps,
                'fs_model': fs,
                'last_response': predictions[-1]['response'],
                'predicted_correct': 1 if s_tc >= 0.5 else 0,
            })
    
    print(f"✅ 计算完成: {len(results)} 个 (学生, concept) 对")
    
    return pd.DataFrame(results)

def analyze_results(df):
    """分析结果"""
    print(f"\n{'='*100}")
    print(f"📊 结果分析")
    print(f"{'='*100}\n")
    
    print(f"基本统计:")
    print(f"  学生数: {df['student_id'].nunique()}")
    print(f"  Concept数: {df['concept_id'].nunique()}")
    print(f"  总记录数: {len(df)}")
    
    print(f"\n模型预测 vs 历史准确率:")
    print(f"  模型s_tc平均: {df['s_tc_model'].mean():.4f}")
    print(f"  历史s_tc平均: {df['s_tc_historical'].mean():.4f}")
    print(f"  相关系数: {df['s_tc_model'].corr(df['s_tc_historical']):.4f}")
    
    print(f"\nForgetting Score分布:")
    print(df['fs_model'].describe())
    
    # 按FS分组分析预测准确性
    df['fs_group'] = pd.cut(df['fs_model'], bins=[0, 0.1, 0.3, 0.5, 1.0], 
                             labels=['Low', 'Medium', 'High', 'Very High'])
    
    print(f"\n按Forgetting Score分组的答错率:")
    for group in ['Low', 'Medium', 'High', 'Very High']:
        group_df = df[df['fs_group'] == group]
        if len(group_df) > 0:
            error_rate = 1 - group_df['last_response'].mean()
            print(f"  {group}: {error_rate:.1%} ({len(group_df)} samples)")
    
    # 模型预测准确性
    print(f"\n模型预测准确性:")
    accuracy = (df['predicted_correct'] == df['last_response']).mean()
    print(f"  准确率: {accuracy:.1%}")
    
    # 对比高FS vs 低FS
    high_fs = df[df['fs_model'] >= 0.3]
    low_fs = df[df['fs_model'] < 0.1]
    
    if len(high_fs) > 0 and len(low_fs) > 0:
        print(f"\n高FS (≥0.3) vs 低FS (<0.1):")
        print(f"  高FS答错率: {(1 - high_fs['last_response'].mean()):.1%}")
        print(f"  低FS答错率: {(1 - low_fs['last_response'].mean()):.1%}")
        print(f"  差异: {(1 - high_fs['last_response'].mean()) - (1 - low_fs['last_response'].mean()):.1%}")

def main():
    print("="*100)
    print("🚀 使用KT模型批量预测并计算Forgetting Score")
    print("="*100)
    
    # 配置
    dataset = 'assist2017'
    model_name = 'lpkt'
    device = 'cpu'
    tau_days = 3.21  # 从之前的分析得出
    
    print(f"\n配置:")
    print(f"  数据集: {dataset.upper()}")
    print(f"  模型: {model_name.upper()}")
    print(f"  τ: {tau_days} 天")
    
    # 1. 加载模型
    print(f"\n{'='*100}")
    print(f"第1步: 加载模型")
    print(f"{'='*100}")
    
    model, config = load_trained_model(dataset, model_name, device)
    
    if model is None:
        print("❌ 模型加载失败，退出")
        return
    
    # 2. 创建DataLoader
    print(f"\n{'='*100}")
    print(f"第2步: 创建DataLoader")
    print(f"{'='*100}")
    
    test_loader = create_dataloader(dataset, config, batch_size=64)
    
    if test_loader is None:
        print("❌ DataLoader创建失败，退出")
        return
    
    # 3. 批量预测
    print(f"\n{'='*100}")
    print(f"第3步: 批量预测")
    print(f"{'='*100}")
    
    all_predictions = predict_all_students(model, model_name, test_loader, device)
    
    # 4. 提取concept级别的预测
    print(f"\n{'='*100}")
    print(f"第4步: 提取concept预测")
    print(f"{'='*100}")
    
    student_concept_preds = extract_concept_predictions(all_predictions)
    
    # 5. 计算Forgetting Scores
    print(f"\n{'='*100}")
    print(f"第5步: 计算Forgetting Scores")
    print(f"{'='*100}")
    
    results_df = calculate_forgetting_scores(student_concept_preds, tau_days)
    
    # 6. 分析结果
    analyze_results(results_df)
    
    # 7. 保存结果
    output_file = f'/mnt/localssd/fs_results_{dataset}_{model_name}.csv'
    results_df.to_csv(output_file, index=False)
    print(f"\n✅ 结果已保存: {output_file}")
    
    print(f"\n{'='*100}")
    print(f"✅ 完成！")
    print(f"{'='*100}")

if __name__ == '__main__':
    main()

