from abc import ABC, abstractmethod

from app.agents.state.types import AgentState
from langgraph.types import Command


class BaseSubAgent(ABC):
    name: str
    short_desc: str
    system_prompt: str

    def __init__(self, name: str, short_desc: str, system_prompt: str):
        self.name = name
        self.short_desc = short_desc
        self.system_prompt = system_prompt

    @abstractmethod
    def build_subgraph(self, state: AgentState) -> Command:
        ...