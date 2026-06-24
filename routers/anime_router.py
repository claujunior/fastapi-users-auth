from typing import Annotated
from services import anime_service
import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from services.anime_service import animes_recente, search_animes, search_id
from services.streaming import resolve_stream


async def _resolver_stream(id: int, ep: int, lang: str):
    detalhe = await search_id(id)
    title = detalhe.get("title")
    if not title:
        raise HTTPException(status_code=404, detail="Anime não encontrado")

    # anipy é síncrono -> roda fora do event loop
    stream = await run_in_threadpool(resolve_stream, title, ep, lang)
    if not stream:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível obter o stream deste episódio (provedor indisponível ou episódio sem fonte)",
        )
    return stream

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

@router.get("/{id}/episodes/{ep}/stream")
async def get_stream(id: int, ep: int, lang: str = "sub"):
    """Metadados do stream (resolução, tipo). O player usa pra decidir mp4/hls."""
    stream = await _resolver_stream(id, ep, lang)
    return {
        "resolution": stream["resolution"],
        "type": stream["type"],
        "provider_title": stream["provider_title"],
    }


@router.get("/{id}/episodes/{ep}/video")
async def proxy_video(id: int, ep: int, request: Request, lang: str = "sub"):
    """Proxy do vídeo: busca no host com o Referer correto (hotlink protection)
    e repassa os bytes pro navegador, encaminhando Range pra permitir seek."""
    stream = await _resolver_stream(id, ep, lang)

    fwd_headers = {}
    if stream.get("referrer"):
        fwd_headers["Referer"] = stream["referrer"]
    if request.headers.get("range"):
        fwd_headers["Range"] = request.headers["range"]

    client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=None))
    upstream = await client.send(
        client.build_request("GET", stream["url"], headers=fwd_headers),
        stream=True,
    )

    if upstream.status_code >= 400:
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(status_code=502, detail="Falha ao buscar o vídeo no provedor")

    passthrough = {}
    for h in ("content-length", "content-range"):
        if h in upstream.headers:
            passthrough[h] = upstream.headers[h]
    passthrough["accept-ranges"] = "bytes"
    content_type = "video/mp4" if stream["type"] == "mp4" else upstream.headers.get(
        "content-type", "application/octet-stream"
    )

    async def body():
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        body(),
        status_code=upstream.status_code,
        media_type=content_type,
        headers=passthrough,
    )
@router.get("/topanimes")
async def animes_top():
    return await anime_service.topanimes()

@router.get("/{id}")
async def searchId(id : int):
    return await search_id(id)

