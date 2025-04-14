import os
import tempfile
from dotenv import load_dotenv
from autogen.coding import DockerCommandLineCodeExecutor

from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor

# 환경변수 불러오기
load_dotenv()

# LLM 설정
config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": os.environ.get("OPENAI_API_KEY"),
    }
]

# Create a temporary directory to store the code files.
temp_dir = tempfile.TemporaryDirectory()


### 호스트 환경에서 LocalCodeExecutor 사용 ###
# Create a local command line code executor.
# executor = LocalCommandLineCodeExecutor(
#     timeout=10,  # Timeout for each code execution in seconds.
#     work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
# )

# # Create an agent with code executor configuration.
# code_executor_agent = ConversableAgent(
#     "code_executor_agent",
#     llm_config=False,  # Turn off LLM for this agent.
#     code_execution_config={"executor": executor},  # Use the local command line code executor.
#     human_input_mode="ALWAYS",  # Always take human input for this agent for safety.
# )

### Docker를 활용한 LocalCodeExecutor 사용 ###
# Create a Docker command line code executor.
executor = DockerCommandLineCodeExecutor(
    image="python:3.12-slim",  # Execute code using the given docker image name.
    timeout=10,  # Timeout for each code execution in seconds.
    work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
)

# Create an agent with code executor configuration that uses docker.
code_executor_agent = ConversableAgent(
    "code_executor_agent_docker",
    llm_config=False,  # Turn off LLM for this agent.
    code_execution_config={"executor": executor},  # Use the docker command line code executor.
    human_input_mode="ALWAYS",  # Always take human input for this agent for safety.
)


### Local용 메시지 블록 ###
# message_with_code_block = """This is a message with code block.
# The code block is below:
# ```python
# import numpy as np
# import matplotlib.pyplot as plt
# x = np.random.randint(0, 100, 100)
# y = np.random.randint(0, 100, 100)
# plt.scatter(x, y)
# plt.savefig('scatter.png')
# print('Scatter plot saved to scatter.png')
# ```
# This is the end of the message.
# """


### Docker용 메시지 블록 ###
message_with_code_block = """This is a message with code block.
The code block is below:
```python
print('Docker Test Case Message')
```
This is the end of the message.
"""


# Generate a reply for the given code.
reply = code_executor_agent.generate_reply(messages=[{"role": "user", "content": message_with_code_block}])
print(reply)
print(os.listdir(temp_dir.name))

temp_dir.cleanup()
### 도커 환경을 더이상 사용하지 않는 경우 종료하는 명령 ###
# When the code executor is no longer used, stop it to release the resources.
executor.stop()