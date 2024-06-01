"""
Тут лежат настройки под разные браузеры (чтобы запросы эмулировать полностью).
Что происходит: импортируется TikTokScrapperConfig и создаются его инстансы под каждый тип настроек.
В конце __init__ этот instance добавляется в SCRAPPER_TIKTOK_SETTINGS (список настроек)
Используются во время парсинга музыки.
"""

from scrappers.tiktok.request_params.config import TikTokScrapperConfig

iphone_mozilla_settings = TikTokScrapperConfig(
    ms_token=(
        'kWAM8FmtQBcUbCBd1Mu1JReYrNpKL1OWMkLuYCVSbv3rWDo-UhRD9ViOKKyJ9PntnrydvG2jFVvsukex6BYHOX-' 'iFC0Fzg5CfcADftcBwAi9omXe1NtnhSQuP2S2J5zkBcdZfGGQPFvNsGH3'
    ),
    x_bogus='DFSzswSO7whANjtItOFHy09WcBnw',
    signature='_02B4Z6wo00001qEnEjAAAIDCoScSMMHtoeKhBx6AAM1j95',
    cookies={
        'tt_csrf_token': 'DuRsICAf-D7xIMBAasa6900xtbipY4f7hLaI',
        'tt_chain_token': 'SoQudvDidit51iGOmR3Ezw==',
        '__tea_cache_tokens_1988': ('{%22_type_%22:%22default%22%2C%22' 'user_unique_id%22:%227289951420127856161%22%2C%22timestamp%22:1697324095098}'),
        'tiktok_webapp_theme': 'light',
        'odin_tt': (
            'f8dc33354b4a2aeba3652c0c0c3caff4fdbc8124c857bb2a36dfa4e0a34806716f2519b6d8d41467ef2d'
            'a6a91a68412fa46b08ea14a42b22662d8cf262dd6378a253d9d79feb5c10fec15531b6258b93'
        ),
        'perf_feed_cache': ('{%22expireTimestamp%22:1697493600000%2C%22itemIds%22:' '[%227282547030654782752%22%2C%227276792487140805893%22]}'),
        'passport_csrf_token': '582a26364335641bdd3598172d5e0bfc',
        'passport_csrf_token_default': '582a26364335641bdd3598172d5e0bfc',
        's_v_web_id': 'verify_lnsxfhms_yHqeSRTa_dagL_4MFC_9IBy_bbMu5iYn28iM',
        'cookie-consent': (
            '{%22ga%22:false%2C%22af%22:false%2C%22fbp%22:false%2C%22lip%22:false%2C%22bing%22:false'
            '%2C%22ttads%22:false%2C%22reddit%22:false%2C%22criteo%22:false%2C%22version%22:%22v9%22}'
        ),
        'ttwid': ('1%7CmOwlKOGX_hzGTArKlHzCj8_CD7iS4qDwcuLcR1xwWcU' '%7C1697636865%7Cc3403a248c3ad20b929a3fa43a5e36524fef1ae3e1470a08683046ed4d441501'),
    },
    params={
        'aid': '1988',
        'app_language': 'ru-RU',
        'app_name': 'tiktok_web',
        'browser_language': 'ru-RU',
        'browser_name': 'Mozilla',
        'browser_online': 'true',
        'browser_platform': 'Win32',
        'browser_version': (
            '5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) ' 'Version/13.0.3 Mobile/15E148 Safari/604.1'
        ),
        'channel': 'tiktok_web',
        'cookie_enabled': 'true',
        'count': '35',
        'device_id': '7289951420127856161',
        'device_platform': 'web_mobile',
        'focus_state': 'true',
        'from_page': 'music',
        'history_len': '1',
        'is_fullscreen': 'false',
        'is_page_visible': 'true',
        'language': 'ru-RU',
        'os': 'ios',
        'priority_region': '',
        'referer': 'https://www.tiktok.com/',
        'region': 'RU',
        'screen_height': '844',
        'screen_width': '390',
        'tz_name': 'Europe/Moscow',
        'webcast_language': 'ru-RU',
    },
    headers={
        'authority': 'www.tiktok.com',
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9',
        'dnt': '1',
        'referer': 'https://www.tiktok.com/',
        'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': ('Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 ' '(KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36'),
    },
)

ubuntu_edge_settings = TikTokScrapperConfig(
    ms_token=(
        'a-3rDqsS3w3GyYY-8dY30hjA-Szed-O9Fm--dJLfrogNV60k3swe-hGn9iLrjJVVvrg-0dGKJN67DY'
        'LDyneldxFQ2E0wYgRAqreP9tNRpN-YI0J7sSifCpLAf_OU5osNoFshSQQT-e-ptM7R8A=='
    ),
    x_bogus='DFSzswVOWjXANy2utmvV0U9WcBj-',
    signature='_02B4Z6wo00001Bs6VPgAAIDAGzpU-1U3DrQbOlBAAGOkcb',
    cookies={
        'tt_csrf_token': 'BZlcQpNB-B1601PshgEXNv5SmQQX4b3y-VDU',
        'tt_chain_token': 'm0RPVq7GmrdVjflkg0bdpA==',
        '__tea_cache_tokens_1988': ('{%22_type_%22:%22default%22%2C%22' 'user_unique_id%22:%227298674240000624133%22%2C%22timestamp%22:1699511857566}'),
        'tiktok_webapp_theme': 'light',
        'odin_tt': (
            'c0e0f0168e1a522b621007afe66c5389e9926dbf7daf30f99030051ddf6a7dd7bfc23d11a2988addc149'
            '929fd4ac76d6ae85e5640749c7a897aecf35f97063e5f6f388cd6acd1400a66e08b52af8e1a9'
        ),
        'perf_feed_cache': ('{%22expireTimestamp%22:1699959600000%2C%22itemIds%22:' '[%227268940080889220357%22%2C%227284544040828390662%22]}'),
        'passport_csrf_token': 'aee1c6dc520bc2a0e1a494b67d260b1c',
        'passport_csrf_token_default': 'aee1c6dc520bc2a0e1a494b67d260b1c',
        's_v_web_id': 'verify_loq5oipy_68HOg4Il_dcML_495r_A4oN_RbzOzpKE1rSw',
        'ttwid': ('1%7C3JbdrNra2QvlI3q2QIjNCv8GQuAunxZkYMO8uYQeRMk%7C1699789914%7C453dd2f6e' '8f1ebaf05e2f9a81d7e7fadd07460b1782266a700ad4cd6b4231a2d'),
    },
    params={
        'aid': '1988',
        'app_language': 'en',
        'app_name': 'tiktok_web',
        'browser_language': 'en-US',
        'browser_name': 'Mozilla',
        'browser_online': 'true',
        'browser_platform': 'Linux x86_64',
        'browser_version': ('5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)' ' Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46'),
        'channel': 'tiktok_web',
        'cookie_enabled': 'true',
        'count': '35',
        'coverFormat': '1',
        'device_id': '7298674240000624133',
        'device_platform': 'web_pc',
        'focus_state': 'false',
        'from_page': 'music',
        'history_len': '1',
        'is_fullscreen': 'false',
        'is_page_visible': 'true',
        'language': 'en',
        'os': 'linux',
        'priority_region': '',
        'referer': 'https://www.tiktok.com',
        'region': 'BY',
        'screen_height': '1080',
        'screen_width': '1920',
        'tz_name': 'Europe/Moscow',
        # 'verifyFp': 'verify_loq5oipy_68HOg4Il_dcML_495r_A4oN_RbzOzpKE1rSw',
        'webcast_language': 'en',
    },
    headers={
        'authority': 'www.tiktok.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        # 'dnt': '1',
        'referer': 'https://www.tiktok.com/',
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' 'Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46'),
    },
)

windows_edge_settings = TikTokScrapperConfig(
    ms_token=('DdssctqyIkoXmgE6tyy8mZXSk9FXMjpFrEqusx0Co_tYeGE2K3OYOInh7pX7hqeSu563Ig3y8gYMEiv9FWhAA' '6KykDAhnFkbVltkUeR1N8vmupRy-lCwUlIPlEDL8U52z7XhYA=='),
    x_bogus='DFSzswSOeLGANeR8tmfdTz9WcBrb',
    signature='_02B4Z6wo00001bVRBfAAAIDBtVEF8qHSKE21cQlAAAgF00',
    cookies={
        'tt_csrf_token': 'kSnIWCGe-LlEjvFMSKWtPVsHe16tllblw5vg',
        'tt_chain_token': '7CtCyETB/5Qz9bZlxHMsoQ==',
        '__tea_cache_tokens_1988': ('{%22_type_%22:%22default%22%2C%22' 'user_unique_id%22:%227300552300538447366%22%2C%22timestamp%22:1699792345959}'),
        'tiktok_webapp_theme': 'light',
        'odin_tt': (
            'c20a9b4c7c2d72b1a7433cfbbc845a3f22e80165e90770249eb05367688a00035dc3eab9584ae'
            '564ca2872c27681ba03386e076f30c85e01fca80a2273224bf9d53ae38a7373b319ddb2788309540a11'
        ),
        'perf_feed_cache': (
            '{%22expireTimestamp%22:1699963200000%2C%22itemIds%22:[%227282354933548977415%22%2C' '%227285299893793770758%22%2C%227294698096750038278%22]}'
        ),
        'passport_csrf_token': '7cdfebdec97c9c2e6329faf6b717b84b',
        'passport_csrf_token_default': '7cdfebdec97c9c2e6329faf6b717b84b',
        's_v_web_id': 'verify_lovgg7zq_Sa2oN5WX_nbq0_4fFn_8YSd_oyVresC5tYos',
        'cookie-consent': (
            '{%22ga%22:true%2C%22af%22:true%2C%22fbp%22:true%2C%22lip%22:true%2C%'
            '22bing%22:true%2C%22ttads%22:true%2C%22reddit%22:true%2C%22hubspot%22:true%2C%22version%22:%22v10%22}'
        ),
        'ttwid': ('1%7CC9pZ_LkETeWI3YqNyyt5OJKZA2nDG-eCGpUC5IxAv5c%7C1699792586%7C6d3' '1a60618643d829015d37c6e0b139dfd4c9358347f011432e953c6703ac43a'),
    },
    params={
        'aid': '1988',
        'app_language': 'ru-RU',
        'app_name': 'tiktok_web',
        'browser_language': 'ru-RU',
        'browser_name': 'Mozilla',
        'browser_online': 'true',
        'browser_platform': 'Win32',
        'browser_version': (
            '5.0%20%28Linux%3B%20Android%206.0%3B%20Nexus%205%20Build%2FMRA58N%29%20AppleWebKit%2F537.36%20%28'
            'KHTML%2C%20like%20Gecko%29%20Chrome%2F119.0.0.0%20Mobile%20Safari%2F537.36%20Edg%2F119.0.0.0'
        ),
        'channel': 'tiktok_web',
        'cookie_enabled': 'true',
        'count': '35',
        'device_id': '7300552300538447366',
        'device_platform': 'web_mobile',
        'focus_state': 'true',
        'history_len': '1',
        'language': 'ru-RU',
        'is_fullscreen': 'false',
        'is_page_visible': 'true',
        'os': 'android',
        'referer': 'https://www.tiktok.com/',
        'region': 'TR',
        'screen_height': '831',
        'screen_width': '664',
        'tz_name': 'Europe/Moscow',
        'webcast_language': 'ru-RU',
    },
    headers={
        'authority': 'www.tiktok.com',
        'accept': '*/*',
        'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        # 'dnt': '1',
        'referer': 'https://www.tiktok.com/',
        'sec-ch-ua': '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': (
            'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/119.0.0.0 Mobile Safari/537.36 Edg/119.0.0.0'
        ),
    },
)
