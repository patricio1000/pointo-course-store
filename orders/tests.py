from decimal import Decimal
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from shop.models import Category, Product
from .models import Order, OrderItem


class OrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Paper rolls', slug='paper-rolls', kind='paper')
        cls.roll = Product.objects.create(category=category, name='Demo Roll', slug='demo-roll', price=Decimal('4.50'), width_mm=80, length_m=80)

    def begin_checkout(self, quantity=2):
        self.client.post(reverse('cart:cart_add', args=[self.roll.id]), {'quantity': quantity})
        response = self.client.get(reverse('orders:order_create'))
        self.assertEqual(response.status_code, 200)
        return {'first_name': 'Demo', 'last_name': 'Customer', 'email': 'demo@example.test', 'address': '123 Example Street', 'postal_code': '00000', 'city': 'Example City', 'checkout_token': self.client.session['checkout_token']}

    def test_checkout_creates_order_items_and_clears_cart(self):
        response = self.client.post(reverse('orders:order_create'), self.begin_checkout())
        order = Order.objects.get()
        self.assertRedirects(response, reverse('orders:order_created', args=[order.id]))
        item = order.items.get()
        self.assertEqual(item.product, self.roll)
        self.assertEqual(item.product_name, 'Demo Roll')
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal('4.50'))
        self.assertEqual(order.get_total_cost(), Decimal('9.00'))
        self.assertFalse(order.paid)
        self.assertNotIn(settings.CART_SESSION_ID, self.client.session)
        receipt = self.client.get(response.url)
        self.assertContains(receipt, f'PRACTICE ORDER #{order.id}')
        self.assertContains(receipt, '<span class="badge">0</span>', html=True)

    def test_checkout_multiple_products(self):
        data = self.begin_checkout()
        second = Product.objects.create(category=self.roll.category, name='Second Roll', slug='second', price=Decimal('2.75'), width_mm=58, length_m=30)
        self.client.post(reverse('cart:cart_add', args=[second.id]), {'quantity': 3})
        self.client.post(reverse('orders:order_create'), data)
        order = Order.objects.get()
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.get_total_cost(), Decimal('17.25'))

    def test_invalid_order_preserves_cart_and_creates_nothing(self):
        data = self.begin_checkout()
        data['email'] = 'invalid-email'
        data['first_name'] = ''
        response = self.client.post(reverse('orders:order_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(OrderItem.objects.exists())
        self.assertEqual(self.client.session[settings.CART_SESSION_ID][str(self.roll.id)]['quantity'], 2)
        self.assertContains(response, 'Enter a valid email address.')

    def test_empty_cart_cannot_checkout(self):
        for method in [self.client.get, self.client.post]:
            self.assertRedirects(method(reverse('orders:order_create')), reverse('shop:product_list'))
        self.assertFalse(Order.objects.exists())

    def test_duplicate_post_creates_only_one_order(self):
        data = self.begin_checkout()
        first = self.client.post(reverse('orders:order_create'), data)
        second = self.client.post(reverse('orders:order_create'), data)
        self.assertEqual(first.url, second.url)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_wrong_checkout_token_is_rejected(self):
        data = self.begin_checkout()
        data['checkout_token'] = str(uuid.uuid4())
        response = self.client.post(reverse('orders:order_create'), data)
        self.assertContains(response, 'This checkout expired.')
        self.assertFalse(Order.objects.exists())

    def test_missing_checkout_token_is_rejected(self):
        data = self.begin_checkout()
        del data['checkout_token']
        response = self.client.post(reverse('orders:order_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())

    def test_second_order_receives_new_token(self):
        first_data = self.begin_checkout()
        self.client.post(reverse('orders:order_create'), first_data)
        second_data = self.begin_checkout()
        self.assertNotEqual(first_data['checkout_token'], second_data['checkout_token'])
        self.client.post(reverse('orders:order_create'), second_data)
        self.assertEqual(Order.objects.count(), 2)

    def test_receipt_is_private_to_owning_session(self):
        response = self.client.post(reverse('orders:order_create'), self.begin_checkout())
        self.assertEqual(Client().get(response.url).status_code, 404)
        self.assertEqual(self.client.get(response.url).status_code, 200)

    def test_order_retains_original_name_and_price(self):
        self.client.post(reverse('orders:order_create'), self.begin_checkout())
        self.roll.name = 'Renamed Roll'
        self.roll.price = Decimal('100.00')
        self.roll.save()
        order = Order.objects.get()
        self.assertEqual(order.items.get().product_name, 'Demo Roll')
        self.assertEqual(order.get_total_cost(), Decimal('9.00'))

    def test_product_deletion_does_not_erase_order_history(self):
        self.client.post(reverse('orders:order_create'), self.begin_checkout())
        self.roll.delete()
        item = OrderItem.objects.get()
        self.assertIsNone(item.product)
        self.assertEqual(item.get_cost(), Decimal('9.00'))

    def test_order_and_item_string_representations(self):
        self.client.post(reverse('orders:order_create'), self.begin_checkout())
        order = Order.objects.get()
        self.assertEqual(str(order), f'Practice order {order.id}')
        self.assertEqual(str(order.items.get()), '2 × Demo Roll')

    def test_admin_shows_persisted_order_items(self):
        self.client.post(reverse('orders:order_create'), self.begin_checkout())
        order = Order.objects.get()
        user = get_user_model().objects.create_superuser('testadmin', 'admin@example.test', 'test-only-password')
        self.client.force_login(user)
        response = self.client.get(reverse('admin:orders_order_change', args=[order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo Roll')
        self.assertContains(response, '4.50')

    def test_duplicate_post_with_stale_session_recovers_receipt(self):
        data = self.begin_checkout()
        stale_data = dict(self.client.session)
        first = self.client.post(reverse('orders:order_create'), data)
        # Simulate a second request that read the session before the first completed.
        session = self.client.session
        session.clear()
        session.update(stale_data)
        session.save()
        second = self.client.post(reverse('orders:order_create'), data)
        self.assertRedirects(second, first.url)
        self.assertEqual(Order.objects.count(), 1)
        self.assertNotIn(settings.CART_SESSION_ID, self.client.session)
        self.assertIn(Order.objects.get().id, self.client.session['order_ids'])

    def test_checkout_integrity_race_returns_existing_order(self):
        from unittest.mock import patch
        data = self.begin_checkout()
        existing = Order.objects.create(
            first_name='Demo', last_name='Customer', email='demo@example.test',
            address='123 Example Street', postal_code='00000', city='Example City',
            checkout_token=data['checkout_token'])
        OrderItem.objects.create(order=existing, product=self.roll, product_name=self.roll.name, price=self.roll.price, quantity=2)
        # First lookup sees no order; the competing request saves before this insert.
        real_filter = Order.objects.filter
        calls = 0
        def racing_filter(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return real_filter(id=-1)
            return real_filter(*args, **kwargs)
        with patch.object(Order.objects, 'filter', side_effect=racing_filter):
            response = self.client.post(reverse('orders:order_create'), data)
        self.assertRedirects(response, reverse('orders:order_created', args=[existing.id]))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
