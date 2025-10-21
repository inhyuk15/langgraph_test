
from typing import Annotated, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from tools.io_tools import File

class TestState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    remaining_steps: int
    structured_response: dict
