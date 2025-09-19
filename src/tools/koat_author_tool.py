import asyncio
import json
import logging
from typing import List, Literal, Optional, Type, Union
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
)
from langchain.agents import AgentType
from langchain.agents.initialize import initialize_agent
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from llms import llms
from prompts.prompts import authors_combine_prompt, authors_mr_prompt
from request_context import RequestContext, context_var
from utils.add_message_to_queue import add_message_to_queue
from utils.es_connector import ESConnector
from utils.map_reduce_loader import load_map_reduce_chain
from utils.lucene_query import create_lucene_query
from agent_config import agent_config
from utils.simple_map_reduce import simple_map_reduce
from utils.tag_extraction import extract_tags
from prompts.summarize.simple_mr import simple_mr_prompt, simple_combine_prompt

mr_chain = load_map_reduce_chain(
    authors_mr_prompt,
    authors_combine_prompt,
    map_llm=llms["gpt4o"]["llm"],
    combine_llm=llms["gpt4o"]["llm"],
)

logger = logging.getLogger("app")


class SearchSchema(BaseModel):
    authors: List[str] = Field(
        description="An array of social media account names. (must be exact social media account handles or usernames)"
    )
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
            ],
        ]
    ] = Field(
        [],
        description="An optional array of filter terms for filtering social media posts based on their emotion (Must be an array!).",
    )
    influence_filter: Optional[List[Literal["bot", "susbot", "organic"]]] = Field(
        [],
        description="An optional array of filter terms for filtering social media posts from users that are flagged as bots, suspected to be bots, or organic users (Must be an array!).",
    )
    sentiment_filter: Optional[List[Literal["pos", "neu", "neg"]]] = Field(
        [],
        description="An optional array of filter terms for filtering tweets based on postive, neutral, or negative sentiment (Must be an array!).",
    )
    from_date: str = Field(
        "now-24h",
        description="A field used to specify the beginning of a date and time range for the data being queried. This can either be now minus a duration (e.g. now-24h, now-1d, now-2d, now-1w) or an ISO 8601 formatted string.",
    )
    to_date: Union[str, Literal["now"]] = Field(
        "now",
        description="A field used to specify the end of a date and time range for the data being queried. This can either be 'now', or an ISO 8601 formatted string.",
    )


class KoatAuthorTool(BaseTool):
    name = "authors_post_search"
    description = """Useful for when you need to answer questions about what specific social media users are saying. In order to set the timeframe, you must use the 'from_date' and 'to_date' parameters. If asked about a date range relative the current date, use "now".
    """
    args_schema: Type[BaseModel] = SearchSchema

    def _run(self) -> str:
        raise Exception("This tool cannot run synchronously")

    async def _arun(
        self,
        authors: List[str],
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
        influence_filter: List[Literal["bot", "susbot", "organic"]] = None,
        sentiment_filter: List[Literal["pos", "neu", "neg"]] = None,
        from_date: str = "now-24h",
        to_date: Union[str, Literal["now"]] = "now",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        request_context: RequestContext = context_var.get()
        es_connector = ESConnector()

        authors = create_lucene_query(authors, "OR")

        emotion_filter = (
            create_lucene_query(emotion_filter, "OR") if emotion_filter else None
        )
        influence_filter = (
            create_lucene_query(influence_filter, "OR") if influence_filter else None
        )
        sentiment_filter = (
            create_lucene_query(sentiment_filter, "OR") if sentiment_filter else None
        )

        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_init",
                        "message": f"Using KOAT Author Post tool...",
                    }
                ),
                request_context.message_queue,
            )

        text = await es_connector.get_text_async(
            authors,
            influence=influence_filter,
            sentiment=sentiment_filter,
            emotion=emotion_filter,
            from_date=from_date,
            to_date=to_date,
            query_type="author",
        )

        if len(text) == 0:
            return "No results found"

        chain_output = extract_tags(
            await simple_map_reduce(text, simple_mr_prompt, simple_combine_prompt)
        )["summary"]

        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_output",
                        "message": chain_output,
                    }
                ),
                request_context.message_queue,
            )

        logger.debug(f"Tool output: {chain_output}")
        return chain_output


if __name__ == "__main__":
    tools = [KoatAuthorTool()]

    async def main():
        agent = initialize_agent(
            llm=llms["chatgpt16k"]["llm"],
            tools=tools,
            verbose=True,
            agent=AgentType.OPENAI_FUNCTIONS,
            handle_parsing_errors="Check your output and make sure it conforms!",
            max_iterations=10,
        )
        print(
            await agent.arun("Are there any bots supporting reddit's recent decision?")
        )

    asyncio.run(main())
