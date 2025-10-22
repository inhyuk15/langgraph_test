import os
from typing import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class ToolMeta(BaseModel):
    function_name: str = Field(..., description="name of the tool used")
    parameters: dict = Field(..., description="parameters passed to the tool")
    
class File(BaseModel):
    file_path: str = Field(..., description="file's absolute path")
    extension: str = Field(..., description="file extension")

class WriteFileOutput(BaseModel):
    file: File
    meta: ToolMeta = Field(..., description="metadata about tool call")



@tool("write_file")
def write_file(file_path: Annotated[str, "absolute path to save the file"], content: Annotated[str, "file content"]) -> str:
    """
    Writes the given content to the specified file path.
    Returns the absolute path of the created file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
        
    # TODO: content는 너무 길 수 있어서 어느정도로 주어야하는지 애매함. 일단 안넣음.
    return WriteFileOutput(
        file=File(file_path=file_path, extension=file_path.split(".")[-1]),
        meta=ToolMeta(
            function_name="write_file",
            parameters={"file_path": file_path},
        )
    )


class ReadFileOutput(BaseModel):
    file: File
    content: str = Field(..., description="file content")
    meta: ToolMeta = Field(..., description="metadata about tool call")

@tool("read_file")
def read_file(file_path: Annotated[str, "absolute path of the file to read"]) -> ReadFileOutput:
    """
    Reads the content from the specified file path.
    Returns both the file metadata and its content.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return ReadFileOutput(
        file=File(file_path=file_path, extension=file_path.split(".")[-1]),
        content=content,
        meta=ToolMeta(
            function_name="read_file",
            parameters={"file_path": file_path},
        )
    )
