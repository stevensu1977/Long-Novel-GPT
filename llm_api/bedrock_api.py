import boto3
import json
from .chat_messages import ChatMessages

# Pricing reference: https://aws.amazon.com/bedrock/pricing/
bedrock_model_config = {
    "us.anthropic.claude-3-5-haiku-20241022-v1:0": {
        "Pricing": (0.003/1000, 0.015/1000),
        "currency_symbol": '$',
    },
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "Pricing": (0.00025/1000, 0.00125/1000),
        "currency_symbol": '$',
    },
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0": {
        "Pricing": (0.015/1000, 0.075/1000),
        "currency_symbol": '$',
    },
}

def stream_chat_with_bedrock(messages, model='anthropic.claude-3-sonnet-20240229-v1:0', response_json=False, region_name='us-east-1', max_tokens=4096, n=1):
    """
    Stream chat with AWS Bedrock models using the new converse_stream API
    
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
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        
        # Convert messages to Bedrock format
        bedrock_messages = []
        system_prompts = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompts = [{"text": msg["content"]}]
            else:
                bedrock_messages.append({
                    "role": msg["role"],
                    "content": [{"text": msg["content"]}]
                })
        
        # Prepare inference configuration
        inference_config = {
            "maxTokens": max_tokens,
            "temperature": 0.7,
            "topP": 0.9
        }
        
        # if response_json:
        #     inference_config["responseFormat"] = "json"
        
        # Stream the response
        response = bedrock.converse_stream(
            modelId=model,
            messages=bedrock_messages,
            inferenceConfig=inference_config,
            system=system_prompts
        )
        
        messages.append({'role': 'assistant', 'content': ''})
        content = ['' for _ in range(n)]
        
        for chunk in response["stream"]:
            if "contentBlockDelta" in chunk:
                text = chunk["contentBlockDelta"]["delta"]["text"]
                for i in range(n):
                    content[i] += text
                    messages[-1]['content'] = content if n > 1 else content[0]
                    yield messages
        
        return messages
        
    except Exception as e:
        print(f"ERROR: Can't invoke '{model}'. Reason: {e}")
        raise

if __name__ == '__main__':
    pass
