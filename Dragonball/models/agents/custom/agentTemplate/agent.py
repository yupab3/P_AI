from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import add_messages
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, HumanMessage
from react_agent.graph import call_model
from react_agent.state import State
from react_agent.utils import load_mcp_config_json
from react_agent.prompts import SYSTEM_PROMPT
import os
import asyncio
import httpx
from typing import Optional
from bs4 import BeautifulSoup
from typing import Any, Dict, AsyncIterable, Literal
from pydantic import BaseModel
import os

memory = MemorySaver()

from bs4 import BeautifulSoup

@tool
def mcp_tool(
    query: Optional[str] = None
) -> Any:
    """
    Uses the React agent's `call_model` function to perform the task end-to-en
d and return the result.
    :param query: A string describing the task the user wants to perform.
    :return: The resulting content from the agent (string or JSON).
    """
    # 1) Initialize state with the user's message
    state: State = {"messages": []}
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
    result = asyncio.run(call_model(state, config))
    # 3) Extract and return the last AI message content
    messages = result.get("messages", [])
    print("MCP TOOL DONE")
    if messages:
        ai_msg = messages[-1]
        return ai_msg.content
    return ""

@tool
def web_search(
    question: str = "",
    language: str = "english",
    max_results: int = 5,
):
    """Use this to search for recent information.

    Args:
        question: The question you want to find information about.
        language: Preferred language for the search results (e.g., "english", "korean").
        max_results: The maximum number of results to return. Defaults to 5.

    Returns:
        A dictionary with a 'results' key containing a list of search results,
        or an error message if the search fails.
    """    
    try:
        url = "https://html.duckduckgo.com/html/"
        response = httpx.post(url, data={"q": question}, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        result_list = []

        for a in soup.find_all("a", class_="result__a", limit=max_results):
            title = a.get_text()
            link = a["href"]
            # print("title: ", title)
            # print("link: ", link)
            result_list.append({"title": title, "link": link})
        # print({"result": result_list})
        print("WEB SEARCH DONE")
        return {"result": result_list}  # ✅ 딕셔너리로 감쌈
    except httpx.HTTPError as e:
        return {"error": f"API request failed: {e}"}
    except ValueError:
        return {"error": "Invalid response format."}


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

class UserDefinedAgent:

    SYSTEM_INSTRUCTION = ""
    MODEL_NAME="gpt-4o"

    def __init__(self, inputmodel: str = "gpt-4o", inputsystem: str = ""):
        UserDefinedAgent.MODEL_NAME = inputmodel
        prefix = inputmodel.split("-", 1)[0].lower()
        os.environ["LLM_MODEL_NAME"] = self.MODEL_NAME
        if prefix == "gpt":
            self.model = ChatOpenAI(model=self.MODEL_NAME)
        elif prefix == "gemini":
            self.model = ChatGoogleGenerativeAI(model=self.MODEL_NAME)
        
        UserDefinedAgent.SYSTEM_INSTRUCTION = (
        f"""SYSTEM:{inputsystem}:

        You are a specialized agent with expertise in both web research and MCP tool operations.
        You may call **exactly two functions** for gathering information:
        - `web_search(query: str)`: performs an internet search and returns results.
        - `mcp_tool(server: str, tool: str, params: dict)`: invokes a specific tool on a named MCP server and returns its output.
         
        For each user request:
        1. Determine which function is appropriate (`web_search` for general queries, `mcp_tool` for MCP actions).
        2. Extract the exact arguments required.
        3. Invoke **only** that function.
        4. Return **only** the raw output of the function call in your response.
         
        Response status rules:
        - If you need more details from the user, set status to `input_required`.
        - If an error occurs during processing, set status to `error`.
        - When you have successfully satisfied the request, set status to `completed`.
         
        Additional rules:
        - Do **not** include any greetings, explanations, or small talk.
        - Do **not** ask follow-up questions beyond requesting missing parameters.
        - Match the response language exactly to the user’s language.
        """
        )
        if os.environ["SMITHERY_API_KEY"]:
            print("******MCP KEY EXIST******")
            self.tools = [web_search, mcp_tool]
        else:
            print("******MCP KEY IS NOT EXIST******")
            self.tools = [web_search]

        self.graph = create_react_agent(
            self.model, tools=self.tools, checkpointer=memory, prompt = self.SYSTEM_INSTRUCTION, response_format=ResponseFormat
        )

    def invoke(self, query, sessionId) -> str:
        config = {"configurable": {"thread_id": sessionId}}
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
                    "content": "Searching...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Making response..",
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
