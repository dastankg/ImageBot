from django.core.checks import messages
from django.http import HttpResponse
from django.shortcuts import render
from django import forms
from openpyxl import Workbook
from datetime import datetime
from post.models import Post, PostAgent
from django.contrib import admin
from django.utils.timezone import localtime


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "name": "start_date"}),
        required=False,
        label="С даты (День/Месяц/Год)",
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "name": "end_date"}),
        required=False,
        label="По дату (День/Месяц/Год)",
    )


def export_posts_to_excel(modeladmin, request, queryset):
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")
    if "apply" not in request.POST:
        form = DateRangeForm()
        context = {
            "queryset": queryset,
            "form": form,
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return render(request, "export_date_range.html", context)

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="posts.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Posts"

    columns = [
        "ID",
        "Магазин",
        "Изображение",
        "Адрес",
        "Адрес магазина",
        "Дата",
        "Время",
    ]
    ws.append(columns)

    for shop in queryset:
        posts = Post.objects.filter(shop=shop)

        if start_date:
            posts = posts.filter(created__gte=start_date)
        if end_date:
            posts = posts.filter(created__lte=end_date)

        for post in posts:
            local_created = localtime(post.created)
            ws.append(
                [
                    post.id,
                    shop.shop_name,
                    f"http://139.59.2.151:8000/media/{post.image}",
                    post.address,
                    shop.address,
                    local_created.strftime("%Y-%m-%d"),
                    local_created.strftime("%H:%M:%S"),
                ]
            )

        if posts:
            ws.append([])

    wb.save(response)
    return response


def export_agent_posts_to_excel(modeladmin, request, queryset):
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    if not queryset:
        modeladmin.message_user(
            request, "Не выбрано ни одного агента", level=messages.ERROR
        )
        return
    if "apply" not in request.POST:
        form = DateRangeForm()
        context = {
            "queryset": queryset,
            "form": form,
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return render(request, "export_date_range1.html", context)

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="agent_posts.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Agent Posts"

    columns = [
        "Имя Агента",
        "Имя Магазина",
        "Фото",
        "Геолокация",
        "Дата",
        "Время",
        "Разница времени",
    ]
    ws.append(columns)

    for agent in queryset:
        posts = PostAgent.objects.filter(agent=agent).order_by("created")

        if start_date:
            posts = posts.filter(created__gte=start_date)
        if end_date:
            posts = posts.filter(created__lte=end_date)

        posts_list = list(posts)
        previous_time = None
        total_work_time_minutes = 0

        for i, post in enumerate(posts_list):
            current_time = post.created
            local_created = localtime(post.created)
            time_diff_str = ""
            if previous_time and i % 2 != 0:
                time_diff = current_time - previous_time
                time_diff_minutes = time_diff.total_seconds() / 60
                time_diff_str = f"{time_diff_minutes:.2f} мин."
                total_work_time_minutes += time_diff_minutes

            row_data = [
                agent.agent_name,
                post.shop,
                f"http://139.59.2.151:8000/media/{post.image}",
                post.address,
                local_created.strftime("%Y-%m-%d"),
                local_created.strftime("%H:%M:%S"),
                time_diff_str,
            ]
            ws.append(row_data)
            previous_time = current_time

        if posts_list:
            ws.append([])

            work_start = posts_list[0].created if posts_list else None
            work_end = posts_list[-1].created if posts_list else None

            if work_start and work_end:
                total_day_minutes = (work_end - work_start).total_seconds() / 60
                work_percentage = (
                    (total_work_time_minutes / total_day_minutes * 100)
                    if total_day_minutes > 0
                    else 0
                )

                ws.append(
                    [
                        "Начало работы",
                        "Конец работы",
                        "Длительность рабочего дня",
                        "Реальное рабочее время",
                        "Процент рабочего времени",
                        "",
                        "",
                    ]
                )

                ws.append(
                    [
                        work_start.strftime("%H:%M:%S"),
                        work_end.strftime("%H:%M:%S"),
                        f"{total_day_minutes:.2f} мин.",
                        f"{total_work_time_minutes:.2f} мин.",
                        f"{work_percentage:.2f}%",
                        "",
                        "",
                    ]
                )

                ws.append([])

    wb.save(response)
    return response
