import os
from dotenv import load_dotenv

from autogen import ConversableAgent
from typing import Annotated, Literal

# 환경변수 불러오기
load_dotenv()

# LLM 설정
config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": os.environ.get("OPENAI_API_KEY"),
    }
]

Operator = Literal["+", "-", "*", "/"]

### pydantic 을 활용한 도구 스키마를 곁들인 툴 생성 ###
# from pydantic import BaseModel, Field

# class CalculatorInput(BaseModel):
#     a: Annotated[int, Field(description="The first number.")]
#     b: Annotated[int, Field(description="The second number.")]
#     operator: Annotated[Operator, Field(description="The operator.")]


# def calculator(input: Annotated[CalculatorInput, "Input to the calculator."]) -> int:
#     if input.operator == "+":
#         return input.a + input.b
#     elif input.operator == "-":
#         return input.a - input.b
#     elif input.operator == "*":
#         return input.a * input.b
#     elif input.operator == "/":
#         return int(input.a / input.b)
#     else:
#         raise ValueError("Invalid operator")


### Autogen 자동 스키마 생성을 이용하는 기본적인 툴 생성 ###
def calculator(a: int, b: int, operator: Annotated[Operator, "operator"]) -> int:
    if operator == "+":
        return a + b
    elif operator == "-":
        return a - b
    elif operator == "*":
        return a * b
    elif operator == "/":
        return int(a / b)
    else:
        raise ValueError("Invalid operator")
    

# Let's first define the assistant agent that suggests tool calls.
assistant = ConversableAgent(
    name="Assistant",
    system_message="You are a helpful AI assistant. "
    "You can help with simple calculations. "
    "Return 'TERMINATE' when the task is done.",
    llm_config={"config_list": config_list},
)

# The user proxy agent is used for interacting with the assistant agent
# and executes tool calls.
user_proxy = ConversableAgent(
    name="User",
    llm_config=False,
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
    human_input_mode="NEVER",
)

### Tool 호출(register_for_llm)에이전트와 실행(register_for_execution)에이전트 각각 등록하기 ###
# Register the tool signature with the assistant agent.
assistant.register_for_llm(name="calculator", description="A simple calculator")(calculator)

# Register the tool function with the user proxy agent.
user_proxy.register_for_execution(name="calculator")(calculator)


### Tool 호출(register_for_llm)과 실행(register_for_execution) 한 번에 등록하기 ###
# from autogen import register_function

# # Register the calculator function to the two agents.
# register_function(
#     calculator,
#     caller=assistant,  # The assistant agent can suggest calls to the calculator.
#     executor=user_proxy,  # The user proxy agent can execute the calculator calls.
#     name="calculator",  # By default, the function name is used as the tool name.
#     description="A simple calculator",  # A description of the tool.
# )

### 3.5는 틀리지만, 4는 정답을 찾는다 ###
# chat_result = user_proxy.initiate_chat(assistant, message="What is (44232 + 13312 / (232 - 32)) * 5?")
chat_result = user_proxy.initiate_chat(assistant, message="What is (1423 - 123) / 3 + (32 + 23) * 5?")

### 자동으로 생성된 스키마 ###
print(assistant.llm_config["tools"])