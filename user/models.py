from django.db import models


class User(models.Model):
    chat_id = models.BigIntegerField(
        verbose_name='Chat id',
        blank=False, null=False
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=100,
        blank=True, null=True,
    )
    state = models.CharField(
        verbose_name='Статус в переписке в боте',
        max_length=50,
        default="NEW",
    )
    last_visit_time = models.DateTimeField(
        verbose_name='Дата и время последнего посещения',
        auto_now=True,
    )
    registration_datetime = models.DateTimeField(
        verbose_name='Даты и время регистрации',
        auto_now_add=True,
    )
    is_approved = models.BooleanField(
        verbose_name='Подтвержден',
        default=False,
    )
    send_alerts = models.BooleanField(
        verbose_name='Слать оповещения?',
        default=False
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return f"{self.username if self.username else self.chat_id}"
