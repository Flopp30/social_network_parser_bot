import aiohttp
import asyncio
import random
import time

from toolbox import saveFileJSON, openFileJSON, getLink
from pwee import dbSaveInstagram, getActiveTracks, dbSaveParseStat, countReelsByTrack
from tg_reporter import sendSyncReport

msToken = "kWAM8FmtQBcUbCBd1Mu1JReYrNpKL1OWMkLuYCVSbv3rWDo-UhRD9ViOKKyJ9PntnrydvG2jFVvsukex6BYHOX-iFC0Fzg5CfcADftcBwAi9omXe1NtnhSQuP2S2J5zkBcdZfGGQPFvNsGH3"
X_Bogus = "DFSzswSO7whANjtItOFHy09WcBnw"
signature = '_02B4Z6wo00001qEnEjAAAIDCoScSMMHtoeKhBx6AAM1j95'

cookies = {
    'tt_csrf_token': 'DuRsICAf-D7xIMBAasa6900xtbipY4f7hLaI',
    'tt_chain_token': 'SoQudvDidit51iGOmR3Ezw==',
    '__tea_cache_tokens_1988': '{%22_type_%22:%22default%22%2C%22user_unique_id%22:%227289951420127856161%22%2C%22timestamp%22:1697324095098}',
    'tiktok_webapp_theme': 'light',
    'odin_tt': 'f8dc33354b4a2aeba3652c0c0c3caff4fdbc8124c857bb2a36dfa4e0a34806716f2519b6d8d41467ef2da6a91a68412fa46b08ea14a42b22662d8cf262dd6378a253d9d79feb5c10fec15531b6258b93',
    'perf_feed_cache': '{%22expireTimestamp%22:1697493600000%2C%22itemIds%22:[%227282547030654782752%22%2C%227276792487140805893%22]}',
    'passport_csrf_token': '582a26364335641bdd3598172d5e0bfc',
    'passport_csrf_token_default': '582a26364335641bdd3598172d5e0bfc',
    's_v_web_id': 'verify_lnsxfhms_yHqeSRTa_dagL_4MFC_9IBy_bbMu5iYn28iM',
    'cookie-consent': '{%22ga%22:false%2C%22af%22:false%2C%22fbp%22:false%2C%22lip%22:false%2C%22bing%22:false%2C%22ttads%22:false%2C%22reddit%22:false%2C%22criteo%22:false%2C%22version%22:%22v9%22}',
    'ttwid': '1%7CmOwlKOGX_hzGTArKlHzCj8_CD7iS4qDwcuLcR1xwWcU%7C1697636865%7Cc3403a248c3ad20b929a3fa43a5e36524fef1ae3e1470a08683046ed4d441501',
    'msToken': 'm3JwC3Fdh4fKbW4stZEhTPu1USSj2eygB4w8P_K3thCumTi0H84L_PjukFJdCKb2_nhQj1DLA9ANCJR69deK7TgSxZT8JADpZ9BauNhp8tvHx-ykruvENpDIBahGQJEJ4Jk8RdQpUPo5rYueYQ==',
    'msToken': 'm3JwC3Fdh4fKbW4stZEhTPu1USSj2eygB4w8P_K3thCumTi0H84L_PjukFJdCKb2_nhQj1DLA9ANCJR69deK7TgSxZT8JADpZ9BauNhp8tvHx-ykruvENpDIBahGQJEJ4Jk8RdQpUPo5rYueYQ==',
}

headers = {
    'authority': 'www.tiktok.com',
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9',
    # 'cookie': 'tt_csrf_token=DuRsICAf-D7xIMBAasa6900xtbipY4f7hLaI; tt_chain_token=SoQudvDidit51iGOmR3Ezw==; __tea_cache_tokens_1988={%22_type_%22:%22default%22%2C%22user_unique_id%22:%227289951420127856161%22%2C%22timestamp%22:1697324095098}; tiktok_webapp_theme=light; odin_tt=f8dc33354b4a2aeba3652c0c0c3caff4fdbc8124c857bb2a36dfa4e0a34806716f2519b6d8d41467ef2da6a91a68412fa46b08ea14a42b22662d8cf262dd6378a253d9d79feb5c10fec15531b6258b93; perf_feed_cache={%22expireTimestamp%22:1697493600000%2C%22itemIds%22:[%227282547030654782752%22%2C%227276792487140805893%22]}; passport_csrf_token=582a26364335641bdd3598172d5e0bfc; passport_csrf_token_default=582a26364335641bdd3598172d5e0bfc; s_v_web_id=verify_lnsxfhms_yHqeSRTa_dagL_4MFC_9IBy_bbMu5iYn28iM; cookie-consent={%22ga%22:false%2C%22af%22:false%2C%22fbp%22:false%2C%22lip%22:false%2C%22bing%22:false%2C%22ttads%22:false%2C%22reddit%22:false%2C%22criteo%22:false%2C%22version%22:%22v9%22}; ttwid=1%7CmOwlKOGX_hzGTArKlHzCj8_CD7iS4qDwcuLcR1xwWcU%7C1697636865%7Cc3403a248c3ad20b929a3fa43a5e36524fef1ae3e1470a08683046ed4d441501; msToken=m3JwC3Fdh4fKbW4stZEhTPu1USSj2eygB4w8P_K3thCumTi0H84L_PjukFJdCKb2_nhQj1DLA9ANCJR69deK7TgSxZT8JADpZ9BauNhp8tvHx-ykruvENpDIBahGQJEJ4Jk8RdQpUPo5rYueYQ==; msToken=m3JwC3Fdh4fKbW4stZEhTPu1USSj2eygB4w8P_K3thCumTi0H84L_PjukFJdCKb2_nhQj1DLA9ANCJR69deK7TgSxZT8JADpZ9BauNhp8tvHx-ykruvENpDIBahGQJEJ4Jk8RdQpUPo5rYueYQ==',
    'dnt': '1',
    'referer': 'https://www.tiktok.com/music/City-7197505126058330114',
    'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
}


def parse_tiktok_data(url, cursor, dat):
    res = {
        'header': {'source': 'tiktok', },
        'items': [],
        'cursor': cursor
    }

    if dat.get('itemList') is None:
        res['err'] = 'No itemList'
        print(f"{dat}")
        return res

    res['header']['music_id'] = url.split('/music/')[-1].replace('/', '')
    res['header']['name'] = dat['itemList'][0]['music'].get('title')

    try:
        for d in dat['itemList']:
            uniqueId = d['author'].get('uniqueId')
            video_id = d.get('id')

            res['items'].append({
                'link': f"{video_id}@{uniqueId}",
                'upload': d.get('createTime'),
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


async def tiktok_request(url, cursor, pp=0):
    await asyncio.sleep(pp / 5)
    music_id = url.split('-')[-1].replace('/', '')
    # print(f"{int(time.time())} REQ [ {cursor} ] {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.tiktok.com/api/music/item_list/',
                               headers=headers,
                               cookies=cookies,
                               params={
                                   'aid': '1988',
                                   'app_language': 'ru-RU',
                                   'app_name': 'tiktok_web',
                                   'browser_language': 'ru-RU',
                                   'browser_name': 'Mozilla',
                                   'browser_online': 'true',
                                   'browser_platform': 'Win32',
                                   'browser_version': '5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
                                   'channel': 'tiktok_web',
                                   'cookie_enabled': 'true',
                                   'count': '30',
                                   'cursor': cursor,  # 'cursor': '60
                                   'device_id': '7289951420127856161',
                                   'device_platform': 'web_mobile',
                                   'focus_state': 'true',
                                   'from_page': 'music',
                                   'history_len': '1',
                                   'is_fullscreen': 'false',
                                   'is_page_visible': 'true',
                                   'language': 'ru-RU',
                                   'musicID': music_id,
                                   'os': 'ios',
                                   'priority_region': '',
                                   'referer': '',
                                   'region': 'RU',
                                   'screen_height': '844',
                                   'screen_width': '390',
                                   'tz_name': 'Europe/Moscow',
                                   'webcast_language': 'ru-RU',
                                   'msToken': msToken,
                                   'X-Bogus': X_Bogus,
                                   '_signature': signature,
                               }) as r:
            if r.status != 200:
                print(f"[ {r.status} ] ERR {cursor}")
                r.raise_for_status()
            try:
                app_details = await r.json()
                if app_details:
                    dat = parse_tiktok_data(url, cursor, app_details)
                else:
                    dat = {'err': 'app_details is None', 'cursor': cursor}
            except Exception as ex:
                print(f"ERR ASREQ: {ex}")
                dat = {'err': ex, 'cursor': cursor}
            return dat


def genCursors(music_id):
    total_rows = countReelsByTrack(music_id)
    DIVER = random.randint(a=15, b=25)
    start_num = 0
    rows = 5000

    if total_rows > 3000:
        start_num = random.randint(a=0, b=4500)
        rows = random.randint(a=1000, b=1500)
        if start_num + rows > 5000: rows = 5000 - start_num

    col_pages = int(rows) // DIVER
    cursors = [str(start_num + cc * DIVER) for cc in range(col_pages)]
    print(f"CURSORS [ {total_rows} ] {music_id} : {start_num} + {rows} = {start_num + rows} {DIVER=} {col_pages=}")
    return rows, cursors


async def TIKTOK_asreq(url, cursors):
    final_result = []
    attempt = 0
    while True:
        print(f"REQUEST #{attempt} : {len(cursors)} cursors")
        tasks = [asyncio.create_task(tiktok_request(url=url, cursor=cursor, pp=i)) for i, cursor in enumerate(cursors)]
        responses = await asyncio.gather(*tasks)
        cursors = []
        for r in responses:
            if r.get('err'):
                cursors.append(r['cursor'])
                print(r.get('err'))
            else:
                final_result.append(r)
        saveFileJSON('tik_tok_async.json', final_result)
        if len(cursors) == 0: break
        if attempt > 5: break
        attempt += 1
        await asyncio.sleep(3)

    # final_result = openFileJSON('tik_tok_async.json')
    res = {'header': final_result[0]['header'], 'items': []}
    uniq = []
    for r in final_result:
        for item in r['items']:
            music_id = item['link'].split('/')[-1]
            if music_id in uniq: continue
            uniq.append(music_id)
            res['items'].append(item)
    print(f"Total : {len(res['items'])}")
    return res


async def startTikTokParser(music_list=None):
    tracks = getActiveTracks(tip='tiktok', music_list=music_list)
    result = []
    for i, music_id in enumerate(tracks, start=1):
        url = f"https://www.tiktok.com/music/{music_id}"
        rows, cursors = genCursors(music_id)
        print(f"{i:02}. {url=}")
        res = await TIKTOK_asreq(url, cursors=cursors)
        if res.get('err') is None:
            new_col = dbSaveInstagram(res)
            print(f"\t{new_col=}")
            result.append({'music_id': music_id, 'plan': rows, 'fact': new_col})
            dbSaveParseStat(music_id, rows, new_col)
        else:
            print(f"TIKTOK STOP! {res.get('err')}")
            result.append({'music_id': music_id, 'plan': rows, 'fact': 0, 'err': res.get('err')})
    saveFileJSON('tik_tok_new_result.json', result)
    tg_rep = "<b>TikTok.</b> Результат сбора:"
    total_plan = 0
    total_fact = 0
    for r in result:
        # https://www.tiktok.com/music/POOR-7183091053677774850
        music_link = f"https://www.tiktok.com/music/{r['music_id']}"
        music_name = tracks.get(r['music_id']) if tracks.get(r['music_id']) else r['music_id']
        tg_rep += f"\n<b>{r['fact']}</b> / {r['plan']} {getLink(music_link, music_name)}"
        total_plan += r['plan']
        total_fact += r['fact']
    tg_rep += f"\n\nИтого новых : <b>{total_fact}</b> / {total_plan}"
    return tg_rep


async def main():
    while True:
        tg_rep = await startTikTokParser()
        sendSyncReport(text=tg_rep)
        await asyncio.sleep(60 * 60)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
