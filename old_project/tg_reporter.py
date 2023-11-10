from aiogram import Bot, types, Dispatcher, executor
from cfg import tg_token, tg_xaw, REP_CHAN
import requests

bot = Bot(token=tg_token,
          parse_mode=types.ParseMode.HTML,
          disable_web_page_preview=True)


async def reportTG(chat_id=REP_CHAN, text='0'):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as ex:
        print(ex)


def sendPhoto(text='', photo=None):
    if photo is None: return None
    url = f"https://api.telegram.org/bot{tg_token}/sendPhoto"
    params = {"chat_id": str(CHAN_ID),
              "photo": photo,
              "caption": text,
              "parse_mode": "html",
              "disable_web_page_preview": 'true'}
    try:
        response = requests.post(url=url, data=params)
        result = response.json()
    except Exception as e:
        print(f"SEND ERR\n{e}")
        result = None
    return result


def sendSyncReport(chat_id=REP_CHAN, text=''):
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    params = {"chat_id": str(chat_id),
              "text": text,
              "parse_mode": "html",
              "disable_web_page_preview": 'true'}
    try:
        response = requests.post(url=url, data=params)
        result = response.json()
    except Exception as e:
        print(f"SEND ERR\n{e}")
        result = None
    return result


def main():
    sendSyncReport(text='TEST')


if __name__ == '__main__':
    main()
   