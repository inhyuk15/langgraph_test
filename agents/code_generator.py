from langchain.agents import create_agent
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from agents.states import File, TestState
from tools.io_tools import write_file

code_generator_prompt = """
you are expert in c programing.
if user ask make c code, you MUST make only one file using write_file tool.
"""
test_prompt ="""
save only structured format data
"""

class CodeGeneratorOut(BaseModel):
    file: File = Field(..., description="Metadata object including both file path and extension, e.g., {file_path: './outputs/hello.c', extension: 'c'}")
    structured_response: dict

# TODO: create_agent vs create_react_agent 비교 필요 (mitmproxy로 실제로 state가 어떻게 전달되는지, 진짜 차이가 있는지. subState에 대해 바뀌었다고 하는데)
def build_code_generator(model):
    agent = create_agent(
        model=model,
        tools=[write_file],
        system_prompt=code_generator_prompt,
        response_format=CodeGeneratorOut,
    )
    return agent
    # def wrapper(state):
    #     result = agent.invoke(state)
    #     return {"file": result.file_path, "structured_repsonse": result.structured_response}

    # return RunnableLambda(wrapper)
    
    