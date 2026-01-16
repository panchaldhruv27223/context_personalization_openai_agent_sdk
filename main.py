import time 
import asyncio 
import nest_asyncio
from agents import Agent, Runner, set_tracing_disabled
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

set_tracing_disabled(True)

client = OpenAI()

async def main():
    agent = Agent(
        name= "Assistant",
        instructions= "Reply very concisely.",
    )

    result = await Runner.run(agent, "tell me why it is important to evaluate ai agents??")
    print(result.final_output)
    
if __name__ == "__main__":
    asyncio.run(main())