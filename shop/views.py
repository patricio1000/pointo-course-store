from django.shortcuts import get_object_or_404, render
from cart.forms import CartAddProductForm
from .models import Category, Product


def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(available=True).select_related('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'shop/product/list.html', {
        'category': category, 'categories': Category.objects.all(), 'products': products,
    })


def product_detail(request, id, slug):
    product = get_object_or_404(Product.objects.select_related('category'), id=id, slug=slug, available=True)
    return render(request, 'shop/product/detail.html', {'product': product, 'cart_product_form': CartAddProductForm()})
