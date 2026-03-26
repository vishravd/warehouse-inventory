from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from inventory.models import InventoryItem, InventoryType, StorageSpace, StockTransaction


class Command(BaseCommand):
    help = 'Create the Staff and Admin groups with appropriate permissions.'

    def handle(self, *args, **options):
        # --- Staff group: can view all models and add/change transactions & items ---
        staff_group, staff_created = Group.objects.get_or_create(name='Staff')
        staff_permissions = self._get_permissions([
            (InventoryItem, ['view', 'add', 'change']),
            (InventoryType, ['view']),
            (StorageSpace, ['view']),
            (StockTransaction, ['view', 'add']),
        ])
        staff_group.permissions.set(staff_permissions)
        self.stdout.write(
            self.style.SUCCESS(
                f'{"Created" if staff_created else "Updated"} group: Staff '
                f'({len(staff_permissions)} permissions)'
            )
        )

        # --- Admin group: full control over catalog and spaces ---
        admin_group, admin_created = Group.objects.get_or_create(name='Admin')
        admin_permissions = self._get_permissions([
            (InventoryItem, ['view', 'add', 'change', 'delete']),
            (InventoryType, ['view', 'add', 'change', 'delete']),
            (StorageSpace, ['view', 'add', 'change', 'delete']),
            (StockTransaction, ['view', 'add', 'change', 'delete']),
        ])
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(
            self.style.SUCCESS(
                f'{"Created" if admin_created else "Updated"} group: Admin '
                f'({len(admin_permissions)} permissions)'
            )
        )

    def _get_permissions(self, model_actions):
        permissions = []
        for model, actions in model_actions:
            ct = ContentType.objects.get_for_model(model)
            for action in actions:
                try:
                    perm = Permission.objects.get(content_type=ct, codename=f'{action}_{model._meta.model_name}')
                    permissions.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permission not found: {action}_{model._meta.model_name}')
                    )
        return permissions
