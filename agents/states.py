
from typing import Annotated, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class File(BaseModel):
    file_path: str = Field(..., description="file's absolute path")
    extension: str = Field(..., description="extension of file")


class TestState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    remaining_steps: int
    structured_response: File  # <- 여기에 결과가 들어옴
