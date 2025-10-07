from curses import raw
from time import sleep
from typing import List, Optional, Union
from litellm import RateLimitError, completion

from agenticrag.types import BaseMessage, LLMResponse
from agenticrag.types.exceptions import LLMError

class LLMClient:
    def __init__(
        self, 
        model: str = "openai/gpt-4o", 
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        top_p: Optional[float] = 1.0,
        rate_limit_wait_multiplier: Optional[int] = 2,
        rate_limit_max_wait: Optional[int] = 32,
    ):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.top_p = top_p
        self.rate_limit_max_wait = rate_limit_max_wait
        self.rate_limit_wait_multiplier = rate_limit_wait_multiplier

    def invoke(self, messages: Union[str, BaseMessage, List[str], List[BaseMessage]]) -> LLMResponse:
        rate_limit_wait = 0
        formatted_messages = []
        if isinstance(messages, str):
            formatted_messages.append({"role": "user", "content": messages})
        elif isinstance(messages, list):
            for message in messages:
                if isinstance(message, str):
                    formatted_messages.append({"role": "user", "content": message})
                elif isinstance(message, BaseMessage):
                    formatted_messages.append({"role": message.role, "content": message.content})
                else:
                    raise LLMError("Invalid message type in list, expected str or BaseMessage")
        elif isinstance(messages, BaseMessage):
            formatted_messages.append({"role": messages.role, "content": messages.content})
        else:
            raise LLMError("Invalid message type, expected str, BaseMessage or list")
        
        while True:
            try:
                resp =  completion(
                    model=self.model, 
                    messages=formatted_messages, 
                    api_key=self.api_key,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
                break
            except RateLimitError as e:
                sleep(rate_limit_wait)
                rate_limit_wait *= self.rate_limit_wait_multiplier 
                if rate_limit_wait > self.rate_limit_max_wait:
                    raise LLMError(f"Rate limit exceeded: {e}")
            except Exception as e:
                raise LLMError(f"Failed to invoke LLM: {e}")

        return LLMResponse(
            role="assistant", 
            content=resp["choices"][0]["message"]["content"],
            completion_tokens=resp["usage"].get("completion_tokens"),
            prompt_tokens=resp["usage"].get("prompt_tokens"),
            total_tokens=resp["usage"].get("total_tokens"),
            raw_litellm_response=resp
        )