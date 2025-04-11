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

### NEVER 옵션 예제, 인간의 개입 없이 Agent가 추리를 함 ###
# agent_with_number = ConversableAgent(
#     "agent_with_number",
#     system_message="You are playing a game of guess-my-number. You have the "
#     "number 53 in your mind, and I will try to guess it. "
#     "If I guess too high, say 'too high', if I guess too low, say 'too low'. ",
#     llm_config={"config_list": config_list},
#     is_termination_msg=lambda msg: "53" in msg["content"],  # terminate if the number is guessed by the other agent
#     human_input_mode="NEVER",  # never ask for human input
# )

# agent_guess_number = ConversableAgent(
#     "agent_guess_number",
#     system_message="I have a number in my mind, and you will try to guess it. "
#     "If I say 'too high', you should guess a lower number. If I say 'too low', "
#     "you should guess a higher number. ",
#     llm_config={"config_list": config_list},
#     human_input_mode="NEVER",
# )

# result = agent_with_number.initiate_chat(
#     agent_guess_number,
#     message="I have a number between 1 and 100. Guess it!",
# )


### ALWAYS 옵션 예제, 인간이 추측을 하거나 스킵할 수 있음 ###
# agent_with_number = ConversableAgent(
#     "agent_with_number",
#     system_message="You are playing a game of guess-my-number. You have the "
#     "number 53 in your mind, and I will try to guess it. "
#     "If I guess too high, say 'too high', if I guess too low, say 'too low'. ",
#     llm_config={"config_list": config_list},
#     is_termination_msg=lambda msg: "53" in msg["content"],  # terminate if the number is guessed by the other agent
#     human_input_mode="NEVER",  # never ask for human input
# )

# human_proxy = ConversableAgent(
#     "human_proxy",
#     llm_config={"config_list": config_list},  # 여기에 LLM을 매핑해주면 skip했을 때 해당 LLM을 이용하여 자동 응답을 생성한다.
#     human_input_mode="ALWAYS",  # always ask for human input
# )

# # Start a chat with the agent with number with an initial guess.
# result = human_proxy.initiate_chat(
#     agent_with_number,  # this is the same agent with the number as before
#     message="10",
# )


### TERMINATE 옵션 예제, 인간이 추측을 하거나 스킵할 수 있음 ###
agent_with_number = ConversableAgent(
    "agent_with_number",
    system_message="You are playing a game of guess-my-number. "
    "In the first game, you have the "
    "number 53 in your mind, and I will try to guess it. "
    "If I guess too high, say 'too high', if I guess too low, say 'too low'. ",
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=1,  # maximum number of consecutive auto-replies before asking for human input
    is_termination_msg=lambda msg: "53" in msg["content"],  # terminate if the number is guessed by the other agent
    human_input_mode="TERMINATE",  # ask for human input until the game is terminated
)

agent_guess_number = ConversableAgent(
    "agent_guess_number",
    system_message="I have a number in my mind, and you will try to guess it. "
    "If I say 'too high', you should guess a lower number. If I say 'too low', "
    "you should guess a higher number. ",
    llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]},
    human_input_mode="NEVER",
)

result = agent_with_number.initiate_chat(
    agent_guess_number,
    message="I have a number between 1 and 100. Guess it!",
)