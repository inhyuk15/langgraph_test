import os
import uuid
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage

from agents.code_generator import build_code_generator
from agents.test_graph import Test
from dotenv import load_dotenv

load_dotenv()
# proxy = "http://127.0.0.1:8080"
# os.environ["HTTP_PROXY"] = proxy
# os.environ["HTTPS_PROXY"] = proxy
# os.environ["http_proxy"] = proxy
# os.environ["https_proxy"] = proxy

def main():
    gpt_model = ChatOpenAI(
        model="gpt-4.1",
        openai_api_base="https://api.openai.com/v1",
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # qwen_model = ChatOpenAI(
    #     model="Qwen/Qwen3-32B",
    #     openai_api_base="http://10.10.10.200:19401/v1",
    #     openai_api_key=os.getenv('OPENAI_API_KEY'),
    #     extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    # )
    test_agent = Test(llm=gpt_model).build()
    # test_agent = Test(llm=qwen_model).build()
    msg = HumanMessage("can you make default c program printing hello world?")
    # agent = build_code_generator(model=gpt_model)
    # agent.invoke({"messages": [msg]})
    test_agent.invoke({"messages": [msg]},
                      config={"configurable": {"thread_id": str(uuid.uuid4())}})

if __name__ == "__main__":
    main()
