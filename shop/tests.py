from decimal import Decimal
from io import StringIO
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from .models import Category, Product


class ShopTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.printers = Category.objects.create(name='Receipt printers', slug='receipt-printers', kind='printer')
        cls.paper = Category.objects.create(name='Paper rolls', slug='paper-rolls', kind='paper')
        cls.printer = Product.objects.create(category=cls.printers, name='Demo Printer', slug='demo-printer', price=Decimal('129.00'), paper_width_mm=80, connection_type='USB')
        cls.roll = Product.objects.create(category=cls.paper, name='Demo Roll', slug='demo-roll', price=Decimal('4.50'), width_mm=80, length_m=80)
        cls.hidden = Product.objects.create(category=cls.printers, name='Unavailable Printer', slug='unavailable', price=Decimal('80.00'), available=False, paper_width_mm=58, connection_type='USB')

    def test_category_creation(self):
        self.assertEqual(str(self.printers), 'Receipt printers')
        self.assertEqual(self.printers.get_absolute_url(), '/receipt-printers/')

    def test_product_creation(self):
        self.assertEqual(str(self.printer), 'Demo Printer')
        self.assertEqual(self.printer.price, Decimal('129.00'))
        self.assertEqual(self.printer.get_absolute_url(), f'/{self.printer.id}/demo-printer/')
        self.assertIsNotNone(self.printer.created)
        self.assertIsNotNone(self.printer.updated)

    def test_product_list_view(self):
        response = self.client.get(reverse('shop:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/product/list.html')
        self.assertContains(response, 'Demo Printer')
        self.assertContains(response, 'Demo Roll')
        self.assertNotContains(response, 'Unavailable Printer')

    def test_category_filter(self):
        """Requirement story 1: include only available products in this category."""
        response = self.client.get(self.printers.get_absolute_url())
        self.assertEqual(list(response.context['products']), [self.printer])
        self.assertContains(response, 'Demo Printer')
        self.assertNotContains(response, 'Demo Roll')
        self.assertNotContains(response, 'Unavailable Printer')

    def test_product_detail_contains_extra_fields(self):
        response = self.client.get(self.printer.get_absolute_url())
        self.assertTemplateUsed(response, 'shop/product/detail.html')
        self.assertContains(response, '80 mm')
        self.assertContains(response, 'USB')
        self.assertContains(response, '$129.00')
        self.assertContains(response, 'printer.svg')

    def test_paper_detail_contains_specs(self):
        response = self.client.get(self.roll.get_absolute_url())
        self.assertContains(response, '80 m')
        self.assertContains(response, '80 mm')

    def test_unavailable_detail_is_404(self):
        self.assertEqual(self.client.get(self.hidden.get_absolute_url()).status_code, 404)

    def test_wrong_slug_is_404(self):
        self.assertEqual(self.client.get(reverse('shop:product_detail', args=[self.printer.id, 'wrong'])).status_code, 404)

    def test_unknown_category_is_404(self):
        self.assertEqual(self.client.get('/does-not-exist/').status_code, 404)

    def test_empty_catalog_has_clear_message(self):
        Product.objects.all().update(available=False)
        self.assertContains(self.client.get('/'), 'No products available yet.')

    def test_image_field_supports_uploaded_path(self):
        self.printer.image = 'products/demo.png'
        self.printer.save()
        self.assertContains(self.client.get(self.printer.get_absolute_url()), '/media/products/demo.png')

    def test_required_specs_are_validated(self):
        self.printer.connection_type = ''
        with self.assertRaises(ValidationError) as error:
            self.printer.full_clean()
        self.assertIn('connection_type', error.exception.message_dict)

    def test_other_category_specs_are_rejected(self):
        self.printer.width_mm = 80
        with self.assertRaises(ValidationError):
            self.printer.full_clean()

    def test_positive_price_and_dimensions_are_validated(self):
        self.printer.price = Decimal('0')
        self.printer.paper_width_mm = 0
        with self.assertRaises(ValidationError) as error:
            self.printer.full_clean()
        self.assertIn('price', error.exception.message_dict)
        self.assertIn('paper_width_mm', error.exception.message_dict)

    def test_stand_specs(self):
        category = Category.objects.create(name='Tablet stands', slug='tablet-stands', kind='stand')
        product = Product(category=category, name='Demo Stand', slug='stand', price=Decimal('39'), tablet_size_inches=Decimal('10.2'), mount_type='Freestanding')
        product.full_clean()
        product.save()
        response = self.client.get(product.get_absolute_url())
        self.assertContains(response, '10.2 inches')
        self.assertContains(response, 'Freestanding')


class DemoDataTests(TestCase):
    def test_seed_is_repeatable_and_preserves_edits(self):
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Product.objects.count(), 6)
        product = Product.objects.first()
        product.name = 'Manager edited this'
        product.save()
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(Product.objects.count(), 6)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Manager edited this')
        for product in Product.objects.all():
            product.full_clean()


class AdminTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser('testadmin', 'admin@example.test', 'test-only-password')
        self.client.force_login(user)

    def test_admin_catalog_and_orders_registered(self):
        for model in ['shop_category', 'shop_product', 'orders_order']:
            self.assertEqual(self.client.get(reverse(f'admin:{model}_changelist')).status_code, 200)

    def test_manager_can_add_edit_and_delete_product(self):
        category = Category.objects.create(name='Paper rolls', slug='paper-rolls', kind='paper')
        data = {'category': category.id, 'name': 'Admin Roll', 'slug': 'admin-roll', 'price': '3.50', 'available': 'on', 'width_mm': 58, 'length_m': 30}
        self.assertEqual(self.client.post(reverse('admin:shop_product_add'), data).status_code, 302)
        product = Product.objects.get(slug='admin-roll')
        data['price'] = '4.00'
        self.assertEqual(self.client.post(reverse('admin:shop_product_change', args=[product.id]), data).status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.price, Decimal('4.00'))
        self.assertEqual(self.client.post(reverse('admin:shop_product_delete', args=[product.id]), {'post': 'yes'}).status_code, 302)
        self.assertFalse(Product.objects.filter(id=product.id).exists())

    def test_admin_rejects_missing_category_specs(self):
        category = Category.objects.create(name='Paper rolls', slug='paper-rolls', kind='paper')
        response = self.client.post(reverse('admin:shop_product_add'), {'category': category.id, 'name': 'Bad Roll', 'slug': 'bad', 'price': '3.50', 'available': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.exists())
        self.assertContains(response, 'Required for this product category.')
