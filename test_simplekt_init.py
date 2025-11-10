#!/usr/bin/env python
"""测试SimpleKT模型初始化"""

import json
import copy
import torch
import sys
sys.path.insert(0, '/mnt/localssd/pykt-toolkit')

from pykt.models import init_model, load_model

# 加载配置
config_path = '/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0/config.json'

with open(config_path) as f:
    config = json.load(f)

print("="*80)
print("测试 SimpleKT 模型初始化")
print("="*80)

# 获取配置
model_config = copy.deepcopy(config["model_config"])
trained_params = config["params"]
model_name_actual = trained_params["model_name"]
dataset_name = trained_params["dataset_name"]
emb_type = trained_params["emb_type"]

print(f"\n模型名称: {model_name_actual}")
print(f"数据集: {dataset_name}")
print(f"Emb类型: {emb_type}")

# 加载data_config
with open("/mnt/localssd/pykt-toolkit/configs/data_config.json") as f:
    curconfig = copy.deepcopy(json.load(f))
    data_config = curconfig[dataset_name]
    data_config["dataset_name"] = dataset_name

print(f"\nData Config:")
print(f"  num_q: {data_config['num_q']}")
print(f"  num_c: {data_config['num_c']}")

# 移除训练相关参数
print(f"\n原始 Model Config 参数: {list(model_config.keys())}")

training_params = ['learning_rate', 'use_wandb', 'add_uuid', 'dataset_name', 'model_name', 'save_dir', 'seed', 'fold', 'emb_type', 'emb_path']
for param in training_params:
    if param in model_config:
        print(f"  移除: {param} = {model_config[param]}")
        model_config.pop(param)

print(f"\n清理后 Model Config 参数: {list(model_config.keys())}")
print(f"清理后 Model Config:")
for k, v in model_config.items():
    print(f"  {k}: {v}")

# 测试初始化
print(f"\n{'='*80}")
print("尝试初始化模型...")
print(f"{'='*80}")

try:
    model = init_model(model_name_actual, model_config, data_config, emb_type)
    
    if model is None:
        print("❌ 模型初始化失败: init_model 返回 None")
        print("   这意味着模型名称不匹配或参数有问题")
    else:
        print(f"✅ 模型初始化成功!")
        print(f"   模型类型: {type(model)}")
        print(f"   模型名称: {model.model_name if hasattr(model, 'model_name') else 'N/A'}")
        
        # 测试加载checkpoint
        print(f"\n{'='*80}")
        print("尝试加载checkpoint...")
        print(f"{'='*80}")
        
        save_dir = '/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0'
        
        try:
            loaded_model = load_model(model_name_actual, model_config, data_config, emb_type, save_dir)
            print(f"✅ Checkpoint加载成功!")
        except Exception as e:
            print(f"❌ Checkpoint加载失败: {e}")
            import traceback
            traceback.print_exc()
        
except Exception as e:
    print(f"❌ 模型初始化异常: {e}")
    import traceback
    traceback.print_exc()

