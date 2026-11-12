"""Create fictional demo catalog data without erasing manager edits."""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Category, Product


class Command(BaseCommand):
    help = 'Create the three Pointo categories and six fictional products. Safe to run again.'

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for name, slug, kind in [
            ('Receipt printers', 'receipt-printers', 'printer'),
            ('Paper rolls', 'paper-rolls', 'paper'),
            ('Tablet stands', 'tablet-stands', 'stand'),
        ]:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'kind': kind})
            categories[kind] = category
        products = [
            ('printer', 'Counter Receipt Printer', 'counter-receipt-printer', '129.00', 'A fictional compact receipt printer for a small-business checkout counter. This demo model prints on 80 mm thermal paper and connects by USB.', {'paper_width_mm': 80, 'connection_type': 'USB'}),
            ('printer', 'Compact Receipt Printer', 'compact-receipt-printer', '89.00', 'A fictional space-saving receipt printer for smaller counters. This demo model uses 58 mm paper and a Bluetooth connection.', {'paper_width_mm': 58, 'connection_type': 'Bluetooth'}),
            ('paper', 'Everyday Paper Roll', 'everyday-paper-roll', '4.50', 'A fictional 80 mm thermal paper roll, 80 metres long. A simple supply for daily receipts. Check printer compatibility before any real purchase.', {'width_mm': 80, 'length_m': 80}),
            ('paper', 'Compact Paper Roll', 'compact-paper-roll', '2.75', 'A fictional 58 mm thermal paper roll, 30 metres long, sized for compact receipt printers. Demo price is per roll.', {'width_mm': 58, 'length_m': 30}),
            ('stand', 'Countertop Tablet Stand', 'countertop-tablet-stand', '39.00', 'A fictional freestanding tablet mount for a tidy checkout station. This demo model fits a 10.2-inch tablet. Tablet not included.', {'tablet_size_inches': Decimal('10.2'), 'mount_type': 'Freestanding'}),
            ('stand', 'Secure Tablet Stand', 'secure-tablet-stand', '59.00', 'A fictional bolt-down tablet stand for a fixed point-of-sale counter. This demo model fits an 11-inch tablet. Tablet not included.', {'tablet_size_inches': Decimal('11.0'), 'mount_type': 'Bolt-down'}),
        ]
        created = 0
        for kind, name, slug, price, description, specs in products:
            if Product.objects.filter(category=categories[kind], slug=slug).exists():
                continue
            product = Product(category=categories[kind], name=name, slug=slug, price=Decimal(price), description=description, **specs)
            product.full_clean()
            product.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} products. Demo catalog has three categories; existing products were not modified.'))
