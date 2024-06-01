# import asyncio
import time

import requests
from pwee import dbSaveInstagram, dbSaveParseStat, getActiveTracks
from tg_reporter import sendSyncReport
from toolbox import TM, getLink, openFileJSON, saveFileJSON


def get_insta_rapi(audio_id, endCursor):
    url = "https://instagram-data1.p.rapidapi.com/audio/feed"
    querystring = {"audio_id": audio_id}
    if endCursor is not None:
        if len(endCursor) > 10: querystring['end_cursor'] = endCursor

    headers = {
        "X-RapidAPI-Key": "5279821d40msh408620f208658b2p1342adjsnd8bcc63d351b",
        "X-RapidAPI-Host": "instagram-data1.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers, params=querystring)
    try:
        dat = response.json()
    except Exception as ex:
        dat = {'err': f"{ex}\n{response.status_code}\n{response.text}"}
    return dat


def rapi_limit():
    url = "https://p.rapidapi.com/account"
    headers = {
        "X-RapidAPI-Key": "5279821d40msh408620f208658b2p1342adjsnd8bcc63d351b",
        "X-RapidAPI-Host": "instagram-data1.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers)
    return response.json()

    pass


def prepareData(dat):
    # Можно обновлять в базе Channels
    res = {'header': {
        'total': dat['media_count'].get('clips_count', 0),
        'name': dat['metadata']['music_info']['music_asset_info'].get('title', 'NO TITLE'),
        'music_id': dat['metadata']['music_info']['music_asset_info']['audio_cluster_id'],
        'duration': dat['metadata']['music_info']['music_asset_info']['duration_in_ms'] // 1000,
    },
        'endCursor': dat.get('endCursor'),
        'items': [],
    }

    tt = {'code': 'link',
          'taken_at': 'upload',
          'video_duration': 'duration',
          'play_count': 'views',
          'like_count': 'likes',
          'comment_count': 'comments',
          }  # 'fb_like_count', 'fb_play_count'

    for d in dat['items']:
        m = d['media']
        desk = {v: int(m.get(k, 0)) if k != 'code' else m.get(k) for k, v in tt.items()}
        res['items'].append(desk)
    return res


def startInstagramParser(PGS=5):
    start_parse = time.time()
    tracks = getActiveTracks(tip='instagram')
    result = openFileJSON('instagram_new_result.json', no={})
    for i, music_id in enumerate(list(tracks.keys()), start=1):
        res = {}
        last_pg = 0
        if result.get(music_id) is None:
            result[music_id] = {'url': f"https://www.instagram.com/reels/audio/{music_id}", 'reqs': []}
        if len(result[music_id]['reqs']) > 0:
            res['endCursor'] = result[music_id]['reqs'][-1].get('endCursor')
            last_pg = result[music_id]['reqs'][-1].get('pg')
            result[music_id]['reqs'] = []
        if len(res.get('endCursor', '-')) > 5200: res['endCursor'] = ''
        total_new = 0
        for pg in range(last_pg, last_pg + PGS):
            print(f"\n[ {i:02} | {pg:02} ] [ {len(res.get('endCursor', '-'))} ] : start parse  INSTA_id : {music_id}")
            dat = get_insta_rapi(audio_id=music_id, endCursor=res.get('endCursor'))
            if 'took too long to respond' in dat.get('info', '') or dat.get('media_count') is None:
                print(f"ERR:\n{dat}")
                break
            elif dat['metadata'].get('music_info') is None:
                print(f"ERR:\n{dat}")
                if dat.get('endCursor'):
                    res = {'endCursor': dat.get('endCursor')}
                continue
            saveFileJSON('insta_parsed.json', dat)
            res = prepareData(dat)
            new_items = dbSaveInstagram(res)
            total_new += new_items
            result[music_id]['reqs'].append({'pg': pg, 'new_items': new_items, 'endCursor': res.get('endCursor')})
            saveFileJSON('instagram_new_result.json', result)
            print(f"\t{new_items=}")

    tg_rep = "<b>Instagram.</b> Результат сбора:"
    itog_sum = 0
    total_pgs = 0
    for music_id, el in result.items():
        if len(el['reqs']) == 0: continue
        col_str = [f"{pg['pg']:03}|{pg['new_items']}|{len(pg.get('endCursor', '-'))}" for pg in el['reqs']]
        total_sum = sum([pg['new_items'] for pg in el['reqs']])
        total_pgs += el['reqs'][-1]['pg']
        itog_sum += total_sum
        dbSaveParseStat(music_id, PGS * 11, total_sum)
        tg_rep += f"\n{getLink(el['url'], tracks.get(music_id, 'NO NAME..'))}\n<b>{total_sum}</b> : {', '.join(col_str)}"

    zapr = 2000 / 15000
    total_req = len(tracks) * PGS
    cost = zapr * total_req / itog_sum * 1000 if itog_sum > 0 else 999999999
    tg_rep += f"\nНовых строк: <b>{itog_sum}</b>\nЗапросов : <b>{total_req}</b>\nСебестоимость : <b>{cost:.2f}</b> руб. / 1К строк\nЗапросов за все время {total_pgs}"
    tg_rep += f"\n\nElaps {(time.time() - start_parse):.2f} sec."

    print(f"[ {TM()} ] INSTAGRAM PARSED Total new : {itog_sum}")
    return tg_rep


def startInstaParser(music_list=None):
    for music_id in music_list:
        EC = {}
        total_new = 0
        pg = 0
        while True:

            dat = get_insta_rapi(audio_id=music_id, endCursor=EC.get(music_id))
            if dat.get('err'):
                print(f"{dat.get('err')}")
                if 'Request-URI Too Large' in dat.get('err'):
                    # EC[music_id]=None
                    # saveFileJSON('ENDCURSORS.json',EC)
                    break
                break
            saveFileJSON('insta_parsed.json', dat)

            if 'took too long to respond' in dat.get('info', '') or dat.get('media_count') is None:
                print("ERR:\ndat.get('media_count') is None\n")
                # break
                continue

            elif dat['metadata'].get('music_info') is None:
                print("ERR:\ndat['metadata'].get('music_info') is None\n")
                # if dat.get('endCursor'): res = {'endCursor': dat.get('endCursor')}
                continue

            if dat.get('endCursor'):
                EC[music_id] = dat.get('endCursor')
                pg += 1
            else:
                print('!! NO END CURSOR')
                print(dat)
                break

            res = prepareData(dat)
            saveFileJSON('insta_prepared.json', res)
            # saveFileJSON('ENDCURSORS.json', EC)
            new_items = dbSaveInstagram(res)
            total_new += new_items
            print(
                f"[ pg: {pg} | {len(res.get('endCursor'))} | {len(dat.get('items', []))}] new = {new_items} ({total_new})")

        print(f"FINISH {music_id=}\ntotal pages : {pg}\t{total_new=}")

        return f"FINISH {music_id=}\ntotal pages : {pg}\t{total_new=}"


def main():
    all_insta_music = [
        548503650698790, 2163177623958819, 3364464810470386, 659100151177940, 659100151177940, 235518475541015,
        836131066758680,
        3051341418441472, 909338913851322, 637699754749923, 2684804191672133,
        # Это собираем, то что выше не трогаем

    ]
    music_id = '2163177623958819'
    EC = openFileJSON('ENDCURSORS.json', no={})
    print(f"{music_id=}")
    # return
    total_new = 0
    pg = 0
    while True:
        dat = get_insta_rapi(audio_id=music_id, endCursor=EC.get(music_id))
        if dat.get('err'):
            print(f"{dat.get('err')}")
            if 'Request-URI Too Large' in dat.get('err'):
                # EC[music_id]=None
                # saveFileJSON('ENDCURSORS.json',EC)
                break
            break
        saveFileJSON('insta_parsed.json', dat)

        if 'took too long to respond' in dat.get('info', '') or dat.get('media_count') is None:
            print("ERR:\ndat.get('media_count') is None\n")
            # break
            continue

        elif dat['metadata'].get('music_info') is None:
            print("ERR:\ndat['metadata'].get('music_info') is None\n")
            # if dat.get('endCursor'): res = {'endCursor': dat.get('endCursor')}
            continue

        if dat.get('endCursor'):
            EC[music_id] = dat.get('endCursor')
            pg += 1
        else:
            print('!! NO END CURSOR')
            print(dat)
            break

        res = prepareData(dat)
        saveFileJSON('insta_prepared.json', res)
        saveFileJSON('ENDCURSORS.json', EC)
        new_items = dbSaveInstagram(res)

        total_new += new_items
        print(
            f"[ pg: {pg} | {len(res.get('endCursor'))} | {len(dat.get('items', []))}] new = {new_items} ({total_new})")

    print(f"FINISH {music_id=}\ntotal pages : {pg}")
    return
    while True:
        tg_rep = startInstagramParser(PGS=5)
        sendSyncReport(text=tg_rep)
        time.sleep(30 * 60)


if __name__ == '__main__':
    main()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
