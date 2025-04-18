import getpass
import os
from dotenv import load_dotenv

# 환경변수 불러오기
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from langchain_core.prompts import ChatPromptTemplate

system_template = "Translate the following from English into {language}"

prompt_template = ChatPromptTemplate.from_messages(
    [("system", system_template), ("user", "{text}")]
)

prompt = prompt_template.invoke({"language": "Italian", "text": "hi!"})

print(prompt)

print(prompt.to_messages())

model = init_chat_model("gpt-3.5-turbo", model_provider="openai")

response = model.invoke(prompt)
print(response.content)