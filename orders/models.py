"""Simulated orders preserve product names and prices at checkout."""
import uuid
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from shop.models import Product


class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False, editable=False)
    checkout_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Practice order {self.id}'

    def get_total_cost(self):
        return sum((item.get_cost() for item in self.items.all()), Decimal('0.00'))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    # Keep the receipt even if the manager later deletes a catalog product.
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(99)])

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gt=0), name='order_item_price_positive'),
            models.CheckConstraint(condition=models.Q(quantity__gte=1, quantity__lte=99), name='order_item_valid_quantity'),
        ]

    def __str__(self):
        return f'{self.quantity} × {self.product_name}'

    def get_cost(self):
        return self.price * self.quantity
