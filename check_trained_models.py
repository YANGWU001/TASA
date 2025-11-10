#!/usr/bin/env python
"""
检查训练好的KT模型并展示如何使用
不需要导入PyKT，只检查文件和读取结果
"""

import os
import json
import pandas as pd

def find_all_trained_models():
    """查找所有训练好的模型"""
    base_dir = '/mnt/localssd/pykt-toolkit/examples/saved_model'
    
    if not os.path.exists(base_dir):
        print(f"❌ 模型目录不存在: {base_dir}")
        return []
    
    models = []
    
    for dirname in os.listdir(base_dir):
        if '_saved_model' in dirname:
            model_dir = os.path.join(base_dir, dirname)
            
            # 解析目录名
            parts = dirname.split('_')
            if len(parts) >= 2:
                dataset = parts[0]
                model_name = parts[1]
                
                # 检查checkpoint
                ckpt_files = [f for f in os.listdir(model_dir) if f.endswith('.ckpt')]
                config_exists = os.path.exists(os.path.join(model_dir, 'config.json'))
                
                if ckpt_files and config_exists:
                    # 读取配置
                    with open(os.path.join(model_dir, 'config.json'), 'r') as f:
                        config = json.load(f)
                    
                    data_config = config.get('data_config', {})
                    
                    models.append({
                        'dataset': dataset,
                        'model': model_name,
                        'dir': model_dir,
                        'checkpoint': ckpt_files[0],
                        'num_q': data_config.get('num_q', 'N/A'),
                        'num_c': data_config.get('num_c', 'N/A'),
                    })
    
    return models

def check_training_logs(model_dir):
    """检查训练日志"""
    log_files = ['train.log', 'training.log', 'output.log']
    
    for log_file in log_files:
        log_path = os.path.join(model_dir, log_file)
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = f.readlines()
                # 找最后几行（通常包含最终结果）
                return ''.join(lines[-20:])
    
    return None

def main():
    print("="*100)
    print("🔍 检查训练好的KT模型")
    print("="*100)
    
    models = find_all_trained_models()
    
    if not models:
        print("\n❌ 未找到训练好的模型")
        return
    
    print(f"\n✅ 找到 {len(models)} 个训练好的模型:\n")
    
    # 按数据集分组
    datasets = {}
    for m in models:
        if m['dataset'] not in datasets:
            datasets[m['dataset']] = []
        datasets[m['dataset']].append(m)
    
    # 显示每个数据集的模型
    for dataset, dataset_models in sorted(datasets.items()):
        print(f"\n{'='*100}")
        print(f"📚 数据集: {dataset.upper()}")
        print(f"{'='*100}")
        
        for m in dataset_models:
            print(f"\n  🤖 模型: {m['model'].upper()}")
            print(f"     目录: {os.path.basename(m['dir'])}")
            print(f"     Checkpoint: {m['checkpoint']}")
            print(f"     num_q={m['num_q']}, num_c={m['num_c']}")
            
            # 检查是否有nohup日志
            nohup_files = []
            parent_dir = '/mnt/localssd/pykt-toolkit/examples'
            for f in os.listdir(parent_dir):
                if 'nohup' in f and dataset in f and m['model'] in f:
                    nohup_files.append(os.path.join(parent_dir, f))
            
            if nohup_files:
                print(f"     训练日志: {os.path.basename(nohup_files[0])}")
                
                # 读取最后几行看是否有AUC/ACC
                try:
                    with open(nohup_files[0], 'r') as f:
                        lines = f.readlines()
                        for line in lines[-30:]:
                            if 'auc' in line.lower() or 'acc' in line.lower():
                                print(f"     {line.strip()}")
                except:
                    pass
    
    print(f"\n{'='*100}")
    print(f"💡 如何使用这些模型:")
    print(f"{'='*100}\n")
    
    print(f"1️⃣  查看训练日志和性能:")
    print(f"   cd /mnt/localssd/pykt-toolkit/examples")
    print(f"   tail -100 nohup_assist2017_lpkt_*.out | grep -i 'auc\\|acc'\n")
    
    print(f"2️⃣  使用模型进行评估（标准方式）:")
    print(f"   cd /mnt/localssd/pykt-toolkit/examples")
    print(f"   python wandb_lpkt_train.py \\")
    print(f"       --dataset_name=assist2017 \\")
    print(f"       --fold=0 \\")
    print(f"       --use_wandb=0\n")
    
    print(f"3️⃣  模型已经可以用于:")
    print(f"   ✅ Test set性能评估（AUC/ACC）")
    print(f"   ✅ 预测学生下一题表现")
    print(f"   ✅ 模型对比研究")
    print(f"   ✅ Forgetting Score计算（但历史准确率更简单）\n")
    
    print(f"4️⃣  对于Forgetting Score:")
    print(f"   ✅ 推荐：继续使用历史准确率（已验证有效，58.3% vs 30%）")
    print(f"   ⚠️  模型预测：需要解决Question ID映射问题\n")
    
    print(f"{'='*100}")
    print(f"📖 详细文档:")
    print(f"   /mnt/localssd/HOW_TO_USE_TRAINED_MODELS.md")
    print(f"{'='*100}")

if __name__ == '__main__':
    main()

