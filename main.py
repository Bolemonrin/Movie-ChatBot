from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import cre

load_dotenv()


class Response(BaseModel):
    movie: str
    recommendations: list[str]

llm = ChatOpenAI(
    model="gpt-4o"
)
messages = [
    (
        "system",
        "You are a machine for recommending movies for users."
    ),
    (
        "human",
        "I want to watch a movie."
    )
]
response = llm.invoke(messages)
print(response)