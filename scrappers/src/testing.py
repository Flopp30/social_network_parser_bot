import asyncio
import logging
from json import JSONDecodeError
from urllib.parse import urlencode

import aiohttp
import requests

logger = logging.getLogger(__name__)

CONSTANT_MUSIC_API_URL = """
     https://m.tiktok.com/api/music/item_list/
     ?aid=1988&app_language=en
     &app_name=tiktok_web
     &battery_info=1
     &browser_language=en-US
     &browser_name=Mozilla
     &browser_online=true
     &browser_platform=Win32
     &browser_version=5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F101.0.4951.64%20Safari%2F537.36%20Edg%2F101.0.1210.53
     &channel=tiktok_web
     &cookie_enabled=true
     &device_id=7002566096994190854
     &device_platform=web_pc&focus_state=false
     &from_page=music&history_len=1
     &is_fullscreen=false&is_page_visible=true&os=windows
     &priority_region=RO&referer=&region=RO
     &screen_height=1080
     &screen_width=1920
     &tz_name=Europe%2FBucharest
     &verifyFp=verify_dca8729afe5c502257ed30b0b070dbdb
     &webcast_language=en
     &msToken=K8Xf-t_4RZ5n27zHsUPRyDIjpHQtfPeuHSvtbWzz0D0CQkX1UEyEdV0Xgx5BdbFPqKZ2McVCdlo1RM_u3o9FRglKoFa7TLZz2Yhd_fYRgWKhQDAq1TxQwLSTCz7Jp-EzVhopdNFO
     &X-Bogus=DFSzswVOLbUANCTQSwQvy2XyYJAm
     &_signature=_02B4Z6wo00001S9DBBwAAIDADOIqsG3-iK0vQwCAAClJd0
    """.replace("\n", "").replace(" ", "")
NODE_URL = 'http://localhost/signature'
MUSIC_ID = 7034143722082192134


async def scrape_page(music_id: int, cursor: int, proxy: str):
    params = {
        "aid": "1988",
        "count": 30,
        "musicID": music_id,
        "cursor": 3000,
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
    fake_url = f"https://m.tiktok.com/api/music/item_list/?" + urlencode(params)
    response = requests.post(NODE_URL, headers={'Content-type': 'application/json'}, data=fake_url, verify=False)
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
    response = requests.get(
        url=CONSTANT_MUSIC_API_URL,
        headers=headers,
        proxies={
            "http": proxy,
            "https": proxy,
        },
        timeout=10
        # verify=False
    )
    # response = requests.get(CONSTANT_MUSIC_API_URL, headers=headers)
    try:
        print(response.json())
    except JSONDecodeError:
        print('Когда ты блядь уже заработаешь :(')


async def check_proxy(results, available_timeout):
    prep = f"https://186.121.235.66:8080"
    async with aiohttp.ClientSession() as client:
        try:
            response = await client.get('https://httpbin.org/get', timeout=available_timeout, proxy=prep)
            assert response.status == 200
        except Exception as e:
            print(e)
            return
        results.append(prep)
    return results

# print(asyncio.run(check_proxy([], 0)))

#
# proxies = []
# while len(proxies) < 6:
#     proxies = asyncio.run(get_proxies())
#     print(proxies)

asyncio.run(
    scrape_page(
        music_id=MUSIC_ID,
        cursor=0,
        proxy="8.219.74.58:6666",
    )
)
proxies = [
    "181.205.130.62:999"
]
# 181.205.130.62:999
# 190.242.181.59:999