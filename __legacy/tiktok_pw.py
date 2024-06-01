import asyncio
import json
import platform
import random

from playwright.async_api import async_playwright
from pw_phones import phones_arr

os_name = platform.system()
HEADLESS = False if os_name=='Windows' else True


proxy_server = "http://geo.iproyal.com:12321"
proxy_name = 'ipuserm94'
proxy_pass = 'Pba1F7_country-nl' # _country-{country}

msToken="kWAM8FmtQBcUbCBd1Mu1JReYrNpKL1OWMkLuYCVSbv3rWDo-UhRD9ViOKKyJ9PntnrydvG2jFVvsukex6BYHOX-iFC0Fzg5CfcADftcBwAi9omXe1NtnhSQuP2S2J5zkBcdZfGGQPFvNsGH3"
X_Bogus="DFSzswSO7whANjtItOFHy09WcBnw"
signature='_02B4Z6wo00001qEnEjAAAIDCoScSMMHtoeKhBx6AAM1j95'

def diver_list(arr, in_one = 7):
    dived_urls = [[]]
    len_arr = len(arr[:25*in_one])
    for i, u in enumerate(arr[:25*in_one], start=1):
        dived_urls[-1].append(u)
        if len(dived_urls[-1])==in_one and i < len_arr: dived_urls.append([])
    return dived_urls

async def getPWLinks(music_id, cursors):
    track_id = music_id.split('-')[-1]
    API_URL =  "https://www.tiktok.com/api/music/item_list/"
    TMP_URL = 'https://www.tiktok.com/api/music/item_list/?aid=1988&app_language=ru-RU&app_name=tiktok_web&browser_language=ru-RU&browser_name=Mozilla' \
              '&browser_online=true&browser_platform=Win32&browser_version=5.0%20%28Linux%3B%20Android%2011%3B%20Pixel%204a%20%285G%29%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F117.0.5938.62%20Mobile%20Safari%2F537.36' \
              '&channel=tiktok_web&cookie_enabled=true&count=30' \
              '&cursor={}&device_id=7291305770762356257&device_platform=web_mobile&focus_state=true&from_page=music&history_len=2&is_fullscreen=false&is_page_visible=true&language=ru-RU' \
              '&musicID={}&os=android&priority_region=&referer=&region=NL&screen_height=765&screen_width=412&tz_name=Europe%2FMoscow&webcast_language=ru-RU&msToken=uVo99OpprkHaCblb93wClXXkndZbNebQuRJw2oV1nvtiDUliPAMw3GnYjuSdMDRtc1qh5K5HddSUNJQpaNjOKpB5vYiJzmiQyZbBWcLCzzM2R_JmwltU0zBNLFbkns_E9VZtFoh3fpmkUBLv1Q==&X-Bogus=DFSzswSOytXAN9VetTuYfz9WcBJs&_signature=_02B4Z6wo00001FDSzLwAAIDAUNLMvzpeUNxQ8oAAAHEid3'
    #'https://www.tiktok.com/api/music/item_list/?aid=1988&app_language=ru-RU&app_name=tiktok_web&browser_language=ru-RU&browser_name=Mozilla&browser_online=true&browser_platform=Win32&browser_version=5.0%20%28Linux%3B%20Android%2011%3B%20Pixel%205%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F90.0.4430.91%20Mobile%20Safari%2F537.36&channel=tiktok_web&cookie_enabled=true&count=30&cursor=0&device_id=7289951420127856161&device_platform=web_mobile&focus_state=true&from_page=music&history_len=2&is_fullscreen=false&is_page_visible=true&language=ru-RU&musicID=7197505126058330114&os=android&priority_region=&referer=&region=NL&screen_height=851&screen_width=393&tz_name=Europe%2FMoscow&verifyFp=verify_lnsxfhms_yHqeSRTa_dagL_4MFC_9IBy_bbMu5iYn28iM&webcast_language=ru-RU&msToken=m3JwC3Fdh4fKbW4stZEhTPu1USSj2eygB4w8P_K3thCumTi0H84L_PjukFJdCKb2_nhQj1DLA9ANCJR69deK7TgSxZT8JADpZ9BauNhp8tvHx-ykruvENpDIBahGQJEJ4Jk8RdQpUPo5rYueYQ==&X-Bogus=DFSzswSOXnGANr0EtTuo2U9WcBjU&_signature=_02B4Z6wo00001cJNb1AAAIDBwk1vUIie8o3CbWPAABW-9f'
    urls_arr = [TMP_URL.format(cursor, track_id) for cursor in cursors]

    async with async_playwright() as p:
        tasks = []
        dived_urls = diver_list(urls_arr, 7)
        for i, ut in enumerate(dived_urls,start=1):
            tasks.append(asyncio.create_task(request_pw_arr(pw=p, urls = ut, i = i)))
        result = await asyncio.gather(*tasks)

        #saveFileJSON('tiktol_pw_result.json', result)

    onelvl_arr = []
    for row in result:
        for task in row:
            onelvl_arr.append(parse_tiktok_data(music_id = music_id, dat = task))

    return onelvl_arr

def parse_tiktok_data(music_id, dat):
    res = {
        'header': {'source': 'tiktok'},
        'items' : [],
        #'cursor': cursor
    }

    if dat.get('itemList') is None:
        res['err'] = 'No itemList'
        print(f"{dat}")
        return res

    res['header']['music_id'] = music_id
    res['header']['name'] = dat['itemList'][0]['music'].get('title')

    try:
        for d in dat['itemList']:
            uniqueId = d['author'].get('uniqueId')
            video_id = d.get('id')

            res['items'].append({
                'link': f"{video_id}@{uniqueId}",
                'upload':d.get('createTime'),
                'duration': d['video'].get('duration'),
                'views': d['stats'].get('playCount'),
                'likes': d['stats'].get('diggCount'),
                'comments': d['stats'].get('commentCount'),
                'resend': d['stats'].get('shareCount'),
                'saves': d['stats'].get('collectCount'),
            })

    except Exception as ex:
        res['err'] = f"FROM parse_tiktok_data {ex}"

    return res

async def request_pw_arr(pw, urls, i):
    #print(f"request_pw_arr\n{urls=}")
    rnd_phone = random.choice(phones_arr)
    phone = pw.devices[rnd_phone]
    print(f"{i}. {rnd_phone}")
    browser = await pw.chromium.launch(
                #proxy={"server": proxy_server,'username': proxy_name,'password': proxy_pass},
                                       headless=HEADLESS,
                                       )
    context = await browser.new_context(**phone)
    page = await context.new_page()
    #await page.goto('https://www.tiktok.com/music/City-7197505126058330114',wait_until='domcontentloaded')  # "commit", "domcontentloaded", "load", "networkidle"

    page_api = await context.new_page()
    res_all = []

    for ui, url in enumerate(urls, start=1):
        try:
            #await page_api.goto('https://www.tiktok.com/api/music/item_list/?aid=1988&app_language=ru-RU&app_name=tiktok_web&browser_language=ru-RU&browser_name=Mozilla&browser_online=true&browser_platform=Win32&browser_version=5.0%20%28Linux%3B%20Android%2011%3B%20Pixel%204a%20%285G%29%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F117.0.5938.62%20Mobile%20Safari%2F537.36&channel=tiktok_web&cookie_enabled=true&count=30&cursor=0&device_id=7291305770762356257&device_platform=web_mobile&focus_state=true&from_page=music&history_len=2&is_fullscreen=false&is_page_visible=true&language=ru-RU&musicID=7197505126058330114&os=android&priority_region=&referer=&region=NL&screen_height=765&screen_width=412&tz_name=Europe%2FMoscow&webcast_language=ru-RU&msToken=uVo99OpprkHaCblb93wClXXkndZbNebQuRJw2oV1nvtiDUliPAMw3GnYjuSdMDRtc1qh5K5HddSUNJQpaNjOKpB5vYiJzmiQyZbBWcLCzzM2R_JmwltU0zBNLFbkns_E9VZtFoh3fpmkUBLv1Q==&X-Bogus=DFSzswSOytXAN9VetTuYfz9WcBJs&_signature=_02B4Z6wo00001FDSzLwAAIDAUNLMvzpeUNxQ8oAAAHEid3')
            await page_api.goto(url)
            #await asyncio.sleep(3000)
        except Exception as ex:
            print(f"DONT LOADED\n{ex}")
            return res_all
        try :
            cont = json.loads(await page_api.text_content('pre'))
        except Exception as ex:
            print(f"DONT JSONed\n{ex}")
            return res_all
        #saveFileJSON(f"TMP_PW_{i}_{ui}.json", cont)
        res_all.append(cont)

    return res_all

def genCursors(music_id):
    total_rows = 10000
    DIVER = random.randint(a=15, b=25)
    start_num = 0
    rows = 5000
    if total_rows > 3000:
        start_num = random.randint(a=0, b=4500)
        rows = random.randint(a=1000, b=1500)
        if start_num + rows > 5000: rows = 5000 - start_num

    #rows = 50
    col_pages = int(rows) // DIVER
    cursors = [str(start_num + cc * DIVER) for cc in range(col_pages)]
    print(f"CURSORS [ {total_rows} ] {music_id} : {start_num} + {rows} = {start_num + rows} {DIVER=} {col_pages=}")

    return rows, cursors

async def startTikTokParser(music_list=None):
    tracks = ['Scary-Garry-6914598970259490818']
    #result = []
    total = {}
    for i, music_id in enumerate(tracks, start=1):
        url = f"https://www.tiktok.com/music/{music_id}"
        rows, cursors = genCursors(music_id)
        print(f"{i:02}. {url=}")
        res = await getPWLinks(music_id, cursors)
        for r in res :
            if total.get(music_id) is None : total[music_id] = 0
            print(f"total[{music_id}] = {total[music_id]}")

        #saveFileJSON('tiktok_parsed_result.json', res)
        #result.extend(res)

    return total

async def main():
    while True:
        tg_rep = await startTikTokParser()
        tg_str = "Результаты сбора по ТикТок:"
        total = 0
        for music_id, col in tg_rep.items():
            tg_str += f"\n{music_id} : {col}"
            total+=col
        tg_str += f"\nИтого: {total}"

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
