import asyncio
import os
import uuid
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage

from agents.test_graph import Test

async def amain():
    gpt_model = ChatOpenAI(
        model="gpt-4.1",
        openai_api_base="https://api.openai.com/v1",
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    test_agent = Test(llm=gpt_model).build()
    msg = HumanMessage("can you make default c program printing hello world?")
    payload = {"messages": [msg]}
    # result = await test_agent.ainvoke(
    #     payload, config={"configurable": {"thread_id": str(uuid.uuid4())}},    
    # )
    
    # print(f"result: \n {result}")
    
    async for ev in test_agent.astream_events(
        payload, 
        config={"configurable": {"thread_id": str(uuid.uuid4())}},
        version="v2",
    ):
        # print ('hi')
        ev
        pass
            
    
    print("\n\n✨ Done!")
        
