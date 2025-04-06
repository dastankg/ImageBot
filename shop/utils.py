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

    # Define headers
    columns = ["ID", "Shop", "Image", "Created"]
    ws.append(columns)

    # Write data
    for shop in queryset:
        posts = Post.objects.filter(shop=shop)
        for post in posts:
            ws.append(
                [
                    post.id,
                    shop.shop_name,
                    'http://139.59.2.151:8000/media'+str(post.image),
                    post.created.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

    wb.save(response)
    return response
