import asyncio
from autogen import AssistantAgent
from autogen import StructuredMessage, TextMessage
from autogen import Console
from autogen import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Define a tool that searches the web for information.
async def web_search(query: str) -> str:
    """Find information on the web"""
    return "AutoGen is a programming framework for building multi-agent applications."


# Create an agent that uses the OpenAI GPT-4o model.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    # api_key="YOUR_API_KEY",
)
agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    tools=[web_search],
    system_message="Use tools to solve tasks.",
)

async def assistant_run() -> None:
    response = await agent.on_messages(
        [TextMessage(content="Find information on AutoGen", source="user")],
        cancellation_token=CancellationToken(),
    )
    print(response.inner_messages)
    print(response.chat_message)


# # Use asyncio.run(assistant_run()) when running in a script.
# await assistant_run()

if __name__ == "__main__":
    asyncio.run(assistant_run())