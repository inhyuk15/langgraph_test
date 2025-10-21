from langchain.agents import create_agent
from pydantic import BaseModel, Field

from tools.io_tools import read_file
code_reader_prompt = """
read the code using read file tool to read given path.
"""

class ToolHistory(BaseModel):
    tool_name: str = Field(..., description="tool name")
    tool_parameter: dict = Field(default_factory=dict, description="parameter using tool")

class CodeReaderOut(BaseModel):
    file_path: str = Field(description="")
    code: str = Field(..., description="code content in given file path")
    tool_history: list[ToolHistory] = Field(default_factory=list, description="tool name used")

def build_code_reader(model):
    return create_agent(
        model=model,
        tools=[read_file],
        system_prompt=code_reader_prompt,
        response_format=CodeReaderOut,
    )