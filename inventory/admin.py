from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import StorageSpace, InventoryType, InventoryItem, StockTransaction


@admin.register(StorageSpace)
class StorageSpaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'shelf_label', 'max_capacity', 'get_used_capacity', 'get_available_capacity']
    list_filter = ['room_type']
    search_fields = ['name', 'shelf_label', 'description']

    @admin.display(description='Used Capacity')
    def get_used_capacity(self, obj):
        return obj.used_capacity

    @admin.display(description='Available Capacity')
    def get_available_capacity(self, obj):
        return obj.available_capacity


@admin.register(InventoryType)
class InventoryTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku_prefix', 'unit_of_measure', 'preferred_storage', 'get_sizes']
    list_filter = ['preferred_storage']
    search_fields = ['name', 'sku_prefix', 'description']

    @admin.display(description='Standard Sizes')
    def get_sizes(self, obj):
        if isinstance(obj.standard_sizes, list):
            return ', '.join(str(s) for s in obj.standard_sizes)
        return str(obj.standard_sizes)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = [
        'inventory_type', 'size', 'quantity', 'storage_space',
        'low_stock_threshold', 'get_is_low_stock', 'last_updated',
    ]
    list_filter = ['inventory_type', 'storage_space', 'storage_space__room_type']
    search_fields = ['inventory_type__name', 'size', 'notes', 'storage_space__name']
    readonly_fields = ['last_updated']

    @admin.display(boolean=True, description='Low Stock?')
    def get_is_low_stock(self, obj):
        return obj.is_low_stock


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'item', 'user', 'transaction_type', 'quantity_changed', 'reason']
    list_filter = ['transaction_type', 'user']
    search_fields = ['item__inventory_type__name', 'reason', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    def has_delete_permission(self, request, obj=None):
        return False


class WarehouseUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'groups']
    actions = ['approve_users']

    @admin.action(description='Approve selected users (set active)')
    def approve_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) approved and can now log in.')


admin.site.unregister(User)
admin.site.register(User, WarehouseUserAdmin)
