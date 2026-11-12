from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'product_name', 'price', 'quantity']
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'city', 'created', 'paid']
    list_filter = ['created']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['created', 'updated', 'paid', 'checkout_token']
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        # Orders are created by validated checkout, not incomplete admin entries.
        return False
