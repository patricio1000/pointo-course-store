"""Session cart: only IDs and quantities are persisted; prices come from the database."""
from decimal import Decimal
from django.conf import settings
from shop.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get(settings.CART_SESSION_ID, {})
        # Remove deleted/unavailable products so stale sessions cannot buy them.
        valid_ids = set(str(pk) for pk in Product.objects.filter(id__in=[int(k) for k in self.cart if k.isdigit()], available=True).values_list('id', flat=True))
        cleaned = {k: v for k, v in self.cart.items() if k in valid_ids and isinstance(v, dict) and type(v.get('quantity')) is int and 1 <= v['quantity'] <= 99}
        if cleaned != self.cart:
            self.cart = cleaned
            self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        old_quantity = self.cart.get(product_id, {}).get('quantity', 0)
        new_quantity = quantity if override_quantity else old_quantity + quantity
        if not product.available or type(quantity) is not int or not 1 <= quantity <= 99 or not 1 <= new_quantity <= 99:
            raise ValueError('Choose a quantity from 1 to 99 per product.')
        self.cart[product_id] = {'quantity': new_quantity}
        self.save()

    def remove(self, product):
        if str(product.id) in self.cart:
            del self.cart[str(product.id)]
            self.save()

    def __iter__(self):
        products = Product.objects.filter(id__in=self.cart.keys(), available=True).select_related('category')
        for product in products:
            quantity = self.cart[str(product.id)]['quantity']
            # Do not insert Product/Decimal objects into the JSON-serialized session.
            yield {'product': product, 'quantity': quantity, 'price': product.price, 'total_price': product.price * quantity}

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum((item['total_price'] for item in self), Decimal('0.00'))

    def clear(self):
        self.cart = {}
        self.session.pop(settings.CART_SESSION_ID, None)
        self.session.modified = True
