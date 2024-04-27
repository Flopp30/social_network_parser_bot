import json
import requests
import time
import re
import os

from toolbox import saveFileJSON, openFileJSON, func_chunk, get_duration_in_seconds, youtube_convert_to_timestamp, \
    getLink
from xls_saver import saveToXls
from pwee import dbSaveInstagram, getActiveTracks, getReelsByTrack, dbSaveParseStat
from tg_reporter import sendSyncReport


def post_request_browser(originalUrl, url_param, visitorData, continuation):
    cookies = {
        'GPS': '1',
        'YSC': 'H3gdXZkYDnQ',
        'VISITOR_INFO1_LIVE': 'p4jEpaI80G4',
        'VISITOR_PRIVACY_METADATA': 'CgJSVRICGgA%3D',
        'PREF': 'f4=4000000&tz=Europe.Moscow',
    }

    headers = {
        'authority': 'www.youtube.com',
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9',
        'content-type': 'application/json',
        # 'cookie': 'GPS=1; YSC=H3gdXZkYDnQ; VISITOR_INFO1_LIVE=p4jEpaI80G4; VISITOR_PRIVACY_METADATA=CgJSVRICGgA%3D; PREF=f4=4000000&tz=Europe.Moscow',
        'dnt': '1',
        'origin': 'https://www.youtube.com',
        'referer': f'{originalUrl}?bp={url_param}',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'x-goog-visitor-id': visitorData,  # 'CgtwNGpFcGFJODBHNCiZ-YWpBjIICgJSVRICGgA%3D',
        'x-youtube-bootstrap-logged-in': 'false',
        'x-youtube-client-name': '1',
        'x-youtube-client-version': '2.20231003.02.02',
    }

    params = {
        'key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
        'prettyPrint': 'false',
    }

    json_data = {
        'context': {
            'client': {
                'hl': 'ru',
                'gl': 'RU',
                # 'remoteHost': '93.88.74.160',
                'deviceMake': 'Apple',
                'deviceModel': 'iPhone',
                'visitorData': 'CgtwNGpFcGFJODBHNCiZ-YWpBjIICgJSVRICGgA%3D',
                'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1,gzip(gfe)',
                'clientName': 'WEB',
                'clientVersion': '2.20231003.02.02',
                'osName': 'iPhone',
                'osVersion': '13_2_3',
                'originalUrl': originalUrl,
                'screenPixelDensity': 3,
                'platform': 'MOBILE',
                'clientFormFactor': 'UNKNOWN_FORM_FACTOR',
                'configInfo': {
                    'appInstallData': 'CJn5hakGENShrwUQweqvBRDp6P4SEO6irwUQtaavBRCa8K8FEN3o_hIQtMmvBRCk-K8FELzrrwUQ1eWvBRC4i64FEOSz_hIQp-r-EhDnuq8FEInorgUQzN-uBRC4-68FEPOorwUQ-r6vBRCn968FEKbs_hIQvvmvBRC7-a8FEMyu_hIQ6-j-EhDbr68FEOrDrwUQ9fmvBRC9tq4FEKn3rwUQ4_KvBRCst68FEJ7jrwUQiOOvBRCX5_4SEML3rwUQ1-mvBRCO-a8FEM3_rwUQ4tSuBRDF-68FENnurwUQ9P-vBRDb2K8FENPhrwUQrvqvBRClwv4SENnJrwU%3D',
                },
                'screenDensityFloat': 3,
                'userInterfaceTheme': 'USER_INTERFACE_THEME_LIGHT',
                'browserName': 'Safari Mobile',
                'browserVersion': '13.0.3.15E148',
                'acceptHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'deviceExperimentId': 'ChxOekk0TnpJME1qWTJPVEl3TlRRMU16UXdOZz09EJn5hakGGJn5hakG',
                'screenWidthPoints': 980,
                'screenHeightPoints': 2121,
                'utcOffsetMinutes': 180,
                'connectionType': 'CONN_CELLULAR_4G',
                'memoryTotalKbytes': '8000000',
                'mainAppWebInfo': {
                    'graftUrl': f'{originalUrl}?bp={url_param}',
                    'webDisplayMode': 'WEB_DISPLAY_MODE_BROWSER',
                    'isWebNativeShareAvailable': True,
                },
                'timeZone': 'Europe/Moscow',
            },
            'user': {
                'lockedSafetyMode': False,
            },
            'request': {
                'useSsl': True,
                'internalExperimentFlags': [
                    {
                        'key': 'force_enter_once_in_webview',
                        'value': 'true',
                    },
                ],
                'consistencyTokenJars': [],
            },
        },
        'continuation': continuation,
    }

    response = requests.post(
        'https://www.youtube.com/youtubei/v1/browse',
        params=params,
        cookies=cookies,
        headers=headers,
        json=json_data,
    )

    print(f"[ {response.status_code} ]")
    return response.json()

    # Note: json_data will not be serialized by requests
    # exactly as it was in the original request.
    # data = '{"context":{"client":{"hl":"ru","gl":"RU","remoteHost":"93.88.74.160","deviceMake":"Apple","deviceModel":"iPhone","visitorData":"CgtwNGpFcGFJODBHNCiZ-YWpBjIICgJSVRICGgA%3D","userAgent":"Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1,gzip(gfe)","clientName":"WEB","clientVersion":"2.20231003.02.02","osName":"iPhone","osVersion":"13_2_3","originalUrl":"https://www.youtube.com/source/Xa3nNeLpuZY/shorts","screenPixelDensity":3,"platform":"MOBILE","clientFormFactor":"UNKNOWN_FORM_FACTOR","configInfo":{"appInstallData":"CJn5hakGENShrwUQweqvBRDp6P4SEO6irwUQtaavBRCa8K8FEN3o_hIQtMmvBRCk-K8FELzrrwUQ1eWvBRC4i64FEOSz_hIQp-r-EhDnuq8FEInorgUQzN-uBRC4-68FEPOorwUQ-r6vBRCn968FEKbs_hIQvvmvBRC7-a8FEMyu_hIQ6-j-EhDbr68FEOrDrwUQ9fmvBRC9tq4FEKn3rwUQ4_KvBRCst68FEJ7jrwUQiOOvBRCX5_4SEML3rwUQ1-mvBRCO-a8FEM3_rwUQ4tSuBRDF-68FENnurwUQ9P-vBRDb2K8FENPhrwUQrvqvBRClwv4SENnJrwU%3D"},"screenDensityFloat":3,"userInterfaceTheme":"USER_INTERFACE_THEME_LIGHT","browserName":"Safari Mobile","browserVersion":"13.0.3.15E148","acceptHeader":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7","deviceExperimentId":"ChxOekk0TnpJME1qWTJPVEl3TlRRMU16UXdOZz09EJn5hakGGJn5hakG","screenWidthPoints":980,"screenHeightPoints":2121,"utcOffsetMinutes":180,"connectionType":"CONN_CELLULAR_4G","memoryTotalKbytes":"8000000","mainAppWebInfo":{"graftUrl":"https://www.youtube.com/source/Xa3nNeLpuZY/shorts?bp=8gUeChwSGgoLWGEzbk5lTHB1WlkSC1hhM25OZUxwdVpZ","webDisplayMode":"WEB_DISPLAY_MODE_BROWSER","isWebNativeShareAvailable":true},"timeZone":"Europe/Moscow"},"user":{"lockedSafetyMode":false},"request":{"useSsl":true,"internalExperimentFlags":[{"key":"force_enter_once_in_webview","value":"true"}],"consistencyTokenJars":[]},"clickTracking":{"clickTrackingParams":"CAAQhGciEwjD3YLAo-SBAxVc4EIFHTrqB1A="},"adSignalsInfo":{"params":[{"key":"dt","value":"1696693409178"},{"key":"flash","value":"0"},{"key":"frm","value":"0"},{"key":"u_tz","value":"180"},{"key":"u_his","value":"5"},{"key":"u_h","value":"844"},{"key":"u_w","value":"390"},{"key":"u_ah","value":"844"},{"key":"u_aw","value":"390"},{"key":"u_cd","value":"24"},{"key":"bc","value":"31"},{"key":"bih","value":"2120"},{"key":"biw","value":"980"},{"key":"brdim","value":"0,0,0,0,390,0,390,844,980,2121"},{"key":"vis","value":"1"},{"key":"wgl","value":"true"},{"key":"ca_type","value":"image"}]}},"continuation":"4qmFsgLlARIRRkVzZnZfYXVkaW9fcGl2b3QasAFDQ0I2WDBORE9GRkNRbTltZFdkWlkwTm9iMHRETVdob1RUSTFUMXBWZUhka1ZuQmFSV2QwV1ZsVVRuVlViVlpOWTBoV1lWZFRTVkpEWnpnd1QycEZNazlVV1RKUFZFMHdUVVJGTkU5RVZYRkVVVzlNVWxaT1dsWlhTa1ZpYlhCUVUycFI4Z1VlQ2h3U0dnb0xXR0V6Yms1bFRIQjFXbGtTQzFoaE0yNU9aVXh3ZFZwWpoCHGJyb3dzZS1mZWVkRkVzZnZfYXVkaW9fcGl2b3Q%3D"}'
    # response = requests.post('https://www.youtube.com/youtubei/v1/browse', params=params, cookies=cookies, headers=headers, data=data)


def get_yt_data(dat):
    saveFileJSON("yt_last_dat.json", dat)
    res = {'header': {'source': 'youtube'}, 'items': []}
    for d in dat:
        if d.get('richItemRenderer'):
            if d['richItemRenderer']['content'].get('reelItemRenderer'):
                res['items'].append(d['richItemRenderer']['content']['reelItemRenderer']['videoId'])
            elif d['richItemRenderer']['content']['shortsLockupViewModel']['onTap']['innertubeCommand'].get(
                    'reelWatchEndpoint'):
                # /12/richItemRenderer/content/shortsLockupViewModel/onTap/innertubeCommand/reelWatchEndpoint/videoId
                res['items'].append(
                    d['richItemRenderer']['content']['shortsLockupViewModel']['onTap']['innertubeCommand'][
                        'reelWatchEndpoint'].get('videoId'))
        elif d.get('richSectionRenderer'):
            res['header']['name'] = \
            d['richSectionRenderer']['content']['sourcePivotHeaderRenderer']['headerInformation'][
                'profilePageHeaderInformationViewModel']['title']['profilePageHeaderTitleViewModel']['title']['content']
            meta_data = d['richSectionRenderer']['content']['sourcePivotHeaderRenderer']['headerInformation'][
                'profilePageHeaderInformationViewModel']['metadata']['profilePageHeaderMetadataViewModel'][
                'metadataRows']
            for md in meta_data:
                if md.get('textParts'):
                    if md['textParts'][0].get('styleRuns'):
                        res['header']['total'] = md['textParts'][0].get('content')
        elif d.get('continuationItemRenderer'):
            res['continuation'] = d['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token']
    return res


def yotube_get_shorts_data(url, rows=1000):
    pgs = rows // 15 + 2
    url = url.split('?bp=')[0]
    print(f"start parse : {url}")

    r = requests.get(url)
    if r.status_code != 200: return {'err': r.text}
    html = r.text
    with open('youtube_shorts_FIRST_PAGE.html', "w", encoding='utf-8') as f:
        f.write(html)
    pattern = r'var ytInitialData = (.*?);</script>'
    match = re.search(pattern, html, re.DOTALL)
    res = {'err': 'NO DATA IN SCRIPT'}
    if match is None: return res

    json_text = match.group(1)
    try:
        js = json.loads(json_text)
    except Exception as ex:
        print(ex)
        return {'err': ex}

    saveFileJSON('youtube_first_page.json', js)

    dat = js['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['richGridRenderer'][
        'contents']

    res = get_yt_data(dat)
    # return res

    # /responseContext/webResponseContextExtensionData/ytConfigData/visitorData
    ytCommand = json.loads(re.search(r'window\[\'ytCommand\'\] = ({.*?});', html).group(1))
    url_param = ytCommand['browseEndpoint']['params']

    visitorData = js['responseContext']['webResponseContextExtensionData']['ytConfigData']['visitorData']
    continuation = res.get('continuation')
    originalUrl = url.split('?bp=')[0]

    saveFileJSON('prepared_youtube_first_page.json', res)

    print(f"{originalUrl=}")
    # print(f"{url_param=}")
    # print(f"{ytCommand.keys()=}")
    # print(f"{continuation=}\n{visitorData=}")
    for n in range(pgs):
        if continuation is None:
            print(f"BREAK! NO continuation")
            break
        print(f"PARSE page #{n + 2} rows : {len(res['items'])}")
        js_dat = post_request_browser(originalUrl, url_param, visitorData, continuation)
        saveFileJSON(f'you_post_{(n + 2):03}.json', js_dat)
        if js_dat.get('onResponseReceivedActions') is None: return res
        new_res = get_yt_data(
            js_dat['onResponseReceivedActions'][0]['appendContinuationItemsAction']['continuationItems'])
        for r in new_res['items']:
            res['items'].append(r)
        continuation = new_res.get('continuation')
        if len(res['items']) > rows:
            print(f"BREAK! > {rows}")
            break
    return res


def startYoutubeParser(music_list=None):
    # подробности тут!!!
    # https://yt.lemnoslife.com/noKey/videos?part=id,statistics,snippet,contentDetails&id=VEQ3_QsoI3k

    report = []
    tracks = getActiveTracks(tip='youtube', music_list=music_list)
    for music_id, name in tracks.items():
        print(f"{music_id} {name}")
        url = f"https://www.youtube.com/source/{music_id}/shorts"
        res = yotube_get_shorts_data(url, rows=600)
        total = None
        if res['header'].get('total'):
            total = res['header']['total'].split('коротких')[0].replace(' ', '').strip()
            if 'тыс.' in total: total = total.replace('тыс.', '000')
            if 'млн' in total: total = total.replace('млн', '000000')
            if ',' in total: total = total.replace(',', '')[:-1]
            try:
                total_int = int(total)
            except Exception as ex:
                print(f"ERR Convert to Int: {total=}\t{res['header'].get('total')=}")
                total = None

        db_reels = getReelsByTrack(music_id=music_id)
        to_parse = [music_id]
        plan_rows = len(res['items'])
        for item in res['items']:
            if item in db_reels: continue
            to_parse.append(item)
        if len(to_parse) == 1: continue

        print(f"pasre description for {len(to_parse)} shorts")

        urllist = func_chunk(to_parse, 20)
        res = {'header': {'source': 'youtube', 'music_id': music_id}, 'items': []}

        for urls in urllist:
            yt_url = ','.join(urls)
            try:
                response = requests.get(
                    f"https://yt.lemnoslife.com/noKey/videos?part=id,statistics,snippet,contentDetails&id={yt_url}")
                dat = response.json()
                saveFileJSON(f'yt_answer.json', dat)
            except Exception as ex:
                print(ex)
                continue

            for d in dat['items']:
                # try:

                if d['id'] == music_id:
                    res['header']['name'] = d['snippet']['title']
                    res['header']['total'] = int(total) if total else 0
                    # res['header']['publishedAt'] = d['snippet']['publishedAt'] #убрать
                    res['header']['upload'] = youtube_convert_to_timestamp(d['snippet']['publishedAt'])
                    res['header']['duration'] = get_duration_in_seconds(d['contentDetails']['duration'])
                    continue
                res['items'].append({
                    'link': d['id'],
                    # 'publishedAt': d['snippet']['publishedAt'],#убрать
                    'upload': youtube_convert_to_timestamp(d['snippet']['publishedAt']),
                    # 'dura_str':d['contentDetails']['duration'], #убрать
                    'duration': get_duration_in_seconds(d['contentDetails']['duration']),
                    'views': d['statistics'].get('viewCount'),
                    'likes': d['statistics'].get('likeCount'),
                    'comments': d['statistics'].get('commentCount'),
                    'saves': d['statistics'].get('favoriteCount'),
                })

                # except Exception as ex:
                # print(f"ERR: {music_id=}\n{ex}")

            saveFileJSON(f"youtube_samplse_preSave.json", res)

        new_col = dbSaveInstagram(res)
        print(f"\t{new_col=}")

        report.append({'music_id': music_id, 'plan': plan_rows, 'fact': new_col})
        dbSaveParseStat(music_id, plan_rows, new_col)
        print(report)
        saveFileJSON("yotube_report.json", report)

    tg_rep = "<b>YouTube.</b> Результат сбора:"
    total_plan = 0
    total_fact = 0
    for r in report:
        music_link = f"https://www.youtube.com/source/{r['music_id']}/shorts"
        music_name = tracks.get(r['music_id']) if tracks.get(r['music_id']) else r['music_id']
        tg_rep += f"\n<b>{r['fact']}</b> / {r['plan']} {getLink(music_link, music_name)}"
        total_plan += r['plan']
        total_fact += r['fact']
    tg_rep += f"\n\nИтого новых : <b>{total_fact}</b> / {total_plan}"
    return tg_rep


def main():
    while True:
        tg_rep = startYoutubeParser()
        sendSyncReport(text=tg_rep)
        time.sleep(60 * 60)


if __name__ == '__main__':
    main()
