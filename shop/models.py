from django.db import models


class Shop(models.Model):
    shop_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    telephone = models.CharField(max_length=100)

    def __str__(self):
        return self.shop_name
