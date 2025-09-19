import asyncio
import json
from typing import Dict, Optional, Type
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
from langchain.agents import AgentType
import aiohttp
import requests
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from queue import Queue

from llms import llms
from constants import DEXANI_HEADERS, DEXANI_URL
from request_context import RequestContext, context_var
from utils.add_message_to_queue import add_message_to_queue


class SearchSchema(BaseModel):
    address: str = Field(description="Contract address for a cryptocurrency token")


class DexaniTool(BaseTool):
    name = "dexani_tool"
    description = """Useful for retreiving a security report for a cryptocurrecy token from it's contract address. Only capable of handling one token at a time"""
    args_schema: Type[BaseModel] = SearchSchema

    def _run(self) -> str:
        raise Exception("This tool cannot run synchronously")

    async def _arun(
        self,
        address: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        request_context: RequestContext = context_var.get()

        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_init",
                        "message": f"Using Dexani tool...",
                    }
                ),
                request_context.message_queue,
            )
        res = await dexani_req_async(address)
        if "error" in res:
            return res["error"]

        report = dexani_output_to_readable(res)

        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_output",
                        "message": {"tool": "dexani", "result": res},
                    }
                ),
                request_context.message_queue,
            )

        return f"Here is a security report for the token address {address}: \n\n {report} \n\n The user will receive this information, so please only provide a simple explanation when responding to the user asking for this information"


def dexani_req(address: str):
    url = f"{DEXANI_URL}?address={address}"
    res = requests.get(url, headers=DEXANI_HEADERS)
    res_json = res.json()
    return res_json


async def dexani_req_async(address: str):
    url = f"{DEXANI_URL}?address={address}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            res_json = await res.json()
            return res_json


def dexani_output_to_readable(dexani_json: Dict):
    token_details = dexani_json["Token Information"]["Token Details"]
    security_report = dexani_json["Token Information"]["Security Report"]

    output_text = ""
    output_text += f"Token Name: {token_details['Name']} \n"
    output_text += f"Token Symbol: {token_details['Symbol']} \n"
    output_text += "\n"
    output_text += "Security Report: \n"
    for check in security_report.keys():
        output_text += f"Check Name: {security_report[check]['title']} \n"
        match (security_report[check]["level"]):
            case 0:
                output_text += f"Level: Check \n"
            case 1:
                output_text += f"Level: Notice \n"
            case 2:
                output_text += f"Level: Warning \n"
            case 3:
                output_text += f"Level: Critcal Risk \n"
        output_text += f"Description: {security_report[check]['description']} \n\n"
    return output_text


if __name__ == "__main__":
    from langchain.agents import initialize_agent

    async def main():
        # res = await dexani_req_async("0xa11d6e01599854a4031008e03f2a0e0b773e94ab")
        tools = [DexaniTool()]

        agent = initialize_agent(
            llm=llms["chatgpt16k"]["llm"],
            tools=tools,
            verbose=True,
            agent=AgentType.OPENAI_FUNCTIONS,
            handle_parsing_errors="Check your output and make sure it conforms!",
            max_iterations=10,
        )

        print(
            await agent.arun(
                "Can you give me a security report for the contrast address 0xa11d6e01599854a4031008e03f2a0e0b773e94ab?"
            )
        )

    asyncio.run(main())
