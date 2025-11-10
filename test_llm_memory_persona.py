#!/usr/bin/env python
"""测试LLM生成persona和memory，诊断为什么会返回空响应"""

import json
from openai import OpenAI

# LLM配置
ENDPOINT = 'http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000'
KEY = 'sk-g-wO3D7N2V-VvcfhfqG9ww'
MODEL = 'gpt-4o'

client = OpenAI(api_key='Bearer ' + KEY, base_url=ENDPOINT)

print("=" * 80)
print("测试1: Persona生成（不使用JSON格式）")
print("=" * 80)

system_prompt_persona = """You are an educational data analyst. Summarize student proficiency for each concept based on their historical performance."""

user_prompt_persona = """Student 1188 (assist2017):

addition-subtraction-concepts: 15/20 (75%)
area-perimeter-volume: 8/12 (67%)
geometry-basics: 10/15 (67%)

For each concept above, provide: 1) Overall mastery (excellent/good/struggling), 2) One insight. Format: 'Concept name: [2 sentences]'"""

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt_persona},
            {"role": "user", "content": user_prompt_persona}
        ],
        temperature=1.0,
        max_tokens=800
    )
    
    content = response.choices[0].message.content
    print(f"✅ 成功获取响应")
    print(f"响应长度: {len(content) if content else 0} 字符")
    print(f"响应内容:\n{content}\n")
    
except Exception as e:
    print(f"❌ 错误: {e}\n")

print("=" * 80)
print("测试2: Memory生成（使用JSON格式）")
print("=" * 80)

system_prompt_memory = """You are an educational data analyst. Describe student learning events naturally and concisely."""

user_prompt_memory = """Student 1188 (assist2017) learning events:

1. Concept: 'addition-subtraction-concepts', Result: correctly
2. Concept: 'area-perimeter-volume', Result: incorrectly
3. Concept: 'geometry-basics', Result: correctly

For each event above, write ONE natural sentence describing what happened. 
Vary your phrasing. Return JSON format:
{
  "memories": [
    {"index": 1, "description": "<natural sentence>"},
    {"index": 2, "description": "<natural sentence>"},
    ...
  ]
}"""

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt_memory},
            {"role": "user", "content": user_prompt_memory}
        ],
        temperature=0.7,
        max_tokens=500,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    print(f"✅ 成功获取响应")
    print(f"响应长度: {len(content) if content else 0} 字符")
    print(f"响应内容:\n{content}\n")
    
    # 尝试解析JSON
    if content:
        result = json.loads(content)
        print(f"✅ JSON解析成功")
        print(f"包含 {len(result.get('memories', []))} 条memory\n")
    else:
        print(f"❌ 响应为空\n")
    
except json.JSONDecodeError as e:
    print(f"❌ JSON解析错误: {e}")
    print(f"响应内容: {content}\n")
except Exception as e:
    print(f"❌ 错误: {e}\n")

print("=" * 80)
print("测试3: 检查完整的response对象")
print("=" * 80)

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Test' in JSON format: {\"message\": \"Test\"}"}
        ],
        temperature=0.7,
        max_tokens=50,
        response_format={"type": "json_object"}
    )
    
    print(f"✅ Response对象信息:")
    print(f"  - ID: {response.id}")
    print(f"  - Model: {response.model}")
    print(f"  - Choices数量: {len(response.choices)}")
    print(f"  - Content: {response.choices[0].message.content}")
    print(f"  - Finish Reason: {response.choices[0].finish_reason}")
    print(f"  - Usage: {response.usage}\n")
    
except Exception as e:
    print(f"❌ 错误: {e}\n")

print("=" * 80)
print("诊断完成")
print("=" * 80)

