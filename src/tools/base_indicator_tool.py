import json
import logging
from typing import Any, Dict, Literal, Optional, Type
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
)
import aiohttp
from pydantic import BaseModel
from langchain.tools import BaseTool
from request_context import RequestContext, context_var
from utils.add_message_to_queue import add_message_to_queue
from aiohttp import BasicAuth

logger = logging.getLogger("app")


class BaseIndicatorTool(BaseTool):
    name: str
    description: str
    args_schema: Type[BaseModel]
    metadata: Dict[str, Any]

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        indicator: str,
        short_name: str,
        tool_name: str,
        description: str,
        args_schema: Type[BaseModel],
        output_fields: dict,
        asset_class: Literal["CRYPTO", "STOCK", "FOREX", "COMMODITY"],
        asset_type: str,
    ):
        super().__init__(
            name=tool_name,
            description=description,
            args_schema=args_schema,
            metadata={
                "indicator": indicator,
                "short_name": short_name,
                "output_fields": output_fields,
                "asset_class": asset_class,
                "asset_type": asset_type,
            },
        )

    def _run(self) -> str:
        raise Exception("This tool cannot run synchronously")

    async def fetch(self, validated_args):
        base_url = f"https://backbone-ta-handler-staging-1.wiseone.ai/taapi/{self.metadata['indicator']}"
        logger.debug(f"Base url: {base_url}")
        query_params = {}
        for key, value in validated_args.dict().items():
            if value is not None:
                query_params[key] = str(value)

        query_params["addResultTimestamp"] = "True"
        query_params["assetClass"] = self.metadata["asset_class"]
        query_params["assetType"] = self.metadata["asset_type"]
        logger.debug(f"Query params: {query_params}")

        async with aiohttp.ClientSession() as session:
            auth = BasicAuth(
                login="system", password="9c0ac5086e912a5c383bca191bb8f62c"
            )
            response = await session.get(base_url, params=query_params, auth=auth)
            return await response.json()

    def parse_response(self, output: dict) -> str:
        text_output = ""
        if "errors" in output:
            text_output = f"Error: {output['errors']}"
            return text_output
        for key, value in output.items():
            field_name = self.metadata["output_fields"][key]["name"]
            text_output += f"{field_name}: {value}\n"

        return text_output

    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Dict[str, Any],
    ) -> str:
        """Use the tool asynchronously."""
        validated_args = self.args_schema(**kwargs)

        logger.debug(f"Validated args: {validated_args}")

        request_context: RequestContext = context_var.get()
        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_init",
                        "message": f"Using {self.metadata['short_name']}...",
                    }
                ),
                request_context.message_queue,
            )

        response = await self.fetch(validated_args)
        logger.debug(f"Response: {response}")
        logger.debug(response)
        if request_context.message_queue != None:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_output",
                        "message": {
                            "indicator": self.metadata["indicator"],
                            "result": response,
                        },
                    }
                ),
                request_context.message_queue,
            )

        output = self.parse_response(response)
        logger.debug(f"Output: {output}")
        return output
