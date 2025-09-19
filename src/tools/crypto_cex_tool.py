import json
import logging
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from llms import llms
from utils.add_message_to_queue import add_message_to_queue
from request_context import RequestContext, context_var
from langchain.agents import initialize_agent
from langchain.agents import AgentType

from utils.ta_tool_builder import load_tools

logger = logging.getLogger("app")


tools = load_tools(
    "ta_config/indicators", "ta_config/crypto_cex_config.yaml", "CRYPTO", "CEX"
)
agent = initialize_agent(
    tools,
    llm=llms["gpt4o"]["llm"],
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
)


class SearchSchema(BaseModel):
    question: str = Field(
        description="Forward the user's question to the crypto cex expert"
    )


class CryptoCexTool(BaseTool):
    name = "crypto_cex_expert"
    description = """Useful for when you need to answer questions related to crypto financial indicators on centralized exchanges (CEX)"""
    args_schema: Type[BaseModel] = SearchSchema

    def _run(self) -> str:
        raise Exception("This tool cannot run synchronously")

    async def _arun(
        self,
        question: str,
    ) -> str:
        request_context: RequestContext = context_var.get()
        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_init",
                        "message": f"Using crypto cex tool...",
                    }
                ),
                request_context.message_queue,
            )

        output = await agent.arun(question)

        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_output",
                        "message": output,
                    }
                ),
                request_context.message_queue,
            )

        logger.debug(f"Tool output: {output}")

        return output
