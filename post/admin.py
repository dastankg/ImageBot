from django.contrib import admin

from post.models import Post, PostAgent


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    exclude = ("latitude", "longitude")  # Hide these fields in the admin form
    list_display = ("id", "shop", "address", "created")
    list_filter = ("shop", "created")
    search_fields = ("shop__shop_name", "address")
    readonly_fields = ("address",)  # Make address read-only


@admin.register(PostAgent)
class PostAgentAdmin(admin.ModelAdmin):
    exclude = ("latitude", "longitude")
    list_display = ("id", "agent")
