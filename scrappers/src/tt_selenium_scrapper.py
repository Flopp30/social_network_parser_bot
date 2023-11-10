import json
import logging
import os
import pickle
import random
import time
from json import JSONDecodeError

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from seleniumwire.utils import decode
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from seleniumwire import webdriver
import undetected_chromedriver as undetected_webdriver

headers = {
    "lang": "en-US,en;q=0.9",
    "referer": "https://google.com",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.9",

}

logger = logging.getLogger(__name__)


class TikTokBot:

    def __init__(self):
        self.os_type = random.choice(['linux', 'macos', 'windows'])
        service = ChromeService(
            executable_path=ChromeDriverManager().install()
        )
        webdriver_options = self._get_chrome_options(self.os_type)
        self.driver = webdriver.Chrome(
            service=service,
            options=webdriver_options
        )
        self.driver.maximize_window()
        # self.update_cookie(self.os_type)

    @staticmethod
    def _get_chrome_options(os_type):
        ua = UserAgent(browsers=['chrome'], os=[os_type])
        # chrome_options = webdriver.ChromeOptions()
        chrome_options = undetected_webdriver.ChromeOptions()
        # headers
        for h_name, h_value in headers.items():
            chrome_options.add_argument(f'--{h_name}={h_value}')
        chrome_options.add_argument(f'--user-agent={ua.random}')

        # Adding argument to disable the AutomationControlled flag
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # Exclude the collection of enable-automation switches
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # Turn-off userAutomationExtension
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # other settings
        # chrome_options.add_argument('--headless')  # hide browser window
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--use_subprocess")
        chrome_options.add_argument("--force-device-scale-factor=0.75")
        chrome_options.add_argument("--high-dpi-support=0.75")
        return chrome_options

    def update_cookie(self, os_type):
        """
            Need to fix
        """
        if not os.path.exists(f'cookies/{os_type}_cookies'):
            self.driver.get('https://www.tiktok.com/')
            with open(f"cookies/{os_type}_cookies", "wb") as cook_file:
                pickle.dump(
                    self.driver.get_cookies(),
                    cook_file
                )
            logger.error(f'{os_type} Cookie was updated successfully')
        with open(f"cookies/{os_type}_cookies", "rb") as cook_file:
            cookies = pickle.load(cook_file)
            for cookie in cookies:
                if cookie['domain'] == 'www.tiktok.com':
                    self.driver.add_cookie(cookie)

    def elem_exists(self, by: By, value: str):
        try:
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False

    def close_driver(self):
        self.driver.close()
        self.driver.quit()

    def parse_page(self, url: str):
        self.driver.get(url)
        while not self.elem_exists(By.CSS_SELECTOR, '[data-e2e="user-post-item"]'):
            logger.error('Жду контента')
            time.sleep(random.randint(1, 3))
            while self.elem_exists(By.XPATH, '//*[@id="main-content-others_homepage"]/div/div[2]/main/div/button'):
                self.driver.find_element(By.XPATH,
                                         '//*[@id="main-content-others_homepage"]/div/div[2]/main/div/button').click()
                logger.error('Нажал на кнопку рефреша')
                time.sleep(random.randint(1, 5))

        SCROLL_PAUSE_TIME = 5
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        self.driver.execute_script("document.body.style.zoom='70%'")
        while True:
            logger.error('Скроллю...')
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(SCROLL_PAUSE_TIME)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        logger.error('Начал обрабатывать запросы')
        parsed_stat = []
        urls = []
        for idx, request in enumerate(self.driver.requests, start=1):
            if 'tiktok.com/api/post/item_list/' in request.url and request.response:
                urls.append(
                    {
                        "id": idx,
                        "url": request.url
                    }
                )
                body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                try:
                    body = json.loads(body)
                    for item in body.get('itemList', []):
                        pk = item.pop("id", None)
                        stats = item.pop("stats", None)
                        desc = item.pop("desc", None)
                        author = item.pop('author').get('nickname')
                        if all((pk, stats)):
                            parsed_stat.append(
                                {
                                    "url": f"{url}/video/{pk}",
                                    "desc": desc,
                                    "author": author,
                                    "stat": stats,
                                }
                            )
                except JSONDecodeError:
                    pass
        if parsed_stat:
            data = {
                "items": parsed_stat
            }
            with open(f'parsed_stat.json', 'w') as file:
                json.dump(data, file, indent=4)
        if urls:
            data = {
                "urls": urls
            }
            with open('urls.json', 'w') as file:
                json.dump(data, file, indent=4)
        self.close_driver()


def main():
    tiktok_bot = TikTokBot()
    tiktok_bot.parse_page('https://www.tiktok.com/@kinoskranzi')


if __name__ == '__main__':
    main()
