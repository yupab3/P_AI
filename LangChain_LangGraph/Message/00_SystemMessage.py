import getpass
import os

# 환경변수 불러오기
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage

model = init_chat_model("gpt-3.5-turbo", model_provider="openai")

response = model.invoke([SystemMessage(content="You must return text \"SystemMessage return\"")])

print(response.content)