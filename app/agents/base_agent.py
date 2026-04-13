"""Base agent class for all HR screening agents."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.services.usf_client import usf_client

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the HR screening pipeline."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.usf_client = usf_client
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the agent's main task."""
        pass
    
    async def think(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        Use LLM to process a prompt and return response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            
        Returns:
            LLM response content
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.usf_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=1024
            )
            
            if "choices" in response and response["choices"]:
                return response["choices"][0]["message"]["content"]
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error in agent think: {e}")
            return ""
    
    def log_action(self, action: str, details: Optional[Dict] = None):
        """Log an agent action."""
        msg = f"[{self.name}] {action}"
        if details:
            msg += f" | {details}"
        self.logger.info(msg)
