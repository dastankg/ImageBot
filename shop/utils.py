from django.http import HttpResponse
from openpyxl import Workbook

from post.models import Post


def export_posts_to_excel(modeladmin, request, queryset):
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="posts.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Posts"

    columns = ["ID", "Shop", "Image", "Address", "Created"]
    ws.append(columns)

    for index, shop in enumerate(queryset):
        posts = Post.objects.filter(shop=shop)

        for post in posts:
            ws.append(
                [
                    post.id,
                    shop.shop_name,
                    f"http://139.59.2.151:8000/media/{post.image}",
                    post.address,
                    post.created.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        if len(posts) != 0:
            ws.append([])

    wb.save(response)
    return response
