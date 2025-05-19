from abc import ABC, abstractmethod
from typing import Any

from agenticrag.utils.logging_config import setup_logger
logger = setup_logger(__name__)

class BaseTask(ABC):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def name(self)->str:
        "Return name of task"
        pass

    @property
    @abstractmethod
    def description(self)->str:
        "Return description of the task"
        pass

    @abstractmethod
    def execute(*args, **kwargs)->Any:
        "Method to execute task"