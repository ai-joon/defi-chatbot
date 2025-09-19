import json
import time
from typing import Literal, Optional, Type, Union
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
)
from langchain.agents import AgentType
import aiohttp
import requests
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from queue import Queue
from request_context import RequestContext, context_var

from constants import (
    ONE_DAY,
    ONE_HOUR,
    TAAPI_HEADERS,
    TAAPI_SECRET,
    TAAPI_URL,
    TWELVE_HOURS,
)
from llms import llms
from utils.add_message_to_queue import add_message_to_queue


class SearchSchema(BaseModel):
    indicator: Literal["rsi", "dmi", "macd"] = Field(
        description="A technical indicator used in the analysis of financial markets"
    )
    currency_code: Literal["BTC", "ETH", "LTC"] = Field(
        description="The currency code of the cryptocurrency that is being queried"
    )
    interval: Literal["15m", "30m", "1h", "12h", "1d", "1w"] = Field(
        description="Interval or time frame. So if you're interested in values on hourly candles, use interval=1h, for daily values use interval=1d, etc."
    )
    number_of_intervals_returned: int = Field(
        description="This controls how many intervals will be returned. MAXIMUM 15"
    )


class TaapiTool(BaseTool):
    name = "taapi_tool"
    description = """Useful for when you need to get information about current cryptocurrency indicators. Only capable of handling one coin at a time. Please note the maximum return values is 15."""
    args_schema: Type[BaseModel] = SearchSchema
    tool_verbosity: bool = False

    def _run(self) -> str:
        raise Exception("This tool cannot run synchronously")

    async def _arun(
        self,
        indicator: Union[Literal["rsi"], Literal["dmi"], Literal["macd"]],
        currency_code: Union[Literal["BTC"], Literal["ETH"], Literal["LTC"]],
        interval: Union[
            Literal["15m"],
            Literal["30m"],
            Literal["1h"],
            Literal["12h"],
            Literal["1d"],
            Literal["1w"],
        ],
        number_of_intervals_returned: int = 1,
        optional_parameter: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        request_context: RequestContext = context_var.get()
        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_init",
                        "message": f"Using Taapi tool to check {currency_code}'s {indicator.upper()}...",
                    }
                ),
                request_context.message_queue,
            )

        symbol = f"{currency_code}/USDT"
        res_dict = await taapi_req_async(
            indicator, symbol, interval, timepoints=number_of_intervals_returned
        )
        res_dict.reverse()
        current_time = time.time()
        match (interval):
            case "1h":
                labels = [
                    (current_time - (x * ONE_HOUR)) * 1000 for x in range(len(res_dict))
                ]
                timescale = "hour"
            case "12h":
                labels = [
                    (current_time - (x * TWELVE_HOURS)) * 1000
                    for x in range(len(res_dict))
                ]
                timescale = "day"
            case "1d":
                labels = [
                    (current_time - (x * ONE_DAY)) * 1000 for x in range(len(res_dict))
                ]
                timescale = "day"
            case _:
                labels = [x * 1000 for x in range(len(res_dict))]

        labels.reverse()
        if "errors" in res_dict:
            return res_dict["errors"]
        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_output",
                        "message": {
                            "tool": "taapi",
                            "indicator": indicator,
                            "result": res_dict,
                            "labels": labels,
                            "timescale": timescale,
                        },
                    }
                ),
                request_context.message_queue,
            )
        text = ""
        if len(res_dict) == 1:
            for key in res_dict[0]:
                text += f"{key}: {res_dict[0][key]} \n"
            return f"Here is the most recent {interval} {indicator} value for {symbol}: \n {text}. \n\n The user has just been provided a graph of the data above, so do not repeat any of the data. Only provide meaningful insights from the data."
        else:
            for i in range(len(res_dict)):
                for key in res_dict[i]:
                    text += f"{key}: {res_dict[i][key]} \n"
                text += "\n"
            return f"Here are the {number_of_intervals_returned} most recent {interval} {indicator} value for {symbol}: \n {text}. \n\n The user has just been provided a graph of the data above, so do not repeat any of the data. Only provide meaningful insights from the data."


def taapi_req(
    indicator: str,
    symbol: str,
    interval: str,
    timepoints: int,
    exchange="gateio",
):
    url = f"{TAAPI_URL}/{indicator}?secret={TAAPI_SECRET}&exchange={exchange}&symbol={symbol}&interval={interval}&backtracks={timepoints}"
    res = requests.get(url, headers=TAAPI_HEADERS)
    res_json = res.json()
    for key in res_json[0]:
        if type(res_json[key]) == float:
            res_json[key] = round(res_json[key], 2)
    return res_json[0]


async def taapi_req_async(
    indicator: str, symbol: str, interval: str, exchange="binance", timepoints: int = 1
):
    url = f"{TAAPI_URL}/{indicator}?secret={TAAPI_SECRET}&exchange={exchange}&symbol={symbol}&interval={interval}&backtracks={timepoints}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            res_json = await res.json()
            if "errors" in res_json:
                return res_json
            for i in range(len(res_json)):
                for key in res_json[i]:
                    if type(res_json[i][key]) == float:
                        res_json[i][key] = round(res_json[i][key], 2)
            return res_json


if __name__ == "__main__":
    from langchain.agents import initialize_agent

    agent_chain = initialize_agent(
        [TaapiTool()],
        llm=llms["chatgpt16k"]["llm"],
        agent=AgentType.AgentType.OPENAI_FUNCTIONS,
        verbose=True,
    )
