import os
from dotenv import load_dotenv
from autogen import ConversableAgent

# 환경변수 불러오기
load_dotenv()

# LLM 설정
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

### initiate_chat에서 max_turns 파라미터를 통해 제어하는 방식 ###
# result = joe.initiate_chat(cathy, message="Cathy, tell me a joke.", max_turns=3)


### ConversableAgent 클래스의 max_consecutive_auto_reply 파라미터를 통해 제어하는 방식 ###
# kim = ConversableAgent(
#     "kim",
#     system_message="Your name is kim and you are a part of a duo of comedians.",
#     llm_config={"config_list": config_list, "temperature": 0.7},
#     human_input_mode="NEVER",  # Never ask for human input.
#     max_consecutive_auto_reply=1,  # Limit the number of consecutive auto-replies.
# )

# result = kim.initiate_chat(cathy, message="Cathy, tell me a joke.")


### ConversableAgent 클래스의 is_termination_msg 파라미터를 통해 제어하는 방식 ###
kim = ConversableAgent(
    "kim",
    system_message="Your name is kim and you are a part of a duo of comedians.",
    llm_config={"config_list": config_list, "temperature": 0.7},
    human_input_mode="NEVER",  # Never ask for human input.
    is_termination_msg=lambda msg: "good bye" in msg["content"].lower(),
)

result = kim.initiate_chat(cathy, message="Cathy, tell me a joke and then say the words GOOD BYE.")
