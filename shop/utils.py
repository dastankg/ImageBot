from django.http import HttpResponse
from django.shortcuts import render
from django import forms
from openpyxl import Workbook
from datetime import datetime
from django.contrib import admin
from django.apps import apps

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

    Post = apps.get_model('post', 'Post')  # получаем модель динамически

    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    if 'apply' not in request.POST:
        form = DateRangeForm()
        context = {
            'queryset': queryset,
            'form': form,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return render(request, 'export_date_range.html', context)

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

    columns = ["ID", "Магазин", "Изображение", "Адрес", "Адрес магазина", "Дата", "Время", "MetaДата", "MetaВремя"]
    ws.append(columns)

    for shop in queryset:
        posts = Post.objects.filter(shop=shop)

        if start_date:
            posts = posts.filter(created__gte=start_date)
        if end_date:
            posts = posts.filter(created__lte=end_date)

        for post in posts:
            creation_time = post.creation_time
            if creation_time and creation_time.tzinfo:
                creation_time = creation_time.astimezone(tz=None).replace(tzinfo=None)

            ws.append([
                post.id,
                shop.shop_name,
                f"http://139.59.2.151:8000/media/{post.image}",
                post.address,
                shop.address,
                post.created.strftime("%Y-%m-%d"),
                post.created.strftime("%H:%M:%S"),
                creation_time.strftime("%Y-%m-%d") if creation_time else "",
                creation_time.strftime("%H:%M:%S") if creation_time else "",
            ])

        if posts:
            ws.append([])

    wb.save(response)
    return response


export_posts_to_excel.short_description = "Экспорт постов в Excel"
