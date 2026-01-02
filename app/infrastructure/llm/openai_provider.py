"""OpenAI LLM provider implementation."""
import os
from typing import Optional, AsyncGenerator
from app.domain.ports.llm_port import LLMPort


class OpenAIProvider(LLMPort):
    """
    OpenAI LLM implementation using the OpenAI API.
    
    Requires OPENAI_API_KEY environment variable to be set.
    
    Supports both legacy models (gpt-3.5, gpt-4) using chat.completions API
    and newer models (gpt-5-*) using responses API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Initialize OpenAI LLM client.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            model: The model to use (e.g., 'gpt-3.5-turbo', 'gpt-4', 'gpt-5-nano').
            temperature: Sampling temperature (0.0 to 2.0). Not used for GPT-5 models.
            max_tokens: Maximum tokens in the response.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.model = model
        self.temperature = temperature
        
        # For gpt-5 models, use lower default max_tokens to maintain coherence
        # GPT-5 Nano requires explicit max_output_tokens and works better with shorter responses
        if model.startswith("gpt-5"):
            # GPT-5 Nano works better with shorter responses (~200-600 tokens)
            # Default to 200 if not specified to ensure streaming works
            if max_tokens == 500:  # Default value, override it
                self.max_tokens = 200
            else:
                self.max_tokens = min(max_tokens, 600) if max_tokens > 600 else max_tokens
        else:
            self.max_tokens = max_tokens
        
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package is required. Install it with: pip install openai"
                )
        return self._client
    
    def _get_completion_params(self):
        """
        Get the correct parameters for API call based on model.
        
        Legacy models (gpt-3.5, gpt-4) use max_tokens and temperature.
        Newer models (gpt-5-*) use max_output_tokens and don't support temperature.
        """
        params = {}
        
        if self.model.startswith("gpt-5"):
            # GPT-5 models use max_output_tokens (not max_tokens!)
            params["max_output_tokens"] = self.max_tokens
            # GPT-5 models only support default temperature, don't send it
        elif self.model.startswith("o1"):
            # o1 models use max_tokens and don't support temperature
            params["max_tokens"] = self.max_tokens
        else:
            # Legacy models (gpt-3.5, gpt-4)
            params["max_tokens"] = self.max_tokens
            params["temperature"] = self.temperature
        
        return params
    
    async def generate(self, message: str) -> str:
        """
        Generate a response using OpenAI API.
        
        Args:
            message: The input message/prompt.
            
        Returns:
            The generated response from OpenAI.
            
        Raises:
            Exception: If API call fails (authentication, rate limit, etc.).
        """
        client = self._get_client()
        
        try:
            # GPT-5 models use responses API, not chat.completions
            if self.model.startswith("gpt-5"):
                import logging
                logger = logging.getLogger(__name__)
                
                response = await client.responses.create(
                    model=self.model,
                    input=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": message}
                            ]
                        }
                    ],
                    max_output_tokens=self.max_tokens
                )
                
                # Debug: Log response structure
                logger.info(f"Response from {self.model}: type={type(response)}, dir={dir(response)}")
                if hasattr(response, '__dict__'):
                    logger.info(f"Response attributes: {response.__dict__}")
                
                # Try different ways to get the output text
                output_text = None
                if hasattr(response, 'output_text'):
                    output_text = response.output_text
                elif hasattr(response, 'output'):
                    output_text = response.output
                elif hasattr(response, 'text'):
                    output_text = response.text
                elif isinstance(response, dict):
                    output_text = response.get('output_text') or response.get('output') or response.get('text')
                
                logger.info(f"Extracted output_text: {repr(output_text)}")
                return output_text or ""
            
            # Legacy models (gpt-3.5, gpt-4) use chat.completions
            completion_params = self._get_completion_params()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                **completion_params
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e
    
    async def generate_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using OpenAI API.
        
        For GPT-5 Nano, implements automatic fallback to GPT-5 Mini if streaming fails.
        
        Args:
            message: The input message/prompt.
            
        Yields:
            Chunks of the generated response as they become available.
            
        Raises:
            Exception: If API call fails.
        """
        client = self._get_client()
        import logging
        import asyncio
        logger = logging.getLogger(__name__)
        
        # GPT-5 models use responses API with streaming
        if self.model.startswith("gpt-5"):
            # Try GPT-5 Nano first (or whatever model is configured)
            primary_model = self.model
            fallback_model = "gpt-5-mini" if primary_model == "gpt-5-nano" else None
            
            if fallback_model:
                logger.info(f"Attempting streaming with {primary_model}, will fallback to {fallback_model} if needed")
            else:
                logger.info(f"Using responses API for streaming with model {primary_model}")
            
            try:
                chunks_yielded = 0
                async with client.responses.stream(
                    model=primary_model,
                    input=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": message}
                            ]
                        }
                    ],
                    max_output_tokens=self.max_tokens
                ) as stream:
                    async for event in stream:
                        if event.type == "response.output_text.delta":
                            if event.delta:
                                chunks_yielded += 1
                                yield event.delta
                
                # Check if streaming completed without yielding any chunks
                if chunks_yielded == 0:
                    logger.warning(
                        f"Streaming with {primary_model} completed but no chunks received. "
                        f"Falling back to {fallback_model}"
                    )
                    raise RuntimeError(f"No chunks received from {primary_model}")
                
                logger.info(f"Streaming with {primary_model} successful: {chunks_yielded} chunks yielded")
                return
                
            except Exception as primary_error:
                # Fallback to GPT-5 Mini if primary model fails
                if fallback_model:
                    logger.warning(
                        f"Streaming with {primary_model} failed: {primary_error}. "
                        f"Falling back to {fallback_model}"
                    )
                    
                    try:
                        # Generate full response with fallback model
                        fallback_response = await client.responses.create(
                            model=fallback_model,
                            input=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "input_text", "text": message}
                                    ]
                                }
                            ],
                            max_output_tokens=self.max_tokens
                        )
                        
                        # Debug: Log fallback response structure
                        logger.info(f"Fallback response from {fallback_model}: type={type(fallback_response)}")
                        if hasattr(fallback_response, '__dict__'):
                            logger.info(f"Fallback response attributes: {fallback_response.__dict__}")
                        
                        # Try different ways to get the output text
                        full_response = None
                        if hasattr(fallback_response, 'output_text'):
                            full_response = fallback_response.output_text
                        elif hasattr(fallback_response, 'output'):
                            full_response = fallback_response.output
                        elif hasattr(fallback_response, 'text'):
                            full_response = fallback_response.text
                        elif isinstance(fallback_response, dict):
                            full_response = fallback_response.get('output_text') or fallback_response.get('output') or fallback_response.get('text')
                        
                        logger.info(f"Extracted fallback output_text: {repr(full_response)}")
                        full_response = full_response or ""
                        
                        if full_response:
                            # Simulate streaming by yielding the response in small chunks
                            chunk_size = 5  # Characters per chunk for smooth streaming effect
                            for i in range(0, len(full_response), chunk_size):
                                yield full_response[i:i + chunk_size]
                                await asyncio.sleep(0.02)  # Small delay to simulate streaming
                            
                            logger.info(
                                f"Fallback to {fallback_model} successful: "
                                f"yielded {len(full_response)} characters in chunks"
                            )
                        else:
                            # Final fallback: try with a legacy model (gpt-3.5-turbo)
                            logger.warning(
                                f"Fallback to {fallback_model} generated empty response. "
                                f"Trying final fallback to gpt-3.5-turbo"
                            )
                            
                            try:
                                legacy_response = await client.chat.completions.create(
                                    model="gpt-3.5-turbo",
                                    messages=[
                                        {"role": "system", "content": "You are a helpful assistant."},
                                        {"role": "user", "content": message}
                                    ],
                                    max_tokens=self.max_tokens,
                                    temperature=0.7
                                )
                                
                                legacy_text = legacy_response.choices[0].message.content or ""
                                
                                if legacy_text:
                                    # Simulate streaming
                                    chunk_size = 5
                                    for i in range(0, len(legacy_text), chunk_size):
                                        yield legacy_text[i:i + chunk_size]
                                        await asyncio.sleep(0.02)
                                    
                                    logger.info(
                                        f"Final fallback to gpt-3.5-turbo successful: "
                                        f"yielded {len(legacy_text)} characters"
                                    )
                                else:
                                    raise RuntimeError("Legacy model also returned empty response")
                            except Exception as legacy_error:
                                logger.error(f"Final fallback to gpt-3.5-turbo also failed: {legacy_error}")
                                raise RuntimeError(
                                    f"All models failed. Primary: {primary_error}, "
                                    f"Fallback: {fallback_error}, Legacy: {legacy_error}"
                                ) from legacy_error
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback to {fallback_model} also failed: {fallback_error}"
                        )
                        raise RuntimeError(
                            f"Both {primary_model} and {fallback_model} failed. "
                            f"Primary error: {primary_error}, Fallback error: {fallback_error}"
                        ) from fallback_error
                else:
                    # No fallback available, re-raise original error
                    raise
            
            return
        
        # Legacy models (gpt-3.5, gpt-4) use chat.completions with streaming
        try:
            completion_params = self._get_completion_params()
            stream = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                stream=True,
                **completion_params
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta:
                        delta = choice.delta
                        content = getattr(delta, 'content', None)
                        if content:
                            yield content
        except Exception as e:
            raise RuntimeError(f"OpenAI API streaming error: {str(e)}") from e
