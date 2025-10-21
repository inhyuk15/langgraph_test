from langchain.agents import create_agent
from pydantic import BaseModel, Field

from tools.io_tools import read_file

code_reader_prompt = """
read the code using read file tool to read given path.
"""

class CodeReaderOut(BaseModel):
    file_path: str = Field(description="")
    code: str = Field(..., description="code content in given file path")
    structured_response: dict

def build_code_reader(model):
    return create_agent(
        model=model,
        tools=[read_file],
        system_prompt=code_reader_prompt,
        response_format=CodeReaderOut,
    )