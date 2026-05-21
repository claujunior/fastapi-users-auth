from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from routers.anime_router import router as anime_router
from routers.user_router import router as user_router
from fastapi.middleware.cors import CORSMiddleware
from exceptions.handler import (
    http_exception_handler
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    HTTPException,
    http_exception_handler
)


app.include_router(user_router)
app.include_router(anime_router)

