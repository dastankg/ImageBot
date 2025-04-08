from django.db import models

class Shop(models.Model):
    shop_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    address = models.TextField()

    def __str__(self):
        return self.shop_name

class Telephone(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='telephones')
    number = models.CharField(max_length=20)

    def __str__(self):
        return self.number
