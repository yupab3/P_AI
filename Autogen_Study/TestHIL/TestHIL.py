import os
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, ConversableAgent
import logging

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

assistant = ConversableAgent(name="Assistant", llm_config={"config_list": config_list})
user = UserProxyAgent(name="Dong")

group_chat = GroupChat(agents=[user, assistant], messages=[], max_round=3)
manager = GroupChatManager(groupchat=group_chat)

user.initiate_chat(manager, message="JSON 형식에 맞게 내 정보를 정리해줘")