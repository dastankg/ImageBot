from django.contrib import admin

from post.models import Post, PostAgent


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    exclude = ("latitude", "longitude")
    list_display = ("id", "shop", "address", "created")
    list_filter = ("shop", "created")
    search_fields = ("shop__shop_name", "address")
    readonly_fields = ("address",)


@admin.register(PostAgent)
class PostAgentAdmin(admin.ModelAdmin):
    exclude = ("latitude", "longitude")
    list_display = ("id", "agent", "shop", "address", "created")
    list_filter = ("agent", "created")
    search_fields = ("shop", "address")
    readonly_fields = ("address",)