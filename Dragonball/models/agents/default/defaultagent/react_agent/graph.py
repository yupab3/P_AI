from datetime import datetime, timezone, timedelta
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS
from react_agent import utils
from contextlib import asynccontextmanager
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain_anthropic.chat_models import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import load_prompt

import os, asyncio
from dotenv import load_dotenv

load_dotenv()
memory = MemorySaver()


@asynccontextmanager
async def make_graph(mcp_tools: Dict[str, Dict[str, str]]):
    async with MultiServerMCPClient(mcp_tools) as client:
        print(mcp_tools)
        if os.getenv("OPENAI_API_KEY"):
            model = ChatOpenAI(model=os.environ["LLM_MODEL_NAME"], temperature=0.1)
        elif os.getenv("GOOGLE_API_KEY"):
            model = ChatGoogleGenerativeAI(model=os.environ["LLM_MODEL_NAME"])
        print("inin1")
        agent = create_react_agent(model, client.get_tools(), checkpointer=memory)
        print("inin2")
        yield agent


async def call_model(
    state: State, config: RunnableConfig
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_runnable_config(config)
    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(
            tz=timezone(timedelta(hours=9), "Asia/Seoul")
        ).isoformat()
    )
    print("---------sys---------")
    print(system_message)
    print("---------sys---------")

    # Get the MCP config path from mounted volume
    mcp_config_json_path = "/Users/dongyeuk/Infobank/Dragonball/models/agents/default/defaultagent/mcp-config/mcp_config.json"
    mcp_tools = {}
    if os.path.exists(mcp_config_json_path):
        mcp_tools = await utils.load_mcp_config_json(mcp_config_json_path)
        # Extract the servers configuration from mcpServers key
        mcp_tools = mcp_tools.get("mcpServers", {})
        print(f"Loaded MCP tools from {mcp_config_json_path}")
    else:
        print(f"Warning: MCP config file not found at {mcp_config_json_path}")
        mcp_tools = {}

    print("설정된 mcp_tools(JSON)")
    print(mcp_tools)

    response = None

    async with make_graph(mcp_tools) as my_agent:
        # Create the messages list
        print("in0")
        print(state)
        messages = [
            SystemMessage(content=system_message),
            *state["messages"],
        ]

        # Pass messages with the correct dictionary structure
        print("in1")
        result = await my_agent.ainvoke({"messages": messages}, config,)
        print("after invoke:", result)
        response = result["messages"][-1]
        print("in2")
        print("---------resp--------")
        print(response)
        print("---------resp--------")

    # Handle the case when it's the last step and the model still wants to use a tool
    # if state.is_last_step and response.tool_calls:
    #     return {
    #         "messages": [
    #             AIMessage(
    #                 id=response.id,
    #                 content="Sorry, I could not find an answer to your question in the specified number of steps.",
    #             )
    #         ]
    #     }
    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}


# Define a new graph

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(call_model)
builder.add_node("tools", ToolNode(TOOLS))

# Set the entrypoint as `call_model`
# This means that this node is the first one called
builder.add_edge("__start__", "call_model")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"


# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    # After call_model finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Add a normal edge from `tools` to `call_model`
# This creates a cycle: after using tools, we always return to the model
builder.add_edge("tools", "call_model")

# Compile the builder into an executable graph
# You can customize this by adding interrupt points for state updates
graph = builder.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
)
graph.name = "ReAct Agent"  # This customizes the name in LangSmith