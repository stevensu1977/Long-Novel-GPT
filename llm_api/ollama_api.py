import boto3
import json
from .chat_messages import ChatMessages

import requests
import json
import time
import sys

class OllamaAPI:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        
    def list_models(self):
        """列出所有可用模型"""
        response = requests.get(f"{self.base_url}/api/tags")
        if response.status_code == 200:
            return response.json()["models"]
        else:
            raise Exception(f"Error listing models: {response.status_code}, {response.text}")
    
    def generate(self, model, prompt, system=None, stream=False, **params):
        """生成文本响应"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            **params
        }
        
        if system:
            payload["system"] = system
            
        if stream:
            return self._stream_response(url, payload)
        else:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"Error generating response: {response.status_code}, {response.text}")
    
    def chat(self, model, messages, stream=False, **params):
        """聊天对话接口"""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            **params
        }
        
        if stream:
            return self._stream_response(url, payload)
        else:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json()["message"]
            else:
                raise Exception(f"Error in chat: {response.status_code}, {response.text}")
    
    def embeddings(self, model, prompt):
        """获取文本嵌入向量"""
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": model,
            "prompt": prompt
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()["embedding"]
        else:
            raise Exception(f"Error getting embeddings: {response.status_code}, {response.text}")
    
    def pull_model(self, model_name):
        """从Ollama库拉取模型"""
        url = f"{self.base_url}/api/pull"
        payload = {"name": model_name}
        
        print(f"Pulling model {model_name}...")
        response = requests.post(url, json=payload, stream=True)
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "status" in data:
                    progress = data.get("completed", 0)
                    total = data.get("total", 0)
                    if total > 0:
                        percentage = (progress / total) * 100
                        print(f"Progress: {percentage:.2f}% - {data['status']}", end="\r")
                    else:
                        print(f"Status: {data['status']}", end="\r")
        
        print("\nModel pull completed!")
    
    def _stream_response(self, url, payload):
        """处理流式响应"""
        payload["stream"] = True
        response = requests.post(url, json=payload, stream=True)
        
        if response.status_code != 200:
            raise Exception(f"Error with stream: {response.status_code}, {response.text}")
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                chunk = data.get("response", "")
                full_response += chunk
                yield chunk
                
                # 如果是最后一个消息，可以获取额外信息
                if data.get("done", False):
                    metadata = {
                        "total_duration": data.get("total_duration"),
                        "load_duration": data.get("load_duration"),
                        "prompt_eval_count": data.get("prompt_eval_count"),
                        "prompt_eval_duration": data.get("prompt_eval_duration"),
                        "eval_count": data.get("eval_count"),
                        "eval_duration": data.get("eval_duration")
                    }
                    yield {"metadata": metadata, "full_response": full_response}

# Pricing reference: https://aws.amazon.com/bedrock/pricing/
ollama_model_config = {
    "qwen2.5-coder:3b": {
        "Pricing": (0.003/1000, 0.015/1000),
        "currency_symbol": '$',
    }
}

def stream_chat_with_ollama(messages, model='anthropic.claude-3-sonnet-20240229-v1:0', response_json=False, region_name='us-east-1', max_tokens=4096, n=1):
    """
    Stream chat with Ollama models
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Bedrock model ID
        response_json: Whether to request JSON response format
        region_name: AWS region name
        max_tokens: Maximum number of tokens to generate
        n: Number of responses to generate
        
    Yields:
        Updated messages list with assistant's response
    """
    try:
        ollama = OllamaAPI()
        prompt = "Explain quantum computing in simple terms"
        print(f"Streaming response for: '{prompt}'")
        
        print("\nResponse: ", end="")
        for chunk in ollama.generate(model, prompt, stream=True):
            if isinstance(chunk, dict) and "metadata" in chunk:
                print(f"\n\nGeneration stats: {chunk['metadata']}")
            else:
                print(chunk, end="", flush=True)
                
    except Exception as e:
        print(f"\nError with streaming: {e}")
    
    return messages

if __name__ == '__main__':
    pass
