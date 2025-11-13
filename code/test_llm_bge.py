#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试LLM和BGE模型
"""

import json
from openai import OpenAI

# LLM配置
ENDPOINT = "http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000"
KEY = "sk-g-wO3D7N2V-VvcfhfqG9ww"
MODEL = "gpt-4o"

print("1. 测试LLM连接...")
try:
    client = OpenAI(
        api_key="Bearer " + KEY,
        base_url=ENDPOINT,
    )
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'hello' in JSON format with a 'message' field."}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    print(f"✅ LLM测试成功: {result}")

except Exception as e:
    print(f"❌ LLM测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n2. 测试BGE-M3...")
try:
    from FlagEmbedding import BGEM3FlagModel
    
    print("  加载模型...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    
    print("  生成embeddings...")
    texts = ["Hello world", "Test embedding"]
    embeddings = model.encode(texts, batch_size=2, max_length=512)['dense_vecs']
    
    print(f"✅ BGE-M3测试成功:")
    print(f"  - 输入文本数: {len(texts)}")
    print(f"  - Embedding维度: {embeddings.shape}")
    print(f"  - 第一个embedding前5维: {embeddings[0][:5]}")

except Exception as e:
    print(f"❌ BGE-M3测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 所有测试完成")

