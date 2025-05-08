import os
import requests
from django.db import models
from shop.models import Shop, Agent


class Post(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to="posts/")
    document = models.FileField(upload_to="documents/%Y/%m/%d/", blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Изображение для {self.shop.shop_name} ({self.id})"

    def delete(self, *args, **kwargs):
        image_path = self.image.path if self.image else None
        super().delete(*args, **kwargs)
        if image_path and os.path.isfile(image_path):
            os.remove(image_path)

    def save(self, *args, **kwargs):
        if self.latitude and self.longitude and not self.address:
            self.address = self.get_address_from_coordinates()
        super().save(*args, **kwargs)

    def get_address_from_coordinates(self):
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": self.latitude,
                    "lon": self.longitude,
                    "format": "json",
                },
                headers={"User-Agent": "DjangoApp"},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("display_name")
        except Exception as e:
            print(f"Ошибка при получении адреса: {e}")
        return None


class PostAgent(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="posts")
    shop = models.CharField(max_length=100)
    image = models.ImageField(upload_to="posts/")
    document = models.FileField(upload_to="documents/%Y/%m/%d/", blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Изображение для {self.shop} ({self.id})"

    def delete(self, *args, **kwargs):
        image_path = self.image.path if self.image else None
        super().delete(*args, **kwargs)
        if image_path and os.path.isfile(image_path):
            os.remove(image_path)

    def save(self, *args, **kwargs):
        if self.latitude and self.longitude and not self.address:
            self.address = self.get_address_from_coordinates()
        super().save(*args, **kwargs)

    def get_address_from_coordinates(self):
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": self.latitude,
                    "lon": self.longitude,
                    "format": "json",
                },
                headers={"User-Agent": "DjangoApp"},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("display_name")
        except Exception as e:
            print(f"Ошибка при получении адреса: {e}")
        return None
