from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

User = get_user_model()


class Product(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField(unique=True)
    image_url = models.URLField(null=True, blank=True)
    followers = models.ManyToManyField(
        User, related_name='products_following', blank=True)

    def __str__(self):
        return f'{self.name} ({self.url})'


class PriceRecord(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='prices')
    price = models.DecimalField(max_digits=15, decimal_places=2)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.name} ${self.price} ({self.registered_at})'
