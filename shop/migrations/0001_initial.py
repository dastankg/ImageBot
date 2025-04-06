# Generated by Django 5.2 on 2025-04-03 14:56

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Shop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("shop_name", models.CharField(max_length=100)),
                ("address", models.CharField(max_length=100)),
                ("owner_name", models.CharField(max_length=100)),
                ("telephone", models.CharField(max_length=100)),
            ],
        ),
    ]
