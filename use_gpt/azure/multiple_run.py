# pip install openai azure-identity

import time

import openai
from openai import AzureOpenAI
from azure.identity import DeviceCodeCredential
import concurrent.futures
from tqdm import tqdm
import json


endpoint = 'https://epic-dms-aoai.openai.azure.com/'

scope = "https://cognitiveservices.azure.com/.default"

tp = DeviceCodeCredential()
tr = None
client = None
tp.authenticate()
tr = tp.get_token(scope)
client = AzureOpenAI(
    azure_endpoint=endpoint,
    azure_ad_token = tr.token,
    api_version = "2025-04-01-preview",  # Use the latest API version
)

# 🎯 函数：对一个 prompt 发起请求（包含 system prompt）

def run_prompt(system_prompt, user_prompt):
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        },
    ]

    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=messages
        )
        return user_prompt, completion.choices[0].message.content
    except Exception as e:
        return user_prompt, f"[ERROR] {str(e)}"

# ✨ 多线程处理多个 prompt
def run_multiple_prompts(prompts, system_prompt, max_workers=5):
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(run_prompt, system_prompt, p) for p in prompts
        ]

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing Prompts", ncols=100):
            prompt, response = future.result()
            # print(f"Prompt: {prompt}\nResponse: {response}\n")
            results.append((prompt, response))

    return results



deployment = "gpt-4o"
num_workers = 10  # 最大线程数，可以根据需要调整
output_file = "result.json"
# ✅ 示例
prompts = [
    "Hello World",
    "What is the capital of France?",
    "Explain quantum computing in simple terms.",
    "Give me a creative idea for a short film.",
    "What's a good lens for night-time shooting?"
]
system_prompt = "You are a helpful assistant who always answers concisely."




# 🚀 执行
result = run_multiple_prompts(prompts, system_prompt, max_workers=num_workers)
# 保存为 JSON 文件
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(
        [{"prompt": prompt, "response": response} for prompt, response in result],
        f,
        ensure_ascii=False,  
        indent=2              
    )

print(f"Save result to file ：{output_file}")