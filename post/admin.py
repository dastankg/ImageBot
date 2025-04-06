from django.contrib import admin

from post.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "image", "created")
    list_filter = ("shop", "created")
    date_hierarchy = "created"
