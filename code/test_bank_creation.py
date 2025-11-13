#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试bank创建流程
"""

import pandas as pd
import os

# 检查数据文件
datasets = {
    'assist2017': '/mnt/localssd/pykt-toolkit/data/assist2017/train_valid_sequences.csv',
    'ednet': '/mnt/localssd/pykt-toolkit/data/ednet/train_valid_sequences.csv',
    'algebra2005': '/mnt/localssd/pykt-toolkit/data/algebra2005/train_valid_sequences.csv',
    'bridge2006': '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/train_valid_sequences.csv',
}

print("检查数据文件...")
for name, path in datasets.items():
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"✅ {name}: {len(df)} 学生, 列: {list(df.columns)}")
    else:
        print(f"❌ {name}: 文件不存在 - {path}")

print("\n检查bank文件夹...")
if os.path.exists('/mnt/localssd/bank'):
    print("✅ bank文件夹已创建")
    os.system("tree -L 3 /mnt/localssd/bank")
else:
    print("❌ bank文件夹不存在")

print("\n检查Python依赖...")
try:
    from openai import OpenAI
    print("✅ openai")
except:
    print("❌ openai")

try:
    from FlagEmbedding import BGEM3FlagModel
    print("✅ FlagEmbedding")
except:
    print("❌ FlagEmbedding - 需要安装")

try:
    from tqdm import tqdm
    print("✅ tqdm")
except:
    print("❌ tqdm")

