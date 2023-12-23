from typing import List, Dict, Any

import aiohttp

from src.config import config


def is_playlist(url: str):
    return url.split("?")[1].startswith('list')


async def get_playlist_items_page(
        playlist_id: str,
        page_token: str = None,
        max_results: int = 50,
        api_key: str = config.general.youtube_token
) -> Dict[str, Any]:
    """
    :param playlist_id: youtube playlist id, list parameter in url
    :param page_token: there can be max 50 items per request, so items are
     spits into several pages. Response for every page consists page token for the next end previous one
    :param max_results: max items per page
    :param api_key: youtube api key
    :return: json response as dict
    """
    url: str = "https://youtube.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "contentDetails",
        "maxResults": max_results,
        "playlistId": playlist_id,
        "key": api_key
    }
    if page_token:
        params["pageToken"] = page_token

    url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

    headers = {
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, headers=headers, compress=True) as response:
            if response.status == 200:
                json_response = await response.json()
                return json_response
            else:
                error_message = await response.text()
                raise Exception(f"API request failed with status {response.status}. Error message: {error_message}")


async def get_playlist_items(
        playlist_url: str,
        max_results: int = 50,
        api_key: str = config.general.youtube_token
) -> List[str]:
    """
    :param playlist_url: youtube playlist url
    :param max_results: max items per page
    :param api_key: youtube api key
    :return: list of video urls
    """
    playlist_id: str = playlist_url.split("=")[1]
    items: List[str] = []
    res = await get_playlist_items_page(playlist_id,
                                        max_results=max_results,
                                        api_key=api_key)
    items.extend(res["items"])
    num_pages = res['pageInfo']['totalResults'] // res['pageInfo']['resultsPerPage']
    for _ in range(num_pages):
        next_page_token = res["nextPageToken"]
        res = await get_playlist_items_page(playlist_id,
                                            page_token=next_page_token,
                                            max_results=max_results,
                                            api_key=api_key)
        items.extend(res["items"])

    return list(map(lambda x: f"https://www.youtube.com/watch?v={x['contentDetails']['videoId']}", items))
