from abc import ABC, abstractmethod
from typing import Any

class LLMProvider(ABC):
    @abstractmethod
    async def complete_text(self, prompt: str, max_tokens: int = 256) -> str: ...
    @abstractmethod
    async def complete_json(self, prompt: str, schema: dict, max_tokens: int = 512) -> dict[str, Any]: ...
