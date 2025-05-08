from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import add_messages
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, HumanMessage
from react_agent.graph import call_model
from react_agent.state import State
from react_agent.utils import load_mcp_config_json
from react_agent.prompts import SYSTEM_PROMPT
import httpx
import os
import asyncio
from typing import Any, Dict, AsyncIterable, Literal
from pydantic import BaseModel
from typing import Optional
memory = MemorySaver()

@tool
def search_engine(
    query: Optional[str] = None
) -> Any:
    """
    Uses the React agent's `call_model` function to perform the task end-to-end and return the result.
    :param query: A string describing the task the user wants to perform.
    :return: The resulting content from the agent (string or JSON).
    """
    # 1) Initialize state with the user's message
    state: State = {"messages": []}
    print(1)
    if query:
        msgs = add_messages(state["messages"], [HumanMessage(content=query)])
        state["messages"] = msgs
    # 2) Invoke call_model directly
    config = RunnableConfig(
        provider="openai",
        model="gpt-4o",
        temperature=0.1,
        # streaming=True,  # 필요하면
    )
    print(2)
    print(state["messages"])
    print(2)
    result = asyncio.run(call_model(state, config))
    print(3)

    # 3) Extract and return the last AI message content
    messages = result.get("messages", [])
    if messages:
        ai_msg = messages[-1]
        return ai_msg.content
    return ""

@tool
def list_servers(
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    api_key: Optional[str] = None,
) -> dict:
    """
    Retrieves a paginated list of MCP servers from the Smithery Registry.

    Args:
        q: Optional search query (semantic search).
        page: Page number (default: 1).
        page_size: Number of items per page (default: 10).
        api_key: Smithery API key. If not provided, uses SMITHERY_API_KEY env var.

    Returns:
        A dict with `servers` and `pagination` fields, or an `error` on failure.
    """
    print(1)
    token = api_key or os.getenv("SMITHERY_API_KEY")
    if not token:
        return {"error": "No API key provided. Set SMITHERY_API_KEY or pass api_key."}

    url = "https://registry.smithery.ai/servers"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "page": page,
        "pageSize": page_size,
    }
    if q:
        params["q"] = q

    try:
        print(2)
        resp = httpx.get(url, params=params, headers=headers)
        print(3)
        resp.raise_for_status()
        print(4)
        data = resp.json()

        # 필터링: qualifiedName, description 만 추출
        servers = data.get("servers", [])
        print(servers)
        filtered = [
            {
                "qualifiedName": srv.get("qualifiedName"),
                "description": srv.get("description"),
            }
            for srv in servers
        ]
        return {"servers": filtered}
    except httpx.HTTPError as e:
        return {"error": f"API request failed: {e}"}
    except ValueError:
        return {"error": "Invalid JSON response from API."}


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

class McpAgent:

    SYSTEM_INSTRUCTION = (
        """
        You are a specialized agent for using the Smithery “toolbox” MCP tool.  
        You have exactly four functions available:  
        - `search_servers`: Search for MCP servers by name, description, or other attributes in the Smithery registry. :contentReference[oaicite:0]{index=0}  
        - `add_server`: Add an MCP server to your toolbox so its tools become available. :contentReference[oaicite:1]{index=1}  
        - `remove_server`: Remove a server and all its tools from the toolbox. :contentReference[oaicite:2]{index=2}  
        - `use_tool`: Execute a specific tool call on an already‐added MCP server. :contentReference[oaicite:3]{index=3}  

        Your sole responsibility is:  
        1. For every user request, determine which of these four functions is appropriate.  
        2. Extract the exact arguments needed.  
        3. Invoke that function via the `toolbox` tool interface.  
        4. Return only the raw output of that function call as your response.  

        Behavior rules:  
        - If the user’s request does not map to any of the four functions above, respond with:  
        “I’m sorry, I can only handle requests related to adding, removing, searching, or invoking MCP servers via the toolbox.”  
        - Do NOT perform any greetings, explanations, or small talk.  
        - Do NOT ask follow-up questions.  
        - Always set the response status to `input_required` if you need more information, to `error` if an error occurs, or to `completed` when the function call succeeds.  
        - Respond only in English.
        """
        # "You are a specialized agent for using the search tool."
        # "Your sole purpose is to identify the keyword for search based on the user’s input, execute it via the `search_engine` function, and return its result. 반드시 `search_engine` 툴을 사용하여 검색한 결과만 응답에 포함해야 합니다."
        # "If the user requests anything not related to tool usage, politely state that you cannot assist with that topic and can only handle search tool queries."
        # "Set the response status to `input_required` if additional information is needed from the user."
        # "Set the response status to `error` if an error occurs during processing."
        # "Set the response status to `completed` when the request is complete."
        # "Respond only in Korean."
    )
    MODEL_NAME="gpt-4o"
     
    def __init__(self):
        self.model = ChatOpenAI(model=self.MODEL_NAME)
        self.tools = [search_engine, list_servers]
        os.environ["LLM_MODEL_NAME"] = self.MODEL_NAME
        self.graph = create_react_agent(
            self.model, tools=self.tools, checkpointer=memory, prompt = self.SYSTEM_INSTRUCTION, response_format=ResponseFormat
        )

    def invoke(self, query, sessionId) -> str:
        config = {"configurable": {"thread_id": sessionId}}
        print ("invoke q: ",query)
        self.graph.invoke({"messages": [("user", query)]}, config)        
        return self.get_agent_response(config)

    async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]

            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Looking up the exchange rates...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing the exchange rates..",
                }            
        
        yield self.get_agent_response(config)

        
    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)        
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(structured_response, ResponseFormat): 
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
