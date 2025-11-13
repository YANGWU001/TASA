#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""简单测试"""

# 1. 测试LLM
print("测试LLM...")
from openai import OpenAI

ENDPOINT = "http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000"
KEY = "sk-g-wO3D7N2V-VvcfhfqG9ww"
MODEL = "gpt-4o"

try:
    client = OpenAI(
        api_key="Bearer " + KEY,
        base_url=ENDPOINT,
    )
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello"}
        ],
        temperature=0.7
    )
    
    content = response.choices[0].message.content
    print(f"✅ LLM响应: {content[:100]}")
    
except Exception as e:
    print(f"❌ LLM失败: {e}")

# 2. 测试BGE-M3（单进程）
print("\n测试BGE-M3...")
try:
    from FlagEmbedding import BGEM3FlagModel
    
    # 使用devices参数避免多进程
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True, devices='cuda:0')
    
    texts = ["Hello world"]
    # 设置batch_size=1避免多进程
    result = model.encode(texts, batch_size=1, max_length=128, return_dense=True, return_sparse=False, return_colbert_vecs=False)
    embeddings = result['dense_vecs']
    
    print(f"✅ BGE-M3成功:")
    print(f"  Shape: {embeddings.shape}")
    print(f"  前5维: {embeddings[0][:5]}")
    
except Exception as e:
    print(f"❌ BGE-M3失败: {e}")
    import traceback
    traceback.print_exc()

