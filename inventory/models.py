from django.db import models
from django.contrib.auth.models import User


ROOM_TYPE_CHOICES = [
    ('humidity_controlled', 'Humidity Controlled'),
    ('normal', 'Normal'),
]


class StorageSpace(models.Model):
    name = models.CharField(max_length=200)
    room_type = models.CharField(max_length=30, choices=ROOM_TYPE_CHOICES)
    shelf_label = models.CharField(max_length=100)
    max_capacity = models.PositiveIntegerField(help_text='Maximum capacity in units')
    description = models.TextField(blank=True)

    def __str__(self):
        return f'{self.name} — {self.shelf_label}'

    @property
    def used_capacity(self):
        return self.inventoryitem_set.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    @property
    def available_capacity(self):
        return self.max_capacity - self.used_capacity

    class Meta:
        verbose_name = 'Storage Space'
        verbose_name_plural = 'Storage Spaces'
        ordering = ['name']


class InventoryType(models.Model):
    name = models.CharField(max_length=200)
    sku_prefix = models.CharField(max_length=20)
    standard_sizes = models.JSONField(
        default=list,
        help_text='JSON array of standard sizes/units, e.g. ["small", "medium"] or ["100mm", "200mm"]',
    )
    unit_of_measure = models.CharField(max_length=50, help_text='e.g. units, kg, rolls')
    preferred_storage = models.CharField(
        max_length=30,
        choices=ROOM_TYPE_CHOICES,
        blank=True,
        help_text='Preferred room type for storing this item',
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Inventory Type'
        verbose_name_plural = 'Inventory Types'
        ordering = ['name']


class InventoryItem(models.Model):
    inventory_type = models.ForeignKey(InventoryType, on_delete=models.PROTECT)
    size = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    storage_space = models.ForeignKey(StorageSpace, on_delete=models.PROTECT)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.inventory_type.name} — {self.size} @ {self.storage_space.name}'

    @property
    def is_low_stock(self):
        return self.quantity < self.low_stock_threshold

    class Meta:
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
        ordering = ['inventory_type__name', 'size']
        unique_together = [['inventory_type', 'size', 'storage_space']]


TRANSACTION_TYPE_CHOICES = [
    ('add', 'Add Stock'),
    ('use', 'Use Stock'),
    ('adjust', 'Adjust'),
]


class StockTransaction(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity_changed = models.IntegerField(help_text='Positive for additions, negative for usage/reductions')
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, verbose_name='Reason / Notes')

    def __str__(self):
        return f'{self.get_transaction_type_display()} — {self.item} ({self.timestamp:%Y-%m-%d %H:%M})'

    class Meta:
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'
        ordering = ['-timestamp']
