import re
from urllib.parse import unquote


class LinkValidator:
    """
        Returned decoded link or None if link is not valid
    """
    @classmethod
    def validate(cls, link) -> str | None:
        if not cls.validate_general_link(link):
            return
        try:
            decoded_link = unquote(link)
        except (ValueError, TypeError):
            return
        if "tiktok" in decoded_link:
            if "music" in decoded_link and cls.validate_tiktok_music_link(decoded_link):
                return decoded_link
            elif cls.validate_tiktok_user_link(decoded_link):
                return decoded_link
        return

    @classmethod
    def validate_general_link(cls, link) -> bool:
        pattern = r'^https?://(?:\w+\.)*\w+\.\w+(?:/\S*)?$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_tiktok_user_link(cls, link) -> bool:
        pattern = r'^https?://(?:www\.)?tiktok\.com/@\w+(?![?&])$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_tiktok_music_link(cls, link) -> bool:
        pattern = r'^https?://(?:www\.)?tiktok\.com/music/[\w-]+\-\d+$'
        return re.match(pattern, link) is not None
