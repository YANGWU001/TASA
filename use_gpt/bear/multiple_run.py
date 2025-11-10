import concurrent.futures
from openai import OpenAI
from tqdm import tqdm
import json

# endpoint : pluto jobs: http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000
# endpoint : corp network: https://pluto-prod-hawang-llm-proxy-9qtfav-0-4000.colligo.dev/
# key = sk-_8YrmHReH57alQr1Jao8ww

# models:    
# • deepseek-r1
# • gpt-3.5-turbo
# • gpt-4.1
# • gpt-4.1-mini
# • gpt-4.1-nano
# • gpt-4.5-preview
# • gpt-4o
# • gpt-4o-mini
# • llama-3-1-70b
# • llama-3-1-8b
# • llama-3-2-90b-vision
# • o3
# • o3-mini
# • o4-mini
# • qwen-2-5-vl-7b
# • text-embedding-3-large
# • text-embedding-3-small

# 配置参数
endpoint = "http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000"
key = "sk-_8YrmHReH57alQr1Jao8ww"

# 初始化 OpenAI 客户端（注意加 "Bearer "）
client = OpenAI(
    api_key="Bearer " + key,
    base_url=endpoint,
)

# 单个 prompt 的请求函数
def run_prompt(system_prompt, user_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return user_prompt, response.choices[0].message.content
    except Exception as e:
        return user_prompt, f"[ERROR] {str(e)}"

# 多线程处理多个 prompts
def run_multiple_prompts(prompts, system_prompt, max_workers=5):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(run_prompt, system_prompt, prompt) for prompt in prompts
        ]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing Prompts", ncols=100):
            prompt, response = future.result()
            results.append((prompt, response))
    return results



model = "gpt-4.1"
output_file = "proxy_llm_results.json"
num_workers = 10
# 示例输入
prompts = [
    "Tell me a joke.",
    "What's the capital of Italy?",
    "Explain general relativity in simple terms.",
    "What makes a great short film script?",
    "Suggest a good camera angle for an emotional scene."
]

system_prompt = "You are a helpful assistant."

# 执行调用
results = run_multiple_prompts(prompts, system_prompt, max_workers=num_workers)

# 保存结果为 JSON 文件
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(
        [{"prompt": p, "response": r} for p, r in results],
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"Result saved in file {output_file}")
