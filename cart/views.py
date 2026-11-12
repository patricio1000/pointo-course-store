from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
from .forms import CartAddProductForm


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, available=True)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        try:
            cart.add(product, form.cleaned_data['quantity'], form.cleaned_data['override'])
            messages.success(request, f'{product.name} updated in your cart.')
        except ValueError as error:
            messages.error(request, str(error))
    else:
        messages.error(request, 'Quantity must be a whole number from 1 to 99.')
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart(request).remove(product)
    messages.success(request, f'{product.name} removed from your cart.')
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    items = list(cart)
    for item in items:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'override': True}, auto_id=f"id_{item['product'].id}_%s")
    return render(request, 'cart/detail.html', {'cart': cart, 'items': items})
