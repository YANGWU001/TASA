#!/usr/bin/env python3
"""
统一的LLM客户端，支持GPT, Llama, Qwen
"""
import os
import httpx
from openai import OpenAI

# API配置
LLAMA_URL = "https://85bb6ded8e37.ngrok-free.app/predict/"
QWEN_URL = "https://5d80b2bc05ca.ngrok-free.app/predict/"
TIMEOUT = 120  # 增加timeout以应对复杂prompt

class UnifiedLLMClient:
    def __init__(self, model_name: str):
        self.model_name = model_name
        
        # 根据模型名称选择backend
        if 'llama' in model_name.lower():
            self.backend = 'llama'
            self.api_url = LLAMA_URL
        elif 'qwen' in model_name.lower():
            self.backend = 'qwen'
            self.api_url = QWEN_URL
        elif 'gpt' in model_name.lower():
            self.backend = 'gpt'
            # 动态导入配置
            api_key = os.getenv("API_KEY")
            endpoint = os.getenv("ENDPOINT")
            
            # 如果环境变量不存在，尝试从配置文件导入
            if not api_key or not endpoint:
                config_module = os.environ.get('TASA_CONFIG', 'tasa_config')
                try:
                    if config_module == 'tasa_config_llama':
                        from tasa_config_llama import API_KEY as api_key, ENDPOINT as endpoint
                    elif config_module == 'tasa_config_qwen':
                        from tasa_config_qwen import API_KEY as api_key, ENDPOINT as endpoint
                    elif config_module == 'tasa_config_gpt':
                        from tasa_config_gpt import API_KEY as api_key, ENDPOINT as endpoint
                    else:
                        from tasa_config import API_KEY as api_key, ENDPOINT as endpoint
                except ImportError:
                    # 最后尝试从tasa_config_gpt导入
                    from tasa_config_gpt import API_KEY as api_key, ENDPOINT as endpoint
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=endpoint
            )
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    def chat_completion(self, messages: list, temperature: float = 0.7, max_tokens: int = 2000):
        """
        统一的对话API
        
        Args:
            messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
        
        Returns:
            str: 模型生成的回复内容
        """
        if self.backend == 'gpt':
            return self._call_gpt(messages, temperature, max_tokens)
        elif self.backend in ['llama', 'qwen']:
            return self._call_custom(messages, temperature, max_tokens)
    
    def _call_gpt(self, messages: list, temperature: float, max_tokens: int) -> str:
        """调用GPT API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                return ""
        except Exception as e:
            print(f"   ⚠️ GPT API调用失败: {e}")
            return ""
    
    def _call_custom(self, messages: list, temperature: float, max_tokens: int) -> str:
        """调用Llama/Qwen自定义API"""
        try:
            # 将messages转换为system_prompt和user_prompt
            system_prompt = ""
            user_prompt = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt += msg["content"] + "\n"
                elif msg["role"] == "user":
                    user_prompt += msg["content"] + "\n"
                elif msg["role"] == "assistant":
                    # 对于历史对话，追加到user_prompt
                    user_prompt += f"Assistant: {msg['content']}\n"
            
            # 调用API
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.post(
                    self.api_url,
                    json={
                        "system_prompt": system_prompt.strip(),
                        "user_prompt": user_prompt.strip()
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('result', '')
                else:
                    print(f"   ⚠️ {self.backend.upper()} API返回错误: {response.status_code}")
                    return ""
        
        except Exception as e:
            print(f"   ⚠️ {self.backend.upper()} API调用失败: {e}")
            return ""


# 便捷函数
def get_llm_client(model_name: str) -> UnifiedLLMClient:
    """获取LLM客户端"""
    return UnifiedLLMClient(model_name)

