from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'kind']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'price', 'available', 'created']
    list_filter = ['available', 'created', 'category']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    fieldsets = [
        ('Catalog', {'fields': ('category', 'name', 'slug', 'image', 'description', 'price', 'available')}),
        ('Receipt printer specifications', {'fields': ('paper_width_mm', 'connection_type'), 'description': 'Fill in only for receipt printers.'}),
        ('Paper roll specifications', {'fields': ('width_mm', 'length_m'), 'description': 'Fill in only for paper rolls.'}),
        ('Tablet stand specifications', {'fields': ('tablet_size_inches', 'mount_type'), 'description': 'Fill in only for tablet stands.'}),
    ]

admin.site.site_header = 'Pointo Store Administration'
admin.site.site_title = 'Pointo Store'
admin.site.index_title = 'Practice store management'
