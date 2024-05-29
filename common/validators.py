import re
from typing import Callable
from urllib.parse import unquote, urlparse, urlunparse


class ValidationScopes:
    TIKTOK_USER = 0
    TIKTOK_MUSIC = 1
    YOUTUBE_USER = 2
    YOUTUBE_MUSIC = 3
    ALL = 4

    # скоупы мониторинга
    MONITORING: list[int] = [TIKTOK_MUSIC, YOUTUBE_USER, YOUTUBE_MUSIC]

    # используется пока что только в тестах
    all_scopes: list[int] = [TIKTOK_USER, TIKTOK_MUSIC, YOUTUBE_USER, YOUTUBE_MUSIC, ALL]

    # отдельные скоупы (не смешивать с теми, что выше, могут поломать валидацию)
    TIKTOK_USER_ONE_VIDEO = 100


class LinkValidator:
    """
        Returned decoded link or None if link is not valid
    """

    @classmethod
    def validate(cls, url: str, scopes: int | list[int] = ValidationScopes.ALL, strict: bool = False) -> str | None:
        """Очищает url (query параметры) и валидирует ссылку в зависимости от переданных scopes"""
        if isinstance(scopes, int):
            scopes = [scopes]

        cleaned_url: str = cls._clean_link(url)

        if not cls.validate_general_link(cleaned_url):
            return None

        try:
            decoded_url: str = unquote(cleaned_url)
        except (ValueError, TypeError):
            return None

        res: list[bool] = []
        # перебираем переданные scopes и вызываем соответствующие валидаторы
        for scope in scopes:
            res.extend(validate_func(decoded_url) for validate_func in cls._validation_scopes_func_mapper(scope))
        # если strict - все валидаторы должны вернуть True
        if strict:
            return decoded_url if all(res) else None

        # иначе достаточно одного True
        return decoded_url if any(res) else None

    @classmethod
    def _clean_link(cls, url: str) -> str | None:
        parsed_url = urlparse(url)
        clean_parsed_url = parsed_url._replace(query="")
        clean_url = str(urlunparse(clean_parsed_url))
        return clean_url

    @classmethod
    def validate_general_link(cls, link: str) -> bool:
        pattern = r'^https:\/\/(?:\w+\.)*\w+\.\w+(?:/\S*)?$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_tiktok_user_link(cls, link: str) -> bool:
        pattern = r'^https:\/\/(?:www\.)?tiktok\.com\/@[^?&]+$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_tiktok_music_link(cls, link: str) -> bool:
        pattern = r'^https:\/\/(?:www\.)?tiktok\.com\/music\/[\w-]+\-\d+$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_youtube_music_link(cls, link: str) -> bool:
        pattern = r'^https:\/\/(?:www\.)?youtube\.com\/source\/[\w-]+\/shorts.*$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_youtube_user_link(cls, link: str) -> bool:
        pattern = r'^https:\/\/(?:www\.)?youtube\.com\/@[\w-]+.*$'
        return re.match(pattern, link) is not None

    @classmethod
    def validate_tiktok_user_one_video_link(cls, link: str) -> bool:
        pattern = r'^https:\/\/(?:www\.)?tiktok\.com\/@[^/?&]+\/video\/\d+$'
        return re.match(pattern, link) is not None

    @classmethod
    def _validation_scopes_func_mapper(cls, scope: int) -> list[Callable[..., bool]]:
        """В зависимости от переданного скоупа возвращает список функций для проверки ссылки"""
        mapper: dict[int, list[Callable[..., bool]]] = {
            ValidationScopes.TIKTOK_USER: [cls.validate_tiktok_user_link],
            ValidationScopes.TIKTOK_MUSIC: [cls.validate_tiktok_music_link],
            ValidationScopes.YOUTUBE_USER: [cls.validate_youtube_user_link],
            ValidationScopes.YOUTUBE_MUSIC: [cls.validate_youtube_music_link],
            ValidationScopes.ALL: [
                cls.validate_tiktok_user_link,
                cls.validate_tiktok_music_link,
                cls.validate_youtube_user_link,
                cls.validate_youtube_music_link,
            ],
            ValidationScopes.TIKTOK_USER_ONE_VIDEO: [cls.validate_tiktok_user_one_video_link],
        }
        return mapper[scope]


# есть тесты на LinkValidator (./manage.py test common)
