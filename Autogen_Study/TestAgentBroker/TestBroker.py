import os
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import logging

# 내부적으로 HTTP 호출이 발생하는지 확인하기 위한 로그 출력
# logging.basicConfig(level=logging.DEBUG)

# 환경변수 불러오기
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# LLM 설정
config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": api_key,
    }
]

# 에이전트 정의
code_writer = AssistantAgent(
    name="FrontEndEngineer",
    llm_config={"config_list": config_list},
    system_message="You are a clean and optimized code writer.",그
)

bug_fixer = AssistantAgent(
    name="BackEndEngineer",
    llm_config={"config_list": config_list},
    system_message="You fix bugs in the code based on feedback.",
)

reviewer = AssistantAgent(
    name="CSSReviewer",
    llm_config={"config_list": config_list},
    system_message="You review the code and give feedback for improvement.",
)

# GroupChat 구성
groupchat = GroupChat(
    agents=[code_writer, reviewer, bug_fixer],
    messages=[],
    max_round=10,
)

# Manager 설정 (자동 발화자 선택 기능은 비활성화 상태로 단순 coordinator 역할)
manager = GroupChatManager(
    groupchat=groupchat,
    llm_config={"config_list": config_list},
)

# 유저 에이전트
user_proxy = UserProxyAgent(name="Dong", human_input_mode="ALWAYS")

# 대화 흐름 (수동)
# 대화 시작
user_proxy.initiate_chat(manager)



# # Step 2: 코드 작성 후 reviewer에게 전달
# response_code = last_message = code_writer.chat_messages[user_proxy][-1]["content"]
# code_writer.send("Here's the code I wrote. Please review it.\n\n" + response_code, reviewer)

# # Step 3: 리뷰어가 피드백 후 bug fixer에게 전달
# response_review = reviewer.generate_reply(messages=reviewer.chat_messages[code_writer], sender=code_writer)
# reviewer.send("There are some issues with the code. Please fix them.\n\n" + response_review[1], bug_fixer)

# # Step 4: bug fixer가 수정 후 유저에게 전달
# response_bug_fixer = bug_fixer.generate_reply(messages=bug_fixer.chat_messages[reviewer], sender=reviewer)
# bug_fixer.send("I fixed the issues. Here's the updated code.\n\n" + response_bug_fixer[1], user_proxy)


# import os
# from dotenv import load_dotenv
# from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# # 환경변수 불러오기
# load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")

# # LLM 설정
# config_list = [
#     {
#         "model": "gpt-3.5-turbo",  # 또는 gpt-4, Claude 등
#         "api_key": os.getenv("OPENAI_API_KEY"),
#     }
# ]

# # 개별 Assistant Agent 생성
# code_writer = AssistantAgent(
#     name="defaultagent",
#     llm_config={"config_list": config_list},
#     system_message="You are betveteran code engineer. You should always answer with clean code and performance optimization in mind.",
# )
# bug_fixer = AssistantAgent(
#     name="BugFixer",
#     llm_config={"config_list": config_list},
#     system_message="You are the one who fixes bugs in the code. You have to improve the parts pointed out by the reviewer and fix them so that it runs well no matter what.",
# )
# reviewer = AssistantAgent(
#     name="CodeReviewer",
#     llm_config={"config_list": config_list},
#     system_message="You are the one who checks whether the code runs properly and finds the parts that need to be fixed or improved. You should always refer to the reference related to the language of the program you are dealing with to check whether the code runs properly.",
# )

# # 그룹 채팅 구성
# groupchat = GroupChat(
#     agents=[code_writer, bug_fixer, reviewer],
#     messages=[],
# )

# # 그룹 채팅을 관리할 중재자 역할의 매니저
# manager = GroupChatManager(
#     groupchat=groupchat,
#     select_speaker_auto_llm_config={"config_list": config_list} # 자동 선택 기능을 위한 옵션 추가
# )

# # 유저 입력을 프록시할 유저 에이전트 (Broker 역할도 수행 가능)
# user_proxy = UserProxyAgent(name="Dong", human_input_mode="ALWAYS")

# # 실제 워크플로우 시작
# user_proxy.initiate_chat(manager)