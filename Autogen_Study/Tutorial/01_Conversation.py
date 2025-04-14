import os
from dotenv import load_dotenv
from autogen import ConversableAgent

# 환경변수 불러오기
load_dotenv()

config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": os.environ.get("OPENAI_API_KEY"),
    }
]

# 두 개의 에이전트를 대화시켜 결과적으로 전달받은 쪽에서 만들어낸 응답을 print 하는 얘제.
cathy = ConversableAgent(
    "cathy",
    system_message="Your name is Cathy and you are a part of a duo of comedians.",
    llm_config={"config_list": config_list, "temperature": 0.9},
    human_input_mode="NEVER",  # Never ask for human input.
)

joe = ConversableAgent(
    "joe",
    system_message="Your name is Joe and you are a part of a duo of comedians.",
    llm_config={"config_list": config_list, "temperature": 0.7},
    human_input_mode="NEVER",  # Never ask for human input.
)

result = joe.initiate_chat(cathy, message="Cathy, tell me a joke.", max_turns=2)
