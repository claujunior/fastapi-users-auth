
from anipy_api.provider.providers import AllAnimeProvider
from anipy_api.provider import LanguageTypeEnum
from anipy_api.player import get_player
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("MAL_CLIENT_ID")


provider = AllAnimeProvider(base_url_override=None)


results = provider.get_search("Naruto")

anime = results[0]

# 2. episódios corretos
episodes = provider.get_episodes(
    anime.identifier,
    LanguageTypeEnum.SUB
)

def get_users():
    for ep in episodes:
        streams = provider.get_video(
            anime.identifier,
            ep,
            LanguageTypeEnum.SUB
        )

        if not streams:
            continue

        best_stream = max(streams, key=lambda s: s.resolution)
        print(ep, best_stream.url)

get_users()



        