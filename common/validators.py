import re
from urllib.parse import unquote


class LinkValidator:
    """
        Returned decoded link or None if link is not valid
    """

    @classmethod
    def validate(cls, link) -> str | None:
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
        # TODO реализовать валидацию
        return True

    @classmethod
    def validate_youtube_user_link(cls, link: str) -> bool:
        # TODO реализовать валидацию ссылки на акк в тиктоке
        return True


if __name__ == '__main__':
    print(LinkValidator.validate('https://www.tiktok.com/@danya1.milok'))
    print(LinkValidator.validate('https://www.tiktok.com/@kingx.music'))
    print(LinkValidator.validate('https://www.tiktok.com/music/Scary-Garry-6914598970259490818'))
    print(LinkValidator.validate('https://youtube.com/source/asfvzc1232/shorts?si=Z-v366gPFTMQeGia'))
    print(LinkValidator.validate('https://youtube.com/source/ZmKk4krdy84/shorts?bp=8gUeChwSGgoLWm1LazRrcmR5ODQSC1ptS2s0a3JkeTg0'))
    print(LinkValidator.validate('https://youtube.com/@officialphonkmusic?si=m1fGBNlqthSp1_Zd'))
