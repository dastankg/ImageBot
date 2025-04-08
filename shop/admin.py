from django.contrib import admin
from post.models import Post
from shop.models import Shop, Telephone
from shop.utils import export_posts_to_excel

class TelephoneInline(admin.TabularInline):
    model = Telephone
    extra = 1


class PostInline(admin.TabularInline):
    model = Post
    extra = 1
    fields = ("image", "created")
    readonly_fields = ("created",)
    ordering = ("-created",)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("shop_name", "owner_name", "get_telephones", "address")
    search_fields = ("shop_name", "owner_name")
    list_filter = ("shop_name",)
    inlines = [TelephoneInline, PostInline]
    actions = [export_posts_to_excel]

    def get_telephones(self, obj):
        return ", ".join(t.number for t in obj.telephones.all())
    get_telephones.short_description = "Telephones"
