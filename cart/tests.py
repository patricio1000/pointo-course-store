from decimal import Decimal
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from shop.models import Category, Product


class CartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Paper rolls', slug='paper-rolls', kind='paper')
        cls.roll = Product.objects.create(category=category, name='Demo Roll', slug='demo-roll', price=Decimal('4.50'), width_mm=80, length_m=80)
        cls.small = Product.objects.create(category=category, name='Small Roll', slug='small-roll', price=Decimal('2.75'), width_mm=58, length_m=30)

    def add(self, quantity=1, override=False, product=None, client=None):
        return (client or self.client).post(reverse('cart:cart_add', args=[(product or self.roll).id]), {'quantity': quantity, 'override': override})

    def test_add_and_increment(self):
        self.add(2)
        self.add(1)
        self.assertEqual(self.client.session[settings.CART_SESSION_ID][str(self.roll.id)]['quantity'], 3)
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.context['cart'].get_total_price(), Decimal('13.50'))
        self.assertEqual(len(response.context['cart']), 3)

    def test_cart_update_and_remove(self):
        """Requirement story 3: quantity replacement, totals, and item removal."""
        self.add(2)
        self.add(2, product=self.small)
        self.add(3, override=True)
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.context['cart'].get_total_price(), Decimal('19.00'))
        self.client.post(reverse('cart:cart_remove', args=[self.roll.id]))
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(len(response.context['cart']), 2)
        self.assertEqual(response.context['cart'].get_total_price(), Decimal('5.50'))
        self.assertNotIn(str(self.roll.id), self.client.session[settings.CART_SESSION_ID])

    def test_global_cart_counter(self):
        self.add(3)
        response = self.client.get('/')
        self.assertEqual(len(response.context['cart']), 3)
        self.assertContains(response, '<span class="badge">3</span>', html=True)

    def test_empty_cart(self):
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertContains(response, 'Your cart is empty.')
        self.assertEqual(response.context['cart'].get_total_price(), Decimal('0.00'))

    def test_invalid_quantities_do_not_change_cart(self):
        self.add(2)
        for quantity in [0, -1, 100, 'abc', '1.5', '']:
            with self.subTest(quantity=quantity):
                response = self.add(quantity, override=True)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(self.client.session[settings.CART_SESSION_ID][str(self.roll.id)]['quantity'], 2)

    def test_increment_cannot_exceed_limit(self):
        self.add(99)
        self.add(1)
        self.assertEqual(self.client.session[settings.CART_SESSION_ID][str(self.roll.id)]['quantity'], 99)

    def test_cart_mutations_require_post(self):
        for name in ['cart:cart_add', 'cart:cart_remove']:
            self.assertEqual(self.client.get(reverse(name, args=[self.roll.id])).status_code, 405)

    def test_cart_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.add(client=client).status_code, 403)

    def test_cart_is_isolated_between_sessions(self):
        self.add(2)
        other = Client()
        self.assertEqual(len(other.get(reverse('cart:cart_detail')).context['cart']), 0)

    def test_unavailable_product_cannot_be_added_and_is_removed(self):
        self.add(2)
        self.roll.available = False
        self.roll.save()
        self.assertEqual(self.add().status_code, 404)
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(len(response.context['cart']), 0)

    def test_deleted_product_is_removed_from_session(self):
        self.add()
        self.roll.delete()
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(len(response.context['cart']), 0)

    def test_server_price_is_authoritative(self):
        self.add(2)
        session = self.client.session
        session[settings.CART_SESSION_ID][str(self.roll.id)]['price'] = '0.01'
        session.save()
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.context['cart'].get_total_price(), Decimal('9.00'))

    def test_iteration_keeps_session_json_serializable(self):
        self.add(1)
        self.client.get(reverse('cart:cart_detail'))
        self.add(1)
        self.assertEqual(self.client.session[settings.CART_SESSION_ID][str(self.roll.id)], {'quantity': 2})

    def test_removing_same_item_twice_is_harmless(self):
        self.add(1)
        for _ in range(2):
            self.assertEqual(self.client.post(reverse('cart:cart_remove', args=[self.roll.id])).status_code, 302)
        self.assertEqual(len(self.client.get(reverse('cart:cart_detail')).context['cart']), 0)
