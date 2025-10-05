from dataclasses import dataclass, field
from typing import  Literal, Optional

from pydantic import BaseModel

@dataclass
class RAGAgentResponse:
    success: bool
    content: str
    iterations: Optional[int] = None
    datasets: list = field(default_factory=list)
    retrievers: list = field(default_factory=list)
    tasks: list = field(default_factory=list)

@dataclass
class BaseMessage:
    content: str
    role: Literal["user", "assistant", "system", "tool"] = "user"

@dataclass
class LLMResponse(BaseMessage):
    completion_tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    raw_litellm_response: Optional[dict] = None

@dataclass
class LLMTool:
    name: str
    func: callable
    args: Optional[BaseModel] = None
    description: Optional[str] = None