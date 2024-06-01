import time

from peewee import *

db = SqliteDatabase('dbase.db')

class Channels(Model):
    tip = CharField()
    music = CharField()

    name = TextField(null=True)
    total = IntegerField(null=True)
    duration = SmallIntegerField(null=True)

    active = BooleanField(default=True)
    start = BigIntegerField()

    class Meta:
        database = db

    @classmethod
    def create_new(self, tip, music, name=None, total=None, duration=None):
        channel = self.get_or_none(music=music)
        if channel is None :
            channel = self.create(
                tip = tip,
                music=music,
                name=name,
                total=total,
                duration=duration,
                start=int(time.time()),
            )
        return channel

class Rows(Model):
    chan = ForeignKeyField(Channels)
    link = CharField()
    upload = IntegerField()
    views = IntegerField()
    likes = IntegerField()
    comments = IntegerField()
    resend = SmallIntegerField(null=True)
    saves = SmallIntegerField(null=True)
    duration = SmallIntegerField(null=True)
    tmupd = IntegerField()

    class Meta:
        database = db

    @classmethod
    def create_new(self, chan, link, upload, views, likes, comments, resend=None, saves=None, duration = None ):
        row = self.get_or_none(link=link)
        is_new = False
        if row is None :
            is_new = True
            row = self.create(
                chan =chan,
                link = link,
                upload=upload,
                views = int(views),
                likes=int(likes) if likes else 0,
                comments=int(comments) if comments else 0,
                resend=int(resend) if resend else 0,
                saves=int(saves) if saves else 0,
                duration=int(duration) if duration else 0,
                tmupd = int(time.time()),
                )
        else:
            re_save = False
            if row.views != views :
                row.views = views
                re_save = True
            if row.likes != views :
                row.likes = likes
                re_save = True
            if row.comments != comments :
                row.comments = comments
                re_save = True
            if row.resend != resend :
                row.resend = resend
                re_save = True
            if row.saves != saves :
                row.saves = saves
                re_save = True
            if re_save :
                row.tmupd = int(time.time())
                row.save()

        return is_new

class Parse(Model):
    chan = ForeignKeyField(Channels)
    tm = IntegerField()
    plan = SmallIntegerField()
    fact= SmallIntegerField()
    class Meta:
        database = db

    @classmethod
    def create_new(self, music_id, plan, fact):
        chan = Channels.get_or_none(music=music_id)
        if chan:
            self.create(
                chan =chan,
                tm = int(time.time()),
                plan = plan,
                fact = fact)

def main():
    db.connect()
    db.drop_tables([Parse]) # Channels, Rows
    db.create_tables([Channels, Rows, Parse], safe = True)

if __name__ == "__main__":
    main()
