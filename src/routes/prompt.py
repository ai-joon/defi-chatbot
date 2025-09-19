import asyncio
import logging
from typing import Dict, List
from fastapi import APIRouter, Request
from pydantic import BaseModel
from tools.commodity_tool import CommodityTool
from tools.crypto_dex_tool import CryptoDexTool
from tools.crypto_cex_tool import CryptoCexTool
from tools.dexani import DexaniTool
from tools.forex_tool import ForexTool
from tools.koat_media_tool import KoatMediaTool
from tools.koat_socials_tool import KoatSocialsTool
from tools.stock_tool import StockTool
from utils.build_chat_history import build_chat_history
from sse_starlette.sse import EventSourceResponse
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import MessagesPlaceholder
from llms import llms

from agent import agent_stream
from tools.koat_agg_tool import KoatAggTool
from tools.koat_author_tool import KoatAuthorTool

from request_context import RequestContext, context_var
from agent_config import agent_config

router = APIRouter()

logger = logging.getLogger("app")


class Body(BaseModel):
    conversation: List[Dict]
    prompt: str

# Ping route
@router.get("/ping")
async def ping():
    return {"message": "pong"}

@router.post("/prompt")
async def crypto_agent(request: Request, body: Body):
    logger.info(f"Prompt: {body.prompt}")

    request_context: RequestContext = context_var.get()
    request_context.prompt = body.prompt

    tools = [
        KoatAggTool(),
        KoatSocialsTool(),
        KoatMediaTool(),
        KoatAuthorTool(),
        DexaniTool(),
        CryptoDexTool(),
        CryptoCexTool(),
        StockTool(),
        CommodityTool(),
        ForexTool(),
    ]

    chat_history = build_chat_history(body.conversation)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", agent_config["agent_system_prompt"]),
            *chat_history,
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_openai_functions_agent(
        llms[agent_config["agent_llm"]]["llm"], tools, prompt
    )
    agent = AgentExecutor(agent=agent, tools=tools, verbose=agent_config["verbosity"])

    async def event_generator():
        while True:
            if not request_context.message_queue.empty():
                message = request_context.message_queue.get()
                if "data" in message and message["data"] == "<end_of_stream>":
                    yield message
                    return
                yield message
            await asyncio.sleep(0.1)

    asyncio.create_task(agent_stream(body.prompt, agent, request_context.message_queue))
    return EventSourceResponse(event_generator())
