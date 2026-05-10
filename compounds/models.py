from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Element(models.Model):
    element_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    atomic_number = models.PositiveIntegerField(unique=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    description = models.TextField(null=True, blank=True)
    symbol = models.CharField(max_length=5, unique=True)

    class Meta:
        db_table = 'element'
        ordering = ['atomic_number']

    def __str__(self):
        return f'{self.name} ({self.symbol})'


class Compound(models.Model):
    class AcidBaseType(models.TextChoices):
        ACID = 'acid', '산성'
        BASE = 'base', '염기성'
        NEUTRAL = 'neutral', '중성'
        AMPHOTERIC = 'amphoteric', '양쪽성'
        UNKNOWN = 'unknown', '미분류'

    compound_id = models.AutoField(primary_key=True)
    formula = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    description = models.TextField(null=True, blank=True)
    acid_base_type = models.CharField(
        max_length=20,
        choices=AcidBaseType.choices,
        default=AcidBaseType.UNKNOWN,
    )
    usage = models.TextField(null=True, blank=True)
    caution = models.TextField(null=True, blank=True)
    risk_level = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    elements = models.ManyToManyField(
        Element,
        through='CompoundElement',
        related_name='compounds',
    )

    class Meta:
        db_table = 'compound'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.formula})'


class CompoundElement(models.Model):
    compound = models.ForeignKey(
        Compound,
        on_delete=models.CASCADE,
        db_column='compound_id',
    )
    element = models.ForeignKey(
        Element,
        on_delete=models.CASCADE,
        db_column='element_id',
    )
    element_count = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'compound_element'
        constraints = [
            models.UniqueConstraint(
                fields=['compound', 'element'],
                name='unique_compound_element',
            ),
        ]

    def __str__(self):
        return f'{self.compound.formula}: {self.element.symbol} x {self.element_count}'
