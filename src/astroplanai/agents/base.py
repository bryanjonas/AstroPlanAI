"""Base agent class for OpenAI-compatible LLM interaction."""

from typing import Optional, Dict, Any
from openai import AsyncOpenAI


class BaseAgent:
    """Base class for LLM agents using OpenAI-compatible API."""

    def __init__(
        self,
        client: AsyncOpenAI,
        name: str,
        system_instruction: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize a base agent.

        Args:
            client: AsyncOpenAI client configured for VLLM
            name: Agent name (for logging/debugging)
            system_instruction: System prompt defining agent behavior
            model: Model name to use
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
        """
        self.client = client
        self.name = name
        self.system_instruction = system_instruction
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using the LLM.

        Args:
            prompt: User prompt
            **kwargs: Additional parameters for chat completion

        Returns:
            Generated text response
        """
        messages = [
            {"role": "system", "content": self.system_instruction},
            {"role": "user", "content": prompt},
        ]

        # Merge kwargs with defaults
        # Compute safe max_tokens (never negative or zero)
        requested_max = kwargs.get("max_tokens", self.max_tokens)
        safe_max = max(1, int(requested_max or 0))

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": safe_max,
        }


        response = await self.client.chat.completions.create(**params)
        return response.choices[0].message.content

    async def generate_with_context(
        self, prompt: str, context: Dict[str, Any], **kwargs
    ) -> str:
        """
        Generate a response with additional context prepended.

        Args:
            prompt: User prompt
            context: Dictionary of context data to include
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        # Format context into prompt
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        full_prompt = f"Context:\n{context_str}\n\n{prompt}"

        return await self.generate(full_prompt, **kwargs)
