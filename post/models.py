import os

from django.db import models

from shop.models import Shop


class Post(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to="posts/")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Изображение для {self.shop.shop_name} ({self.id})"

    def delete(self, *args, **kwargs):
        if self.image:
            image_path = self.image.path
        else:
            image_path = None

        super().delete(*args, **kwargs)

        if image_path and os.path.isfile(image_path):
            os.remove(image_path)
