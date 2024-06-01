from typing import TypeAlias, Any

TypeHeaders: TypeAlias = dict[str, Any]
TypeCookies: TypeAlias = dict[str, Any]
TypeParams: TypeAlias = dict[str, Any]
PostData: TypeAlias = dict[str, Any]


def get_yt_post_params(original_url: str, query_params: str, visitor_data: str, continuation: str) -> tuple[TypeHeaders, TypeCookies, TypeParams, PostData]:
    """Возвращает параметры для post запроса к api youtube"""
    headers: TypeHeaders = {
        'authority': 'www.youtube.com',
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.youtube.com',
        'referer': f'{original_url}?bp={query_params}',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'x-goog-visitor-id': visitor_data,
        'x-youtube-bootstrap-logged-in': 'false',
        'x-youtube-client-name': '1',
        'x-youtube-client-version': '2.20231003.02.02',
    }

    cookies: TypeCookies = {
        'GPS': '1',
        'YSC': 'H3gdXZkYDnQ',
        'VISITOR_INFO1_LIVE': 'p4jEpaI80G4',
        'VISITOR_PRIVACY_METADATA': 'CgJSVRICGgA%3D',
        'PREF': 'f4=4000000&tz=Europe.Moscow',
    }

    params: TypeParams = {
        'key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
        'prettyPrint': 'false',
    }

    json_data: PostData = {
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
                'originalUrl': original_url,
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
                    'graftUrl': f'{original_url}?bp={query_params}',
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
    return headers, cookies, params, json_data
