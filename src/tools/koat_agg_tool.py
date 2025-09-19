import json
import logging
from typing import Literal, Optional, Type, Union
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
from langchain.agents import AgentType
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from llms import llms

from request_context import RequestContext, context_var
from utils.add_message_to_queue import add_message_to_queue
from utils.es_agg_connector import ESAggConnector

logger = logging.getLogger("app")


class SearchSchema(BaseModel):
    query: str = Field(description="The query string")
    agg_filter: Literal[
        "impressions", "sentiment", "engagement", "emotion", "influence", "manipulation"
    ] = Field(
        description="The type of aggregated data you are interested in returning for the query"
    )
    from_date: str = Field(
        "now-24h",
        description="A field used to specify the beginning of a date and time range for the data being queried. This can either be now minus a duration (e.g. now-24h, now-1d, now-2d, now-1w) or an ISO 8601 formatted string.",
    )
    to_date: Union[str, Literal["now"]] = Field(
        "now",
        description="A field used to specify the end of a date and time range for the data being queried. This can either be 'now', or an ISO 8601 formatted string.",
    )


class KoatAggTool(BaseTool):
    name = "agg_tool"
    description = """Useful for when you need to answer general questions about aggregated impressions, sentiment, engagement, emotions, influence, or manipulation data from social media."""
    args_schema: Type[BaseModel] = SearchSchema

    def _run(self) -> str:
        raise Exception("This tool cannot run synchronously")

    async def _arun(
        self,
        query: str,
        agg_filter: str,
        from_date: str = "now-24h",
        to_date: Union[str, Literal["now"]] = "now",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        logger.debug(f"Query: {query}")
        logger.debug(f"Agg filter: {agg_filter}")
        logger.debug(f"From: {from_date}")
        logger.debug(f"To: {to_date}")

        request_context: RequestContext = context_var.get()
        es_connector = ESAggConnector()
        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_init",
                        "message": f"Using Agg tool...",
                    }
                ),
                request_context.message_queue,
            )

        try:
            text = await es_connector.get_text_async(
                query,
                agg_filter=agg_filter,
                from_date=from_date,
                to_date=to_date,
                message_queue=request_context.message_queue,
                timezone=request_context.timezone,
            )
        except Exception as e:
            print(e)
            return "Data retrieval failed. You might not have permission to access this data."

        text += "\n\n The user has just been provided a graph of the data above, so do not repeat any of the data. Only provide meaningful insights from the data."
        logger.debug(f"Tool output: {text}")
        return text


if __name__ == "__main__":
    from langchain.agents import initialize_agent
    import asyncio

    async def main():
        agent_chain = initialize_agent(
            [KoatAggTool()],
            llm=llms["gpt4o"]["llm"],
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )
        print("")
        print(
            "Question: 'Can you tell me what public sentiment trend is like for BTC over the last 24h?'"
        )
        print(
            await agent_chain.arun(
                "Can you tell me what public sentiment trend is like for BTC over the last 24h?"
            )
        )

    asyncio.run(main())
