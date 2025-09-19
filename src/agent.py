import json
import logging
from queue import Queue
import time
from langchain.chains import LLMChain
import openai
from langchain.schema import OutputParserException

from langchain_community.callbacks import get_openai_callback
from prompts.prompts import prompt_crafter_prompt

from langchain.agents.agent import AgentExecutor
from llms import llms
from request_context import RequestContext, context_var
from utils.tag_extraction import extract_tags
from utils.add_message_to_queue import add_message_to_queue

logger = logging.getLogger("app")

prompt_crafter_chain = LLMChain(llm=llms["gpt4o"]["llm"], prompt=prompt_crafter_prompt)


async def agent_stream(input: str, agent: AgentExecutor, queue: Queue):
    request_context: RequestContext = context_var.get()
    out = await agent.ainvoke({"input": input})
    print('--------agent out-------: ', out)
    try:
        with get_openai_callback() as cb:
            output = await agent.ainvoke({"input": input})
    except OutputParserException as e:
        logger.error(f"Output parser error: {e}")
        await add_message_to_queue(
            json.dumps(
                {
                    "error": f"output_parse_exception",
                    "error_description": "The agent failed to parse intermediate steps",
                }
            ),
            queue,
        )
        await add_message_to_queue("<end_of_stream>", queue)
        return
    except openai.RateLimitError as e:
        logger.error(f"OpenAI rate limit error: {e}")

        await add_message_to_queue(
            json.dumps(
                {
                    "error": "rate_limit",
                    "error_description": e.message,
                }
            ),
            queue,
        )
        await add_message_to_queue("<end_of_stream>", queue)
        return
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        await add_message_to_queue(
            json.dumps(
                {
                    "error": "internal_server_error",
                    "error_description": "Something went wrong when processing your message",
                }
            ),
            queue,
        )
        await add_message_to_queue("<end_of_stream>", queue)
        return

    await add_message_to_queue(
        json.dumps(
            {
                "message_type": "agent_output",
                "message": output["output"],
            }
        ),
        queue,
    )
    await add_message_to_queue("<end_of_stream>", queue)
