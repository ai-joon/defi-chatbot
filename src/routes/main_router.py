from fastapi import APIRouter
from routes.prompt import router


main_router = APIRouter(prefix="/api/v1")

main_router.include_router(router)
