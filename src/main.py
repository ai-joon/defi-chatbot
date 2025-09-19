import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import yaml

from request_context import RequestContext, context_var
from routes.main_router import main_router
with open("logging-config.yml", "r") as f:
    logging_config = yaml.safe_load(f.read())

logging.config.dictConfig(logging_config)
logger = logging.getLogger("app")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_creation(request: Request, call_next):
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    request_context = RequestContext()
    request_context.timezone = request.headers.get("Timezone")

    token = context_var.set(request_context)
    response = await call_next(request)
    context_var.reset(token)
    return response


app.include_router(main_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8020, log_level="info")
