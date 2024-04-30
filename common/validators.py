import re
from urllib.parse import unquote, urlparse, urlunparse


class LinkValidator:
    """
        Returned decoded link or None if link is not valid
    """
    @classmethod
    def clean_link(cls, link) -> str | None:
        parsed_url = urlparse(link)
        clean_parsed_url = parsed_url._replace(query="")
        clean_url = str(urlunparse(clean_parsed_url))
        return clean_url

    @classmethod
    def validate(cls, link) -> str | None:
        link = cls.clean_link(link)
        if not cls.validate_general_link(link):
            return None
        try:
            decoded_link = unquote(link)
        except (ValueError, TypeError):
            return None

        if "tiktok" in decoded_link:
            if "music" in decoded_link and cls.validate_tiktok_music_link(decoded_link):
                return decoded_link
            elif cls.validate_tiktok_user_link(decoded_link):
                return decoded_link

        if 'youtube' in decoded_link:
            if 'source' in decoded_link and cls.validate_youtube_music_link(decoded_link):
                return decoded_link
            if cls.validate_youtube_user_link(decoded_link):
                return decoded_link

        return None

    @classmethod
    def validate_general_link(cls, link: str) -> bool:
        pattern = r'^https?://(?:\w+\.)*\w+\.\w+(?:/\S*)?$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_tiktok_user_link(cls, link: str) -> bool:
        pattern = r'^https?:\/\/(?:www\.)?tiktok\.com\/[^?&]+$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_tiktok_music_link(cls, link: str) -> bool:
        pattern = r'^https?:\/\/(?:www\.)?tiktok\.com\/music\/[\w-]+\-\d+$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_youtube_music_link(cls, link: str) -> bool:
        pattern = r'^https?:\/\/(?:www\.)?youtube\.com\/source\/[\w-]+\/shorts.*$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_youtube_user_link(cls, link: str) -> bool:
        # TODO реализовать валидацию ссылки на акк в тиктоке
        return False


if __name__ == '__main__':
    print(LinkValidator.validate('https://www.tiktok.com/@danya1.milok'))
    print(LinkValidator.validate('https://www.tiktok.com/@kingx.music'))
    print(LinkValidator.validate('https://www.tiktok.com/music/Scary-Garry-6914598970259490818'))
    print(LinkValidator.validate('https://youtube.com/source/asfvzc1232/shorts?si=Z-v366gPFTMQeGia'))
    print(LinkValidator.validate('https://youtube.com/source/ZmKk4krdy84/shorts?bp=8gUeChwSGgoLWm1LazRrcmR5ODQSC1ptS2s0a3JkeTg0'))
    # print(LinkValidator.validate('https://youtube.com/@officialphonkmusic?si=m1fGBNlqthSp1_Zd'))
    print(LinkValidator.clean_link("https://www.tiktok.com/music/%D0%BE%D1%80%D0%B8%D0%B3%D0%B8%D0%BD%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9-%D0%B7%D0%B2%D1%83%D0%BA-7357401700558916357?lang=ru-RU"))
    print(LinkValidator.clean_link("https://youtube.com/source/asfvzc1232/shorts?si=Z-v366gPFTMQeGia"))
