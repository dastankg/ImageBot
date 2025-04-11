from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django import forms
from openpyxl import Workbook
from datetime import datetime

from post.models import Post
from shop.models import Shop, Telephone


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="С даты (День/Месяц/Год)"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="По дату (День/Месяц/Год)"
    )


def export_posts_to_excel(modeladmin, request, queryset):
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    if 'apply' not in request.POST:
        form = DateRangeForm()
        context = {
            'queryset': queryset,
            'form': form,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return render(
            request,
            'export_date_range.html',
            context
        )

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="posts.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Posts"

    columns = ["ID", "Магазин", "Изображение", "Адрес", "Адрес магазина", "Дата", "Время"]
    ws.append(columns)

    for shop in queryset:
        posts = Post.objects.filter(shop=shop)

        if start_date:
            posts = posts.filter(created__gte=start_date)
        if end_date:
            posts = posts.filter(created__lte=end_date)

        for post in posts:
            ws.append(
                [
                    post.id,
                    shop.shop_name,
                    f"http://139.59.2.151:8000/media/{post.image}",
                    post.address,
                    shop.address,
                    post.created.strftime("%Y-%m-%d"),
                    post.created.strftime("%H:%M:%S"),
                ]
            )

        if posts:
            ws.append([])

    wb.save(response)
    return response


export_posts_to_excel.short_description = "Экспорт постов в Excel"


class TelephoneInline(admin.TabularInline):
    model = Telephone
    extra = 1


class PostInline(admin.TabularInline):
    model = Post
    extra = 1
    fields = ("image", "created", "address")
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

    get_telephones.short_description = "Телефоны"