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

student_agent = ConversableAgent(
    name="Student_Agent",
    system_message="You are a student willing to learn.",
    llm_config={"config_list": config_list},
)

teacher_agent = ConversableAgent(
    name="Teacher_Agent",
    system_message="You are a math teacher.",
    llm_config={"config_list": config_list},
)

chat_result = student_agent.initiate_chat(
    teacher_agent,
    message="What is triangle inequality?",
    summary_method="reflection_with_llm",
    max_turns=2,
)

print(chat_result.summary)
print(ConversableAgent.DEFAULT_SUMMARY_PROMPT)