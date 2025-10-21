import os
from typing import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class File(BaseModel):
    file_path: str = Field(..., description="file's absolute path")
    extension: str = Field(..., description="file extension")

class WriteFileOutput(BaseModel):
    file: File

@tool("write_file")
def write_file(file_path: Annotated[str, "absolute path to save the file"], content: Annotated[str, "file content"]) -> str:
    """
    Writes the given content to the specified file path.
    Returns the absolute path of the created file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        return WriteFileOutput(
            file=File(file_path=file_path, extension=file_path.split(".")[-1])
        )


class ReadFileOutput(BaseModel):
    file: File
    content: str = Field(..., description="file content")

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
        content=content
    )
