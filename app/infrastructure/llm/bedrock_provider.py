"""AWS Bedrock LLM provider implementation."""
import json
import os
import asyncio
from typing import Optional, AsyncGenerator
from app.domain.ports.llm_port import LLMPort


class BedrockProvider(LLMPort):
    """
    AWS Bedrock LLM implementation.
    
    Requires AWS credentials configured (via AWS CLI, IAM role, or environment variables).
    """
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Initialize AWS Bedrock LLM client.
        
        Args:
            model_id: The Bedrock model ID to use.
            region: AWS region. If not provided, reads from AWS_REGION env var or uses 'us-east-1'.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens in the response.
        """
        self.model_id = model_id
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Bedrock runtime client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    service_name="bedrock-runtime",
                    region_name=self.region
                )
            except ImportError:
                raise ImportError(
                    "boto3 package is required. Install it with: pip install boto3"
                )
        return self._client
    
    async def generate(self, message: str) -> str:
        """
        Generate a response using AWS Bedrock API.
        
        Args:
            message: The input message/prompt.
            
        Returns:
            The generated response from Bedrock.
            
        Raises:
            Exception: If API call fails (authentication, rate limit, etc.).
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        client = self._get_client()
        
        # Prepare the request body based on model type
        if "claude" in self.model_id.lower():
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            })
        else:
            # Default format for other models
            body = json.dumps({
                "prompt": message,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            })
        
        try:
            # Bedrock uses synchronous boto3, so we use asyncio.to_thread
            response = await asyncio.to_thread(
                client.invoke_model,
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response based on model type
            response_body = json.loads(response["body"].read())
            
            if "claude" in self.model_id.lower():
                return response_body["content"][0]["text"]
            elif "amazon" in self.model_id.lower():
                return response_body["results"][0]["outputText"]
            else:
                # Generic fallback
                return str(response_body)
                
        except Exception as e:
            raise RuntimeError(f"AWS Bedrock API error: {str(e)}") from e
    
    async def generate_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using AWS Bedrock API.
        
        Note: Bedrock streaming requires invoke_model_with_response_stream.
        This is a simplified implementation that yields the full response.
        For true streaming, use Bedrock's streaming API.
        
        Args:
            message: The input message/prompt.
            
        Yields:
            Chunks of the generated response.
            
        Raises:
            Exception: If API call fails.
        """
        # For now, generate full response and yield it in chunks
        # TODO: Implement true streaming with invoke_model_with_response_stream
        full_response = await self.generate(message)
        
        # Yield in chunks of 10 characters for demonstration
        chunk_size = 10
        for i in range(0, len(full_response), chunk_size):
            yield full_response[i:i + chunk_size]
            await asyncio.sleep(0.01)  # Small delay to simulate streaming

