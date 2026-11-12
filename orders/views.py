import uuid
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem


def order_create(request):
    cart = Cart(request)
    token = request.session.get('checkout_token')
    # A double-click or repeated POST returns the same receipt, not another order.
    if request.method == 'POST' and token and request.POST.get('checkout_token') == token:
        existing = Order.objects.filter(checkout_token=token).first()
        if existing:
            order_ids = request.session.get('order_ids', [])
            if existing.id not in order_ids:
                # A concurrent request can still hold the pre-checkout session.
                request.session['order_ids'] = (order_ids + [existing.id])[-20:]
                cart.clear()
            return redirect('orders:order_created', order_id=existing.id)
    if not len(cart):
        messages.info(request, 'Your cart is empty. Add a product before checking out.')
        return redirect('shop:product_list')
    if request.method == 'GET':
        if not token or Order.objects.filter(checkout_token=token).exists():
            token = str(uuid.uuid4())
            request.session['checkout_token'] = token
        form = OrderCreateForm(initial={'checkout_token': token})
    else:
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            if str(form.cleaned_data['checkout_token']) != token:
                form.add_error(None, 'This checkout expired. Open checkout again from your cart.')
            else:
                items = list(cart)
                try:
                    with transaction.atomic():
                        order = form.save(commit=False)
                        order.checkout_token = form.cleaned_data['checkout_token']
                        order.save()
                        for item in items:
                            OrderItem.objects.create(order=order, product=item['product'], product_name=item['product'].name, price=item['price'], quantity=item['quantity'])
                except IntegrityError:
                    # The unique token arbitrates concurrent duplicate submissions.
                    # Any unrelated integrity error is still raised rather than hidden.
                    order = Order.objects.filter(checkout_token=form.cleaned_data['checkout_token']).first()
                    if order is None:
                        raise
                request.session['order_ids'] = (request.session.get('order_ids', []) + [order.id])[-20:]
                cart.clear()
                return redirect('orders:order_created', order_id=order.id)
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})


def order_created(request, order_id):
    # Sequential order IDs alone are not permission to view another customer's receipt.
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id, id__in=request.session.get('order_ids', []))
    return render(request, 'orders/order/created.html', {'order': order})
