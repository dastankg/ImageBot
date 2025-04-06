from django.db import models

# Create your models here.


class TgUser(models.Model):
    telegram_id = models.BigIntegerField()
    phone_number = models.BigIntegerField()
