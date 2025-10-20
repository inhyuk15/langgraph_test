import os
import uuid
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage

from agents.code_generator import build_code_generator
from agents.test_graph import Test
from dotenv import load_dotenv

load_dotenv()

def main():
    gpt_model = ChatOpenAI(
        model="gpt-4.1",
        openai_api_base="https://api.openai.com/v1",
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    test_agent = Test(llm=gpt_model).build()
    msg = HumanMessage("can you make default c program printing hello world?")
    # agent = build_code_generator(model=gpt_model)
    # agent.invoke({"messages": [msg]})
    test_agent.invoke({"messages": [msg]},
                      config={"configurable": {"thread_id": str(uuid.uuid4())}})

if __name__ == "__main__":
    main()
