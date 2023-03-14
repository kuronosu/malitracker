from django.contrib import admin

from .models import PriceRecord, Product

# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'url', 'image_url']


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ['pk', 'price', 'registered_at', 'product',]
