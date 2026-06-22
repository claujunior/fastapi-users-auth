from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from auth.token_handler import verify_token
from services import mal_service

router = APIRouter(tags=["MAL"])


class ListUpdate(BaseModel):
    status: Optional[str] = None
    score: Optional[int] = None
    num_watched_episodes: Optional[int] = None


@router.get("/auth/mal/start")
async def mal_start(data=Depends(verify_token)):
    auth_url = await mal_service.build_authorize_url(data["sub"])
    return {"auth_url": auth_url}


@router.get("/auth/mal/callback")
async def mal_callback(code: str, state: str):
    frontend = await mal_service.handle_callback(code, state)
    return RedirectResponse(f"{frontend}/#perfil")


@router.get("/me/mal")
async def mal_status(data=Depends(verify_token)):
    return await mal_service.connection_status(data["sub"])


@router.delete("/me/mal")
async def mal_disconnect(data=Depends(verify_token)):
    return await mal_service.disconnect(data["sub"])


@router.get("/me/animelist")
async def my_animelist(status: Optional[str] = None, data=Depends(verify_token)):
    return await mal_service.get_animelist(data["sub"], status)


@router.patch("/me/animelist/{anime_id}")
async def update_my_list(anime_id: int, body: ListUpdate, data=Depends(verify_token)):
    return await mal_service.update_list(data["sub"], anime_id, body.model_dump())


@router.delete("/me/animelist/{anime_id}")
async def remove_my_list(anime_id: int, data=Depends(verify_token)):
    return await mal_service.remove_from_list(data["sub"], anime_id)
