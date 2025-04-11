import os
from dotenv import load_dotenv
from pathlib import Path

from autogen import ConversableAgent
from autogen.coding.jupyter import DockerJupyterServer, JupyterCodeExecutor

# 환경변수 불러오기
load_dotenv()

# LLM 설정
config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": os.environ.get("OPENAI_API_KEY"),
    }
]

server = DockerJupyterServer()

output_dir = Path("coding")
output_dir.mkdir(exist_ok=True)

code_executor_agent = ConversableAgent(
    name="code_executor_agent",
    llm_config=False,
    code_execution_config={
        "executor": JupyterCodeExecutor(server, output_dir=output_dir),
    },
    human_input_mode="NEVER",
)

# The code writer agent's system message is to instruct the LLM on how to
# use the Jupyter code executor with IPython kernel.
code_writer_system_message = """
You have been given coding capability to solve tasks using Python code in a stateful IPython kernel.
You are responsible for writing the code, and the user is responsible for executing the code.

When you write Python code, put the code in a markdown code block with the language set to Python.
For example:
```python
x = 3
```
You can use the variable `x` in subsequent code blocks.
```python
print(x)
```

Write code incrementally and leverage the statefulness of the kernel to avoid repeating code.
Import libraries in a separate code block.
Define a function or a class in a separate code block.
Run code that produces output in a separate code block.
Run code that involves expensive operations like download, upload, and call external APIs in a separate code block.

When your code produces an output, the output will be returned to you.
Because you have limited conversation memory, if your code creates an image,
the output will be a path to the image instead of the image itself."""

code_writer_agent = ConversableAgent(
    "code_writer",
    system_message=code_writer_system_message,
    llm_config={"config_list": config_list},
    code_execution_config=False,  # Turn off code execution for this agent.
    max_consecutive_auto_reply=2,
    human_input_mode="NEVER",
)

import pprint

chat_result = code_executor_agent.initiate_chat(
    code_writer_agent, message="Write Python code to calculate the 14th Fibonacci number."
)

# pprint.pprint(chat_result)

server.stop()