from anipy_api.provider.providers import AllAnimeProvider
from anipy_api.provider import LanguageTypeEnum
from anipy_api.mal import MyAnimeList,MyAnimeListAdapter,MALAnime,MALMediaTypeEnum

mal = MyAnimeList(
    client_id="9d3de26134abfa6109b3e81d0cf3e3a7"
)
provider = AllAnimeProvider()
adapter = MyAnimeListAdapter(mal, provider)

anime = MALAnime(id=22319,title="Tokyo Ghoul",media_type=MALMediaTypeEnum.TV,num_episodes=0)

anime2 = adapter.from_myanimelist(
    anime
)
eps=provider.get_episodes(anime2.identifier,LanguageTypeEnum.SUB)
for ep in eps:
    print("Episódio:", ep)

    videos = provider.get_video(
        anime2.identifier,
        ep,
        LanguageTypeEnum.SUB
    )

    print(videos)
