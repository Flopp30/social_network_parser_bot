from models import Channels, Rows, Parse
from peewee import fn
import time

from tg_reporter import sendSyncReport
from toolbox import getLink


def dbTextFinderCount(text, counter=False):
    text = text.lower()
    query = Channels.select().where((fn.LOWER(Channels.name).contains(text)) & (Channels.active == True))

    if counter:
        return query.count()
    else:
        return query.order_by(Channels.name.asc())


def getInstaActiveChannels():
    tracks = Channels.select().where((Channels.tip == 'instagram') & (Channels.active == True))
    return [_.music for _ in tracks]


def getActiveTracks(tip, music_list=None):
    tracks = Channels.select().where((Channels.tip == tip) & (Channels.active == True))

    if music_list:
        return {_.music: _.name for _ in tracks if _.music in music_list}
    else:
        return {_.music: _.name for _ in tracks}


def getReelsByTrack(music_id):
    rows = Rows.select().join(Channels).where(Channels.music == music_id)
    return [_.link for _ in rows]


def countReelsByTrack(music_id):
    col_rows = Rows.select().join(Channels).where(Channels.music == music_id).count()
    return col_rows


def dbSaveInstagram(res):
    if res['header'].get('music_id') is None:
        print(f"NO MUSIC ID : {res.get('header')=}")
        return 0
    music_id = res['header']['music_id']
    print(f"{res['header']=}")

    chan = Channels.get_or_none(music=music_id)
    if chan is None:
        chan = Channels.create_new(tip=res['header']['source'],
                                   music=res['header']['music_id'],
                                   name=res['header']['name'],
                                   )
    if chan:
        if res['header'].get('name'):
            if chan.name is None or chan.name != res['header']['name']:
                chan.name = res['header']['name']
                chan.save()

        if res['header'].get('duration'):
            if chan.duration is None:
                chan.duration = res['header'].get('duration')

        if res['header'].get('total'):
            if chan.total is None:
                chan.total = res['header'].get('total')
                chan.save()
            elif chan.total > res['header']['total'] * 1.01:
                chan.total = res['header']['total']
                chan.save()

        new_col = 0
        for item in res['items']:
            item['chan'] = chan.id
            is_new = Rows.create_new(**item)
            if is_new: new_col += 1
    else:
        new_col = -1

    return new_col


def dbSaveParseStat(music_id, plan, fact):
    Parse.create_new(music_id, plan, fact)


ONE_MIN = 60
ONE_HOUR = ONE_MIN * 60
ONE_DAY = ONE_HOUR * 24


def getStatReport(interval=ONE_DAY):
    now_time = int(time.time())
    from_time = now_time - interval
    posts = Parse.select().where(Parse.tm > from_time)
    res = {}
    for p in posts:
        tip = p.chan.tip
        music = p.chan.music
        if res.get(tip) is None: res[tip] = {}
        if res[tip].get(music) is None: res[tip][music] = {'name': p.chan.name, 'plan': 0, 'fact': 0}
        res[tip][music]['plan'] += p.plan
        res[tip][music]['fact'] += p.fact
        print(f"{tip} {p.chan.name}  {p.fact} / {p.plan}")

    tg_rep = "Добыто за последние сутки:"
    total_all = 0
    for tip in ['tiktok', 'instagram', 'youtube']:
        if res.get(tip) is None: continue
        tg_rep += f"\n<b>{tip}</b> :"
        total_tip = 0
        for music_id, dat in res[tip].items():
            total_tip += dat['fact']
            tg_rep += f"\n{dat['name']} : {dat['fact']} / {dat['plan']}"
        tg_rep += f"\nИтого : <b>{total_tip}</b>"
        total_all += total_tip
    tg_rep += f"\n\nВСЕГО : <b>{total_all}</b>"
    # sendSyncReport(text=tg_rep)
    return tg_rep


def main():
    qq = dbTextFinderCount(text='live')
    print(f"{qq.count()=}")
    for q in qq:
        print(q.name)
    return
    tg_rep = getStatReport()
    sendSyncReport(text=tg_rep)
    print(tg_rep)

    return
    music_id = 'w1JjPvLAzRE'
    reels = getReelsByTrack(music_id)
    print(reels)
    pass


if __name__ == '__main__':
    main()
   