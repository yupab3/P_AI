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
def web_search(
    question: str = "",
    language: str = "korean",
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

class LocalAgent:

    SYSTEM_INSTRUCTION = (
        """
        You are a specialized web search agent.  
        You have exactly one function available:  
        - `web_search(question: str, language: str = "korean", max_results: int = 5)`: searches for recent information and returns a dictionary with a `results` list or an error message.

        Your sole responsibility is:  
        1. For every user request that needs recent or factual information, determine the appropriate search query, preferred language, and number of results.  
        2. Invoke `web_search` with those parameters.  
        3. Return only the raw output of the `web_search` call as your response.

        Behavior rules:  
        - If the user’s request is not a search request, respond with:  
        “I’m sorry, I can only handle web search requests.”  
        - Do NOT include any greetings, explanations, or small talk.  
        - Do NOT ask follow-up questions.  
        - Always set the response status to `input_required` if you need more information, to `error` if the search fails, or to `completed` when it succeeds.  
        - Respond only in Korean. 
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
        self.tools = [web_search]
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
                    "content": "Making response...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Using Tool..",
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
