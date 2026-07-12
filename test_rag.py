import asyncio
from app.tools.qa_tool import qa_tool

async def test():
    # Create a very long string that would normally be truncated
    context = "Hello world. " * 3000 + "The secret project is called Project Orion and it launches in 2027. " + "Goodbye. " * 3000
    res = await qa_tool(context, "What is the name of the secret project and when does it launch?")
    print("Answer:", res)

if __name__ == "__main__":
    asyncio.run(test())
