SCRAPPER_SETTINGS: dict[str: list] = {
    "tiktok": [],
    "youtube": [],
    "instagram": [],
}


class TikTokScrapperConfig:
    def __init__(
            self,
            ms_token: str,
            x_bogus: str,
            signature: str,
            cookies: dict[str:str],
            params: dict[str:str],
            headers: dict[str:str],
            is_available: bool = True,
    ):
        self.msToken = ms_token
        self.X_Bogus = x_bogus
        self.signature = signature
        self.cookies = cookies | {
            'msToken': ms_token,
        }
        self.params = params | {
            'msToken': ms_token,
            'X-Bogus': x_bogus,
            '_signature': signature,
        }
        self.headers = headers
        self.is_available = is_available
        SCRAPPER_SETTINGS["tiktok"].append(self)
