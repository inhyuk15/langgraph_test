from pathlib import Path
from typing import Annotated
from pydantic import BaseModel, Field
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from agents.code_generator import build_code_generator
from agents.states import TestState
from agents.code_reader import build_code_reader

def from_code_out(state):
    sr = state.get("structured_response")
    file = getattr(sr, 'file')
    return state

def show_file_path(state: TestState):
    sr = state.get('structured_response')
    file = getattr(sr, 'file')
    file_path = getattr(file, 'file_path')
    
    print(f"this is file path: {file_path}")

def show_code_content(state: TestState):
    sr = state.get('structured_response')
    code = getattr(sr, 'code')
    tool_history = getattr(sr, 'tool_history')
    
    print(f'this is code: \n\n {code}')
    print(f'this is tool history: \n\n {tool_history}')
    
class Test:
    def __init__(self, llm):
        self.llm = llm
    
    def build(self):
        graph = StateGraph(TestState)
        code_generator = build_code_generator(self.llm)
        code_reader = build_code_reader(self.llm)
        
        graph.add_node('code_generator', code_generator)
        graph.add_node('from_code_out', from_code_out)
        graph.add_node('show_file_path', show_file_path)
        graph.add_node('show_code_content', show_code_content)
        graph.add_node('code_reader', code_reader)
        
        
        graph.add_edge(START, 'code_generator')
        graph.add_edge('code_generator', 'code_reader')
        graph.add_edge('code_reader', 'show_code_content')
        graph.add_edge('show_code_content', END)
        
        memory = InMemorySaver()
        return graph.compile(checkpointer=memory)
    