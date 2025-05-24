from django.db import models
from django.utils.translation import gettext_lazy as _


class Shop(models.Model):
    shop_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    manager_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    description = models.CharField(max_length=255, default="", blank=True)

    def __str__(self):
        return self.shop_name

    class Meta:
        verbose_name = _("ShelfRent")
        verbose_name_plural = _("ShelfRents")


class Telephone(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="telephones")
    number = models.CharField(max_length=20, db_index=True, unique=True)
    is_owner = models.BooleanField(default=False)
    chat_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.number


class Store(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Store Name"))
    address = models.TextField(blank=True, null=True, verbose_name=_("Address"))
    phone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name=_("Phone")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Market")
        verbose_name_plural = _("Markets")


class Agent(models.Model):
    agent_name = models.CharField(max_length=255, verbose_name=_("Agent Name"))
    agent_number = models.CharField(
        max_length=21, db_index=True, verbose_name=_("Agent Number")
    )

    monday_stores = models.ManyToManyField(
        Store, related_name="monday_agents", blank=True, verbose_name=_("Monday Stores")
    )
    tuesday_stores = models.ManyToManyField(
        Store,
        related_name="tuesday_agents",
        blank=True,
        verbose_name=_("Tuesday Stores"),
    )
    wednesday_stores = models.ManyToManyField(
        Store,
        related_name="wednesday_agents",
        blank=True,
        verbose_name=_("Wednesday Stores"),
    )
    thursday_stores = models.ManyToManyField(
        Store,
        related_name="thursday_agents",
        blank=True,
        verbose_name=_("Thursday Stores"),
    )
    friday_stores = models.ManyToManyField(
        Store, related_name="friday_agents", blank=True, verbose_name=_("Friday Stores")
    )
    saturday_stores = models.ManyToManyField(
        Store,
        related_name="saturday_agents",
        blank=True,
        verbose_name=_("Saturday Stores"),
    )
    sunday_stores = models.ManyToManyField(
        Store, related_name="sunday_agents", blank=True, verbose_name=_("Sunday Stores")
    )

    def __str__(self):
        return self.agent_name

    class Meta:
        verbose_name = _("Merchandiser")
        verbose_name_plural = _("Merchandisers")
