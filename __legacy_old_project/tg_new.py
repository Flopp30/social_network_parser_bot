from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ContentType
import asyncio
import time
from models import Channels, Rows
from cfg import tg_token, tg_xaw, autorized, id_owner
from keyb import uniKeyb

from you_post import startYoutubeParser
from tiktok_pw import startTikTokParser
from insta_rapi import startInstaParser

#from keyb import *
from toolbox import TM, digZero
from xls_saver import saveToXls, createXLS

from pwee import getStatReport, dbTextFinderCount

import os

#from youtube_lib import get_youtube_top_videos, getTextToTG, getShortsFromVideo
#from you_post import yotube_get_shorts_data
#from insta_uc_lib import selba_inst, instaToTG
#from tik_tok import get_tik_tok, tiktokToTG
#from tiktok_asreq import TIKTOK_asreq

bot = Bot(token = tg_token,
          parse_mode = types.ParseMode.HTML,
          disable_web_page_preview = True)

dp = Dispatcher(bot)

users = {}
URLS = {'tiktok': 'https://www.tiktok.com/music/{}',
        'instagram': 'https://www.instagram.com/reels/audio/{}',
        'youtube': 'https://www.youtube.com/source/{}/shorts',
        }


def getRootMess():
    total_col = Rows.select().count()
    tg_str = f"<b>Выбери площадку:</b>\nВ базе всего : <b>{digZero(total_col)}</b> строк"
    buttons = [[["TIKTOK", "ROOT|tiktok"]], [["INSTAGRAM", "ROOT|instagram"]], [["YOUTUBE", "ROOT|youtube"]], ]
    return tg_str, buttons

def aboutTrackDesk(chan_id,find_track = None):
    track = Channels.get_by_id(chan_id)
    rows_col = Rows.select().where(Rows.chan==track.id).count()
    status = "✅ Собираются данные." if track.active else "❌ На паузе"
    tg_str = f"Что сделаем с треком : \n<b>{track.tip.upper()}\n{track.name}</b>\n{URLS[track.tip].format(track.music)}\n\nСтатус : {status}\nв базе : <b>{digZero(rows_col)}</b> строк"
    action = ["⏸ На паузу", f"PAUSE|{chan_id}|0"] if track.active else ["▶️ Запуск", f"PAUSE|{chan_id}|1"]
    back = ["🔙 Назад", f"ROOT|{track.tip}"] if find_track is None else ["🔙 ПОИСК", f"FIND|{find_track}"]
    buttons = [
        [action, ["💾 ФАЙЛ", f"XLS|{chan_id}"]],
        [back, ["❌ Закрыть", "CANCEL"]],
    ]
    return tg_str, buttons

async def sendXLStoTG(message, track, rows):
    try:
        xls_filename = createXLS(track, rows)
        await message.answer_document(document=open(xls_filename, 'rb'))
        os.remove(xls_filename)
    except Exception as ex:
        print(ex)
        await message.answer(f"Что то пошло не так при отправке файла.\n{ex}")

@dp.message_handler(commands=["start"])
async def cmd_mypolls(message: types.Message):
    user_id = message.from_user.id
    user = message.from_user
    if user_id not in autorized :
        await message.answer(f'<code>{user.id}</code>\n@{user.username} {user.full_name}\nДоступ ограничен')
    else:
        tg_str, buttons = getRootMess()
        await message.answer(text=tg_str, reply_markup=uniKeyb(buttons))

@dp.message_handler(commands=["report"])
async def cmd_mypolls(message: types.Message):
    user_id = message.from_user.id
    user = message.from_user
    if user_id not in autorized :
        await message.answer(f'<code>{user.id}</code>\n@{user.username} {user.full_name}\nДоступ ограничен')
    else:
        tg_str = getStatReport()
        await message.answer(text=tg_str)

@dp.message_handler( content_types = ContentType.TEXT )
async def any_msg(message: types.Message):
    user = message.from_user
    if user.id not in autorized: return
    print(f"{TM()} TEXT : {user.id} @{user.username} {user.full_name}")
    rows = message.text.split('\n')
    ORDER = {}
    for u in rows:
        # https://www.tiktok.com/music/City-7197505126058330114
        # https://www.youtube.com/source/w1JjPvLAzRE/shorts?bp=8gVeClESQgoLdzFKalB2TEF6UkUSC3cxSmpQdkxBelJFGgtja09CV1RjRlJzRSINCLgZEggINhDAx93UAyoKEggINhDAx93UAxoLY2tPQldUY0ZSc0UosZv19v2O7ruIAQ%253D%253D
        # https://www.instagram.com/reels/audio/548503650698790/
        if len(u)<1 : continue
        cu = u[:-1] if '/' == u[-1] else u
        if 'tiktok' in cu:
            music_id = cu.split('/')[-1]
            tip = 'tiktok'

        elif 'instagram' in cu:
            music_id = cu.split('/')[-1]
            tip = 'instagram'
        elif 'youtube' in cu:
            music_id = cu.split('/shorts')[0].split('/')[-1]
            tip = 'youtube'
        else:
            continue
        if ORDER.get(tip) is None : ORDER[tip] = []
        ORDER[tip].append(music_id)
    buttons = None
    if len(ORDER) > 0 :
        tg_str = "Новые треки для парсинга:"
        new_chans = 0
        for tip, ids in ORDER.items():
            id_str = ''
            for i, music_id in enumerate(ids, start=1):
                if Channels.get_or_none(music=music_id) :
                    id_str += f"\n➖ {music_id} в базе"
                    continue
                id_str += f"\n➕ {i}. {music_id}"
                Channels.create_new(tip, music_id)
                new_chans+=1
            tg_str += f"\n <b>{tip.upper()}</b> :{id_str}"

        buttons = [[['Спарсить новые','PARSENEW']]]
        if new_chans ==0:
            tg_str += "\n\nНе найдено ссылок на НОВЫЕ треки"
            buttons = None
    else:
        tg_str = "Не найдено ссылок для загрузки."
        query = dbTextFinderCount(text = message.text, counter=True)
        print(f"{query=}")
        if query>0:
            tg_str+=f"\nНо найдено {query} записей по названию:\n<code>{message.text}</code>"
            buttons = [[["Показать",f"FIND|{message.text.lower()}"]]]

    await message.answer(tg_str, reply_markup=uniKeyb(buttons))

@dp.callback_query_handler(lambda callback_query: True)
async def callback_query_all(call: types.CallbackQuery):
    global users
    message = call.message
    user = message.chat
    if user.id not in autorized : return

    cb = call.data.split("|")
    print(f"\n{message.chat.full_name} : {cb=}")
    ON_PG = 7
    if cb[0]=='ROOT':
        if len(cb)==1:
            tg_str, buttons = getRootMess()
        else:
            tip = cb[1]
            pg = 0 if len(cb)==2 else int(cb[2])
            print(f"{pg=}")
            tracks = Channels.select().where(Channels.tip==tip).order_by(Channels.start)
            total_col = Rows.select().join(Channels).where(Channels.tip==tip).count()
            buttons = []
            for t in tracks[pg*ON_PG:(pg+1)*ON_PG]:
                nm = t.music if t.name is None else t.name
                sym = '✅' if t.active else '❌'
                buttons.append([[f"{sym} {nm[:30]}", f"TRACK|{t.id}"]])

            total_tracks= tracks.count()
            if total_tracks > ON_PG :

                prev_pg = pg-1
                if prev_pg < 0 : prev_pg = total_tracks // ON_PG

                next_pg = pg+1
                if next_pg > total_tracks // ON_PG: next_pg = 0

                print(f"{total_tracks=}\n{prev_pg=}\n{next_pg=}")
                buttons.append([[f"⬅️⬅️ [ {prev_pg} ]", f"ROOT|{tip}|{prev_pg}"], [f"➡️➡️[ {next_pg} ]", f"ROOT|{tip}|{next_pg}"], ])
            buttons.append([["🔙 Главное", "ROOT"],["❌ Закрыть", "CANCEL"],])
            tg_str = f"<b>{tip.upper()}</b>\nВыбери трек:\nВ разделе всего : <b>{digZero(total_col)}</b> строк"

        await message.edit_text(text = tg_str, reply_markup=uniKeyb(buttons))

    if cb[0] == 'PARSENEW':
        await message.edit_reply_markup(None)
        wait = await message.answer("Желательно ничего не делать с ботом пока идет загрузка")

        tm_start = int(time.time())-60*1
        new_chans = Channels.select().where(Channels.start>=tm_start)

        if new_chans.count()>0:
            print("start parse!")
            ORDER = {}
            for ch in new_chans:
                if ORDER.get(ch.tip) is None : ORDER[ch.tip] = []
                ORDER[ch.tip].append(ch.music)
                print(f"{ch.tip} {ch.music}")
                start_mess = await message.answer(f"START {ch.tip} {ch.music}")
                tg_str = f"Еще не прикручен парсер под {ch.tip}"
                if ch.tip == 'youtube':
                    tg_str = startYoutubeParser([ch.music])
                elif ch.tip == 'tiktok':
                    tg_str = await startTikTokParser([ch.music])
                elif ch.tip == 'instagram':
                    #pass
                    tg_str = startInstaParser([ch.music])

                track = Channels.get_by_id(ch.music)
                rows = Rows.select().where((Rows.chan == track.id))
                if rows.count():
                    await sendXLStoTG(message, track, rows)
                    tg_str += f"\n\n<b>{digZero(rows.count())} строк</b>"
                else:
                    tg_str += "\n\n <b>Пока нечего выгружать.</b>"
                await start_mess.edit_text(tg_str)
            print(f"{ORDER=}")
        else:
            print("no new channels to parse!")

        await wait.delete()
        await message.answer("Готово! Можно работать дальше.")

    if cb[0] == 'FIND':
        text = cb[1]
        tracks = dbTextFinderCount(text)
        buttons = []
        TT = {'tiktok':'🎵',
              'instagram':'📷',
              'youtube':'▶️'
              }
        for t in tracks:
            nm = t.music if t.name is None else t.name
            buttons.append([[f"{TT.get(t.tip,'')} {nm[:30]}", f"TRACK|{t.id}|{text}"]])
        buttons.append([["❌ Закрыть", "CANCEL"]])
        tg_str = f"Найдено по запросу : <b>{text}</b>\nВыбери трек:"
        await message.edit_text(text=tg_str, reply_markup=uniKeyb(buttons))

    if cb[0]=='TRACK':
        chan_id = int(cb[1])
        text = cb[-1] if len(cb)>2 else None
        tg_str, buttons = aboutTrackDesk(chan_id, find_track = text)
        await message.edit_text(text=tg_str, reply_markup=uniKeyb(buttons))

    if cb[0]=='PAUSE':
        chan_id = int(cb[1])
        new_active = bool(int(cb[2]))
        Channels.update(active=new_active).where(Channels.id==chan_id).execute()
        tg_str, buttons = aboutTrackDesk(chan_id)
        await message.edit_text(text="🔄 Обновленно.\n"+tg_str, reply_markup=uniKeyb(buttons))

    if cb[0]=='XLS':
        chan_id = int(cb[1])
        track = Channels.get_by_id(chan_id)

        tg_str = f"<b>💾 {track.tip.upper()}\nФайл по треку:</b> \n{URLS[track.tip].format(track.music)}"
        #print(track.__data__)
        #if track.tip in ['instagram', 'tiktok'] :
        rows = Rows.select().where((Rows.chan==track.id))

        if rows.count():
            await sendXLStoTG(message, track, rows)
            tg_str += f"\n\n<b>{digZero(rows.count())} строк</b>"
        else:
            tg_str += "\n\n <b>Пока нечего выгружать.</b>"
        try:
            await message.edit_text(text=tg_str, reply_markup=message.reply_markup)
        except Exception as ex:
            print(ex)


    if cb[0]=='CANCEL':
        await message.delete()

    try:
        await call.answer()
    except Exception as e:
        print(e)


async def main():
    current_bot = await bot.get_me()
    print(f"{TM()} STARTED BOT {current_bot=}\n{current_bot['username']=}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    executor.start_polling(dp, skip_updates=False)
