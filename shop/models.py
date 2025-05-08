from django.db import models


class Shop(models.Model):
    shop_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    manager_name = models.CharField(max_length=255)
    address = models.TextField()
    Region = models.CharField(max_length=255)
    Description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.shop_name


class Agent(models.Model):
    agent_name = models.CharField(max_length=255)
    agent_number = models.CharField(max_length=21, db_index=True)

    def __str__(self):
        return self.agent_name


class Telephone(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="telephones")
    number = models.CharField(max_length=20, db_index=True)

    def __str__(self):
        return self.number
