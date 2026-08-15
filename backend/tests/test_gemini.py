import os, dotenv, asyncio
from livekit.plugins.google import LLM
from livekit.agents.llm import ChatContext, ChatMessage

dotenv.load_dotenv(".env.local")


async def main():
    llm = LLM(model="gemini-3.1-flash-lite")
    ctx = ChatContext()
    ctx.messages.append(ChatMessage(role="user", content="hello"))

    stream = await llm.chat(chat_ctx=ctx)
    async for chunk in stream:
        print(chunk.choices[0].delta.content, end="")
    print()


if __name__ == "__main__":
    asyncio.run(main())
