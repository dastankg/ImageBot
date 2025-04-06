from django.contrib import admin

from post.models import Post
from shop.models import Shop
from shop.utils import export_posts_to_excel


class PostInline(admin.TabularInline):
    model = Post
    extra = 1
    fields = ("image", "created")
    readonly_fields = ("created",)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("shop_name", "owner_name", "address", "telephone")
    search_fields = ("shop_name", "owner_name")
    list_filter = ("shop_name",)
    inlines = [PostInline]
    actions = [export_posts_to_excel]  # Добавляем действие экспорта
