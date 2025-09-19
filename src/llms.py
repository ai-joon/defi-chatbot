from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, ChatOpenAI
import tiktoken

load_dotenv()

llms = {
    "chatgpt16k": {
        "llm": AzureChatOpenAI(temperature=0, deployment_name="gpt-35-turbo-16k"),
        "token_limit": 16384,
        "tokenizer": tiktoken.get_encoding("cl100k_base"),
    },
    "gpt4o": {
        "llm": AzureChatOpenAI(temperature=0, deployment_name="wiseonegpt-4o-mini"), # gpt-4o
        "token_limit": 128000,
        "tokenizer": tiktoken.encoding_for_model("gpt-4o"),
    },
}
