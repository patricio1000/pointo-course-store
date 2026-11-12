"""Catalog models from the assignment, extended with Pointo specifications."""
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Category(models.Model):
    class Kind(models.TextChoices):
        PRINTER = 'printer', 'Receipt printers'
        PAPER = 'paper', 'Paper rolls'
        STAND = 'stand', 'Tablet stands'

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    kind = models.CharField(max_length=10, choices=Kind.choices)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Only the two fields belonging to the product's category should be filled in.
    paper_width_mm = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    connection_type = models.CharField(max_length=80, blank=True)
    width_mm = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    length_m = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    tablet_size_inches = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(Decimal('0.1'))])
    mount_type = models.CharField(max_length=80, blank=True)

    SPEC_FIELDS = {
        Category.Kind.PRINTER: ('paper_width_mm', 'connection_type'),
        Category.Kind.PAPER: ('width_mm', 'length_m'),
        Category.Kind.STAND: ('tablet_size_inches', 'mount_type'),
    }

    class Meta:
        ordering = ['name']
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name='product_price_positive')]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])

    def clean(self):
        super().clean()
        if not self.category_id:
            return
        required = self.SPEC_FIELDS.get(self.category.kind, ())
        errors = {}
        for fields in self.SPEC_FIELDS.values():
            for field in fields:
                value = getattr(self, field)
                if field in required and value in (None, ''):
                    errors[field] = 'Required for this product category.'
                elif field not in required and value not in (None, ''):
                    errors[field] = 'Leave this field blank for this product category.'
        if errors:
            raise ValidationError(errors)

    @property
    def specifications(self):
        """Labels and values for the active category, shared by the product template."""
        if self.category.kind == Category.Kind.PRINTER:
            return [('Paper width', f'{self.paper_width_mm} mm'), ('Connection', self.connection_type)]
        if self.category.kind == Category.Kind.PAPER:
            return [('Width', f'{self.width_mm} mm'), ('Length', f'{self.length_m} m')]
        return [('Tablet size', f'{self.tablet_size_inches} inches'), ('Mount', self.mount_type)]
