# Список созданных настроек
# FIXME не самая хорошая реализация, но трогать я её не советую
SCRAPPER_TIKTOK_SETTINGS = []


class TikTokScrapperConfig:
    """Объект настроек для парсера"""

    def __init__(
        self,
        ms_token: str,
        x_bogus: str,
        signature: str,
        cookies: dict[str, str],
        params: dict[str, str],
        headers: dict[str, str],
        is_available: bool = True,
    ):
        self.msToken: str = ms_token
        self.X_Bogus: str = x_bogus
        self.signature: str = signature
        self.cookies: dict[str, str] = cookies | {
            'msToken': ms_token,
        }
        self.params: dict[str, str] = params | {
            'msToken': ms_token,
            'X-Bogus': x_bogus,
            '_signature': signature,
        }
        self.headers: dict[str, str] = headers
        self.is_available: bool = is_available
        SCRAPPER_TIKTOK_SETTINGS.append(self)
