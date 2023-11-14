import asyncio
import logging
from json import JSONDecodeError
from urllib.parse import urlencode

import aiohttp
import httpx
import requests

logger = logging.getLogger(__name__)

CONSTANT_USER_API_URL = (
    "https://www.tiktok.com/api/post/item_list/?aid=1988&app_language=en&app_name=tiktok_web&battery_info=1&browser_language=en-US&browser_name=Mozilla&browser_online=true&browser_platform=Win32&browser_version=5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F107.0.0.0%20Safari%2F537.36%20Edg%2F107.0.1418.56&channel=tiktok_web&cookie_enabled=true&device_id=7165118680723998214&device_platform=web_pc&focus_state=true&from_page=user&history_len=3&is_fullscreen=false&is_page_visible=true&os=windows&priority_region=RO&referer=&region=RO&screen_height=1440&screen_width=2560&tz_name=Europe%2FBucharest&webcast_language=en&msToken=G3C-3f8JVeDj9OTvvxfaJ_NppXWzVflwP1dOclpUOmAv4WmejB8kFwndJufXBBrXbeWNqzJgL8iF5zn33da-ZlDihRoWRjh_TDSuAgqSGAu1-4u2YlvCATAM2jl2J1dwNPf0_fk9dx1gJxQ21S0=&X-Bogus=DFSzswVYxTUANS/JS8OTqsXyYJUo&_signature=_02B4Z6wo00001CoOkNwAAIDBCa--cQz5e0wqDpRAAGoE8f"
).replace("\n", "").replace(" ", "")
NODE_URL = 'http://localhost/signature'
# SEC_UID = 'MS4wLjABAAAArUev1Z6Bg_FAs6xIzkgOdYJESLJsN_g7ho-2qrxsXbtHMBzmjO9GcBozJvX0Jb1V'
SEC_UID = 'MS4wLjABAAAAGgU83ADd2PeKM1Lj73jdNsl04aIThUBOwcBbkVDb1a0_Pny-uGFKSUSB3R0jTcs8'

async def scrape_page(cursor: int):
    params = {
        "aid": "1988",
        "count": 30,
        "secUid": SEC_UID,
        "cursor": cursor,
        "cookie_enabled": "true",
        "screen_width": 0,
        "screen_height": 0,
        "browser_language": "",
        "browser_platform": "",
        "browser_name": "",
        "browser_version": "",
        "browser_online": "",
        "timezone_name": "Europe/London",
    }
    fake_url = f"https://m.tiktok.com/api/post/item_list/?" + urlencode(params)
    response = requests.post(NODE_URL, headers={'Content-type': 'application/json'}, data=fake_url)
    try:
        data = response.json()
    except JSONDecodeError:
        logger.error('Error in the response from the internal service (signer)')
        return
    if not (tt_params := data.get('data', {}).get('x-tt-params')):
        logger.error(f'tt_params not in {data}')
        return
    headers = {
        "x-tt-params": tt_params,
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56",
    }
    response = httpx.get(
        url=CONSTANT_USER_API_URL,
        headers=headers,
    )
    try:
        print(response.json())
    except JSONDecodeError:
        print('Когда ты блядь уже заработаешь :(')


# async def check_proxy(results, available_timeout):
#     prep = f"https://186.121.235.66:8080"
#     async with aiohttp.ClientSession() as client:
#         try:
#             response = await client.get('https://httpbin.org/get', timeout=available_timeout, proxy=prep)
#             assert response.status == 200
#         except Exception as e:
#             print(e)
#             return
#         results.append(prep)
#     return results

asyncio.run(
    scrape_page(
        cursor=0,
    )
)
