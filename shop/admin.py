from django.contrib import admin
from django import forms
from post.models import Post
from shop.models import Shop, Telephone, Agent, Store
from shop.utils import export_posts_to_excel, export_agent_posts_to_excel


class TelephoneInline(admin.TabularInline):
    model = Telephone
    extra = 1


class PostInline(admin.TabularInline):
    model = Post
    extra = 1
    fields = ("image", "created", "address")
    readonly_fields = ("created",)
    ordering = ("-created",)


class ManyToManyStoreWidget(forms.SelectMultiple):
    pass


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


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "phone")
    search_fields = ("name", "address")


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        "agent_name",
        "agent_number",

    )
    search_fields = ("agent_name", "agent_number")

    filter_horizontal = (
        "monday_stores",
        "tuesday_stores",
        "wednesday_stores",
        "thursday_stores",
        "friday_stores",
        "saturday_stores",
        "sunday_stores",
    )

    actions = [export_agent_posts_to_excel]

    def get_monday_stores(self, obj):
        return ", ".join([store.name for store in obj.monday_stores.all()])

    def get_tuesday_stores(self, obj):
        return ", ".join([store.name for store in obj.tuesday_stores.all()])

    def get_wednesday_stores(self, obj):
        return ", ".join([store.name for store in obj.wednesday_stores.all()])

    def get_thursday_stores(self, obj):
        return ", ".join([store.name for store in obj.thursday_stores.all()])

    def get_friday_stores(self, obj):
        return ", ".join([store.name for store in obj.friday_stores.all()])

    def get_saturday_stores(self, obj):
        return ", ".join([store.name for store in obj.saturday_stores.all()])

    def get_sunday_stores(self, obj):
        return ", ".join([store.name for store in obj.sunday_stores.all()])

    fieldsets = (
        (None, {"fields": ("agent_name", "agent_number")}),
        (
            "Назначения на магазины по дням",
            {
                "fields": (
                    "monday_stores",
                    "tuesday_stores",
                    "wednesday_stores",
                    "thursday_stores",
                    "friday_stores",
                    "saturday_stores",
                    "sunday_stores",
                )
            },
        ),
    )
