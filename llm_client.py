"""
统一的LLM Client Wrapper
支持GPT、Llama、Qwen等不同的backbone
"""
import os
import httpx
from openai import OpenAI
from typing import Dict, List, Optional

# API配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")

LLAMA_URL = "https://2d96013eaaf0.ngrok-free.app/predict/"
QWEN_URL = "https://d53740ee5f4b.ngrok-free.app/predict/"

class UnifiedLLMClient:
    """统一的LLM客户端，支持多种backbone"""
    
    def __init__(self, model_name: str):
        """
        Args:
            model_name: 模型名称，如 "gpt-oss-120b", "llama-3.1-8b", "qwen3-4b"
        """
        self.model_name = model_name
        self.model_type = self._get_model_type(model_name)
        
        if self.model_type == "gpt":
            self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_ENDPOINT)
        elif self.model_type in ["llama", "qwen"]:
            self.client = None  # 使用httpx直接调用
        else:
            raise ValueError(f"Unsupported model: {model_name}")
    
    def _get_model_type(self, model_name: str) -> str:
        """根据模型名称判断类型"""
        if "llama" in model_name.lower():
            return "llama"
        elif "qwen" in model_name.lower():
            return "qwen"
        else:
            return "gpt"
    
    def _get_api_url(self) -> str:
        """获取API URL"""
        if self.model_type == "llama":
            return LLAMA_URL
        elif self.model_type == "qwen":
            return QWEN_URL
        return None
    
    def chat_completion(self, messages: List[Dict], temperature: float = 0.7, 
                       max_tokens: int = 500, **kwargs):
        """
        统一的chat completion接口
        
        Args:
            messages: 消息列表，格式为 [{"role": "system/user/assistant", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
        
        Returns:
            response对象，统一格式
        """
        if self.model_type == "gpt":
            # GPT使用OpenAI格式
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response
        
        elif self.model_type in ["llama", "qwen"]:
            # Llama/Qwen使用自定义API
            # 转换消息格式
            system_prompt = ""
            user_prompt = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                elif msg["role"] == "user":
                    user_prompt = msg["content"]
                elif msg["role"] == "assistant":
                    # 如果有assistant消息，添加到user_prompt中作为上下文
                    user_prompt = f"Previous: {msg['content']}\n\n{user_prompt}"
            
            # 调用API
            url = self._get_api_url()
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    url,
                    json={
                        "system_prompt": system_prompt,
                        "user_prompt": user_prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                resp.raise_for_status()
                result = resp.json()
            
            # 转换为统一格式
            class MockResponse:
                def __init__(self, content):
                    self.choices = [type('obj', (object,), {
                        'message': type('obj', (object,), {'content': content})()
                    })()]
            
            return MockResponse(result.get('result', ''))
        
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")


def get_llm_client(model_name: str) -> UnifiedLLMClient:
    """获取LLM客户端的工厂函数"""
    return UnifiedLLMClient(model_name)

