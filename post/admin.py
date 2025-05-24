from django.contrib import admin

from post.models import Post, PostAgent


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    exclude = ("latitude", "longitude")
    list_display = ("shop", "address", "created")
    list_filter = ("shop", "created")
    search_fields = ("shop__shop_name", "address")


@admin.register(PostAgent)
class PostAgentAdmin(admin.ModelAdmin):
    exclude = ("latitude", "longitude")
    list_display = ("agent", "shop", "address", "post_type", "created")
    list_filter = ("agent", "created")
    search_fields = ("shop", "address")
