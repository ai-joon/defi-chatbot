import os
import yaml
from typing import Any, Dict, List, Type
from pydantic import BaseModel, Field, create_model
from langchain.tools import BaseTool
from tools.base_indicator_tool import BaseIndicatorTool
from typing import Literal


# Define a base schema dynamically
def create_tool_schema(
    indicator_config: Dict[str, Any], parent_config: Dict[str, Any]
) -> Type[BaseModel]:
    fields = {}
    indicator = indicator_config["indicator"]
    parent_params = parent_config["parameters"]
    combined_params = {**parent_params, **indicator["parameters"]}

    for param, param_config in combined_params.items():
        field_type = eval(param_config["type"])

        if param_config.get("required", False):
            # Required field (no default)
            fields[param] = (
                field_type,
                Field(..., description=param_config["description"]),
            )
        else:
            # Optional field with default
            fields[param] = (
                field_type,
                Field(
                    default=param_config.get("default", None),
                    description=param_config["description"],
                ),
            )

    # Use pydantic's create_model function to dynamically create the model
    return create_model(f"{indicator['shortName']}Schema", __base__=BaseModel, **fields)


def load_tools(
    indicator_dir: str,
    parent_config_config_path: str,
    asset_class: Literal["CRYPTO", "STOCK", "FOREX", "COMMODITY"],
    asset_type: Literal["CEX", "DEX", "DEFAULT"],
) -> List[BaseTool]:
    parent_config = yaml.safe_load(open(parent_config_config_path, "r").read())

    tools = []

    for filename in os.listdir(indicator_dir):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            file_path = os.path.join(indicator_dir, filename)
            with open(file_path, "r") as file:
                try:
                    indicator_config = yaml.safe_load(file)
                    indicator = indicator_config["indicator"]
                    IndicatorSchema = create_tool_schema(
                        indicator_config, parent_config
                    )
                    tool = BaseIndicatorTool(
                        indicator["key"],
                        indicator["shortName"],
                        f"{indicator['key']}_tool",
                        indicator.get("description", ''),
                        IndicatorSchema,
                        indicator["responseValues"],
                        asset_class,
                        asset_type,
                    )
                    tools.append(tool)

                except yaml.YAMLError as e:
                    print(f"Error loading {filename}: {e}")

    return tools


if __name__ == "__main__":
    from langchain.agents import initialize_agent
    from langchain.agents import AgentType
    from llms import llms
    from request_context import RequestContext, context_var
    import asyncio
    import logging
    import logging.config

    with open("../logging-config.yml", "r") as f:
        logging_config = yaml.safe_load(f.read())

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger("app")
    crypto_cex_config = yaml.safe_load(
        open("ta_config/crypto_cex_config.yaml", "r").read()
    )
    rsi_config = yaml.safe_load(open("ta_config/indicator_config/rsi.yaml", "r").read())
    indicator = rsi_config["indicator"]
    RSISchema = create_tool_schema(rsi_config, crypto_cex_config)
    tool = BaseIndicatorTool(
        indicator["key"],
        indicator["shortName"],
        f"{indicator['key']}_tool",
        indicator["description"],
        RSISchema,
        indicator["responseValues"],
        "CRYPTO",
        "DEX",
    )

    async def main():
        request_context = RequestContext()
        request_context.timezone = "America/Edmonton"
        token = context_var.set(request_context)

        agent = initialize_agent(
            [tool],
            llm=llms["gpt4o"]["llm"],
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
        )
        print(await agent.arun("Can you give me the 1h rsi of doge against usdt?"))

    asyncio.run(main())
