from typing import Annotated

from fastapi import APIRouter, Query
from services.anime_service import animes_recente,search_animes,search_id
router = APIRouter(
    prefix="/anime",
    tags=["Animes"]
)

@router.get("")
async def animes_recentes(page: Annotated[int, Query(ge=1)] = 1):
    return await animes_recente(page)

@router.get("/search")
async def search_anime(search: str):
    return await search_animes(search)
    
@router.get("/{id}")
async def searchId(id : int):
    return await search_id(id)