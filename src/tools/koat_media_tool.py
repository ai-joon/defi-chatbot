import asyncio
import json
import logging
import time
from typing import List, Literal, Optional, Type, Union
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
)
from langchain.agents import AgentType
from langchain.agents.initialize import initialize_agent
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from llms import llms
from utils.add_message_to_queue import add_message_to_queue
from utils.es_connector import ESConnector
from utils.simple_map_reduce import simple_map_reduce
from request_context import RequestContext, context_var
from utils.lucene_query import create_lucene_query
from agent_config import agent_config

from utils.tag_extraction import extract_tags
from prompts.summarize.simple_mr import simple_mr_prompt, simple_combine_prompt

logger = logging.getLogger("app")


class SearchSchema(BaseModel):
    query: str = Field(description="Search query")
    emotion_filter: Optional[
        List[
            Literal[
                "anger",
                "joy",
                "disgust",
                "anticipation",
                "sadness",
                "fear",
                "trust",
                "surprise",
                "love",
            ],
        ]
    ] = Field(
        [],
        description="An optional array of filter terms for filtering content based on their emotion (Must be an array!).",
    )
    sentiment_filter: Optional[List[Literal["pos", "neu", "neg"]]] = Field(
        [],
        description="An optional array of filter terms for filtering tweets based on postive, neutral, or negative sentiment (Must be an array!).",
    )
    from_date: str = Field(
        "now-24h",
        description="A field used to specify the beginning of a date and time range for the data being queried. This can either be now minus a duration (e.g. now-24h, now-1d, now-2d, now-1w) or an ISO 8601 formatted string. The time range cannot be more than a month",
    )
    to_date: Union[str, Literal["now"]] = Field(
        "now",
        description="A field used to specify the end of a date and time range for the data being queried. This can either be 'now', or an ISO 8601 formatted string.",
    )


class KoatMediaTool(BaseTool):
    name = "news_media_expert"
    description = """Useful for when you need to answer questions news articles/media content. In order to set the timeframe, you must use the 'from_date' and 'to_date' parameters. If asked about a date range relative the current date, use "now".
    """
    args_schema: Type[BaseModel] = SearchSchema

    def _run(self) -> str:
        raise Exception("This tool cannot run synchronously")

    async def _arun(
        self,
        query: str,
        emotion_filter: List[
            Literal[
                "anger",
                "joy",
                "disgust",
                "anticipation",
                "sadness",
                "fear",
                "trust",
                "surprise",
            ],
        ] = None,
        sentiment_filter: List[Literal["pos", "neu", "neg"]] = None,
        from_date: str = "now-24h",
        to_date: Union[str, Literal["now"]] = "now",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        request_context: RequestContext = context_var.get()
        es_connector = ESConnector()

        emotion_filter = (
            create_lucene_query(emotion_filter, "OR") if emotion_filter else None
        )

        sentiment_filter = (
            create_lucene_query(sentiment_filter, "OR") if sentiment_filter else None
        )

        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_init",
                        "message": "Using KOAT Media tool...",
                    }
                ),
                request_context.message_queue,
            )

        score = agent_config["media_tool"]["score_override"]
        size = agent_config["media_tool"]["media_num_results"]

        text = await es_connector.get_text_async(
            query,
            score=score,
            size=size,
            influence="media",
            sentiment=sentiment_filter,
            emotion=emotion_filter,
            from_date=from_date,
            to_date=to_date,
            timezone=request_context.timezone,
        )

        output = extract_tags(
            await simple_map_reduce(text, simple_mr_prompt, simple_combine_prompt)
        )["summary"]

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


if __name__ == "__main__":

    async def main():
        request_context = RequestContext()
        request_context.timezone = "America/Edmonton"
        token = context_var.set(request_context)
        tools = [KoatMediaTool()]

        agent = initialize_agent(
            llm=llms["gpt4o"]["llm"],
            tools=tools,
            verbose=True,
            agent=AgentType.OPENAI_FUNCTIONS,
            handle_parsing_errors="Check your output and make sure it conforms!",
            max_iterations=10,
        )

        s = time.time()
        print(
            await agent.arun(
                "Could you expand on criticisms towards X's climate policies?"
            )
        )
        e = time.time()
        print(e - s)

    asyncio.run(main())
