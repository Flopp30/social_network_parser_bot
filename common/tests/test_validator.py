from django.test import TestCase

from common.validators import LinkValidator, ValidationScopes


class LinkValidatorTest(TestCase):
    validator = LinkValidator

    def test_tiktok_one_video_url(self):
        """Ссылка на одно видео в аккаунте пользователя"""
        link_res: list[tuple[str, str]] = [
            ('https://www.tiktok.com/@makoto.gif/video/7369694849286540576', 'https://www.tiktok.com/@makoto.gif/video/7369694849286540576'),
            ('https://www.tiktok.com/@ricc_1st/video/6930305666573716741?wqeqqwe', 'https://www.tiktok.com/@ricc_1st/video/6930305666573716741'),
        ]

        for link, res in link_res:
            validated_link = self.validator.validate(link, scopes=ValidationScopes.TIKTOK_USER_ONE_VIDEO)
            self.assertEqual(validated_link, res)

    def test_tt_user_or_music(self):
        links = [
            'https://www.tiktok.com/music/son-original-7264928629472856864',
        ]
        for link in links:
            validated_link = self.validator.validate(link, scopes=[ValidationScopes.TIKTOK_USER, ValidationScopes.TIKTOK_MUSIC])
            print(validated_link)

    def test_correct_tt_music_url(self):
        """Проверяем валидные ссылки на музыку в tiktok"""
        links_res: list[tuple[str, str]] = [
            ('https://www.tiktok.com/music/Scary-Garry-6914598970259490818', 'https://www.tiktok.com/music/Scary-Garry-6914598970259490818'),
            ('https://www.tiktok.com/music/Scary-Garry-6914598970259490818?q=a', 'https://www.tiktok.com/music/Scary-Garry-6914598970259490818'),
        ]
        for link, res in links_res:
            # успешный кейс, scope - ALL
            validated_link = self.validator.validate(link, scopes=ValidationScopes.ALL)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # успешный кейс, scope - empty
            validated_link = self.validator.validate(link)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # успешный кейс, scope - music
            validated_link = self.validator.validate(link, scopes=ValidationScopes.TIKTOK_MUSIC)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # неуспешный кейс, scope - user
            validated_link = self.validator.validate(link, scopes=ValidationScopes.TIKTOK_USER)
            self.assertIsNone(validated_link)
            # неуспешный кейс, scope - yt music
            validated_link = self.validator.validate(link, scopes=ValidationScopes.YOUTUBE_MUSIC)
            self.assertIsNone(validated_link)

    def test_incorrect_tt_music_url(self):
        """Проверяем невалидные ссылки на tt music"""
        links: list[str] = [
            'http://www.tiktok.com/music/Scary-Garry-6914598970259490818',
            'http://www.tiktok.com/music/Scary-Garry-6914598970259490818?q=a',
            'https://www.tiktok.kom/music/Scary-Garry-6914598970259490818',
            'https://www.tiktok.kom/music/Scary-Garry-6914598970259490818?q=a',
            'https://www.tiktok.kom/music/Scary-Garry-6914598970259490818/source',
            'https://www.tiktok.kom/music/Scary-Garry-6914598970259490818/source?q=a',
        ]
        for link in links:
            for scope in ValidationScopes.all_scopes:
                validated_link = self.validator.validate(link, scopes=scope)
                self.assertIsNone(validated_link)

    def test_correct_tt_user_url(self):
        """Проверяем валидные ссылки на юзера в tiktok"""
        links_res: list[tuple[str, str]] = [
            ('https://www.tiktok.com/@danya1.milok', 'https://www.tiktok.com/@danya1.milok'),
            ('https://www.tiktok.com/@danya1.milok?some_query=asddffsa', 'https://www.tiktok.com/@danya1.milok'),
            ('https://www.tiktok.com/@kingx.music', 'https://www.tiktok.com/@kingx.music'),
            ('https://www.tiktok.com/@kingx.music?some_query=asddffsa', 'https://www.tiktok.com/@kingx.music'),
        ]
        for link, res in links_res:
            # успешный кейс, scope - ALL
            validated_link = self.validator.validate(link, scopes=ValidationScopes.ALL)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # успешный кейс, scope - empty
            validated_link = self.validator.validate(link)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # успешный кейс, scope - user
            validated_link = self.validator.validate(link, scopes=ValidationScopes.TIKTOK_USER)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # неуспешный кейс, scope - music
            validated_link = self.validator.validate(link, scopes=ValidationScopes.TIKTOK_MUSIC)
            self.assertIsNone(validated_link)

            # неуспешный кейс, scope - yt user
            validated_link = self.validator.validate(link, scopes=ValidationScopes.YOUTUBE_USER)
            self.assertIsNone(validated_link)

    def test_incorrect_tt_user_url(self):
        """Проверяем невалидные ссылки на юзера в tiktok"""
        links: list[str] = [
            'http://www.tiktok.com/@danya1.milok',
            'http://www.tiktok.com/@danya1.milok?some_query=asddffsa',
            'https://www.1tiktok.com/@danya1.milok',
            'https://www.1tiktok.com/@danya1.milok?some_query=asddffsa',
            'https://www.tiktok.kom/@kingx.music',
            'https://www.tiktok.kom/@kingx.music?some_query=asddffsa',
            'https://www.tiktok.com/zxc213@kingx.music?some_query=asddffsa',
        ]
        for link in links:
            for scope in ValidationScopes.all_scopes:
                validated_link = self.validator.validate(link, scopes=scope)
                self.assertIsNone(validated_link)

    def test_correct_youtube_user_url(self):
        """Проверяем валидные ссылки на пользователя в youtube"""
        link_res: list[tuple[str, str]] = [
            ('https://youtube.com/@officialphonkmusic?si=m1fGBNlqthSp1_Zd', 'https://youtube.com/@officialphonkmusic'),
            ('https://youtube.com/@officialphonkmusic', 'https://youtube.com/@officialphonkmusic'),
            ('https://www.youtube.com/@skazhigordeevoy?q=a', 'https://www.youtube.com/@skazhigordeevoy'),
            ('https://www.youtube.com/@skazhigordeevoy', 'https://www.youtube.com/@skazhigordeevoy'),
        ]

        for link, res in link_res:
            # успешный кейс, scope - ALL
            validated_link = self.validator.validate(link, scopes=ValidationScopes.ALL)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # успешный кейс, scope - empty
            validated_link = self.validator.validate(link)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # успешный кейс, scope - user
            validated_link = self.validator.validate(link, scopes=ValidationScopes.YOUTUBE_USER)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # неуспешный кейс, scope - music
            validated_link = self.validator.validate(link, scopes=ValidationScopes.YOUTUBE_MUSIC)
            self.assertIsNone(validated_link)

            # неуспешный кейс, scope - tt user
            validated_link = self.validator.validate(link, scopes=ValidationScopes.TIKTOK_USER)
            self.assertIsNone(validated_link)

    def test_incorrect_youtube_user_url(self):
        """Проверяем невалидные ссылки на youtube пользователя"""
        links: list[str] = [
            'http://www.youtube.com/@danya1.milok',
            'http://www.youtube.com/@danya1.milok?some_query=asddffsa',
            'https://www.1youtube.com/@danya1.milok',
            'https://www.1youtube.com/@danya1.milok?some_query=asddffsa',
            'https://www.youtube.kom/@kingx.music',
            'https://www.youtube.kom/@kingx.music?some_query=asddffsa',
        ]
        for link in links:
            for scope in ValidationScopes.all_scopes:
                validated_link = self.validator.validate(link, scopes=scope)
                self.assertIsNone(validated_link)

    def test_correct_youtube_music_url(self):
        """Проверяем валидные ссылки на youtube музыку"""
        links_res: list[tuple[str, str]] = [
            ('https://youtube.com/source/asfvzc1232/shorts', 'https://youtube.com/source/asfvzc1232/shorts'),
            ('https://youtube.com/source/asfvzc1232/shorts?si=Z-v366gPFTMQeGia', 'https://youtube.com/source/asfvzc1232/shorts'),
            ('https://youtube.com/source/ZmKk4krdy84/shorts', 'https://youtube.com/source/ZmKk4krdy84/shorts'),
            ('https://youtube.com/source/ZmKk4krdy84/shorts?si=Z-v366gPFTMQeGia', 'https://youtube.com/source/ZmKk4krdy84/shorts'),
        ]
        for link, res in links_res:
            # успешный кейс, scope - ALL
            validated_link = self.validator.validate(link, scopes=ValidationScopes.ALL)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # успешный кейс, scope - empty
            validated_link = self.validator.validate(link)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # успешный кейс, scope - music
            validated_link = self.validator.validate(link, scopes=ValidationScopes.YOUTUBE_MUSIC)
            self.assertIsNotNone(validated_link)
            self.assertEqual(validated_link, res)

            # неуспешный кейс, scope - user
            validated_link = self.validator.validate(link, scopes=ValidationScopes.YOUTUBE_USER)
            self.assertIsNone(validated_link)

            # неуспешный кейс, scope - tt user
            validated_link = self.validator.validate(link, scopes=ValidationScopes.TIKTOK_USER)
            self.assertIsNone(validated_link)

    def test_incorrect_youtube_music_url(self):
        """Проверяем невалидные ссылки на youtube музыку"""
        links: list[str] = [
            'http://www.youtube.com/source/asfvzc1232/shorts',
            'http://www.youtube.com/source/asfvzc1232/shorts?some_query=asddffsa',
            'https://www.1youtube.com/source/asfvzc1232/shorts',
            'https://www.1youtube.com/source/asfvzc1232/shorts?some_query=asddffsa',
            'https://www.youtube.kom/source/asfvzc1232/shorts',
            'https://www.youtube.kom/source/asfvzc1232/shorts?some_query=asddffsa',
        ]
        for link in links:
            for scope in ValidationScopes.all_scopes:
                validated_link = self.validator.validate(link, scopes=scope)
                self.assertIsNone(validated_link)
