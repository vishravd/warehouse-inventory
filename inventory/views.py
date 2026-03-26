import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddStockForm, CapacityEstimatorForm, RegistrationForm, UseStockForm
from .models import InventoryItem, InventoryType, StorageSpace, StockTransaction


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # requires admin approval before first login
            user.save()
            staff_group, _ = Group.objects.get_or_create(name='Staff')
            user.groups.add(staff_group)
            messages.success(request, 'Registration submitted. An admin will review your account.')
            return redirect('pending_approval')
    else:
        form = RegistrationForm()
    return render(request, 'inventory/register.html', {'form': form})


def pending_approval(request):
    return render(request, 'inventory/pending_approval.html')


@login_required
def dashboard(request):
    items = InventoryItem.objects.select_related('inventory_type', 'storage_space').order_by(
        'inventory_type__name', 'size'
    )
    low_stock_count = sum(1 for item in items if item.is_low_stock)
    return render(request, 'inventory/dashboard.html', {
        'items': items,
        'low_stock_count': low_stock_count,
    })


@login_required
def item_detail(request, pk):
    item = get_object_or_404(
        InventoryItem.objects.select_related('inventory_type', 'storage_space'),
        pk=pk,
    )
    transactions = item.transactions.select_related('user').order_by('-timestamp')
    return render(request, 'inventory/item_detail.html', {
        'item': item,
        'transactions': transactions,
    })


@login_required
def add_stock(request):
    inventory_types = InventoryType.objects.all()
    sizes_data = {str(it.id): it.standard_sizes for it in inventory_types}

    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            inv_type = form.cleaned_data['inventory_type']
            size = form.cleaned_data['size']
            quantity = form.cleaned_data['quantity']
            storage_space = form.cleaned_data['storage_space']
            notes = form.cleaned_data['notes']
            reason = form.cleaned_data['reason']

            if inv_type.standard_sizes and size not in inv_type.standard_sizes:
                form.add_error(
                    'size',
                    f'Invalid size. Choose from: {", ".join(str(s) for s in inv_type.standard_sizes)}',
                )
            else:
                with transaction.atomic():
                    item, created = InventoryItem.objects.get_or_create(
                        inventory_type=inv_type,
                        size=size,
                        storage_space=storage_space,
                        defaults={'notes': notes, 'quantity': 0},
                    )
                    if not created and notes:
                        item.notes = notes
                    item.quantity += quantity
                    item.save()

                    StockTransaction.objects.create(
                        item=item,
                        user=request.user,
                        transaction_type='add',
                        quantity_changed=quantity,
                        reason=reason or f'Stock added by {request.user.username}',
                    )
                messages.success(
                    request,
                    f'Added {quantity} {inv_type.unit_of_measure} of {inv_type.name} ({size}).',
                )
                return redirect('dashboard')
    else:
        form = AddStockForm()

    return render(request, 'inventory/add_stock.html', {
        'form': form,
        'sizes_data': json.dumps(sizes_data),
    })


@login_required
def use_stock(request, pk=None):
    initial = {}
    if pk:
        item = get_object_or_404(InventoryItem, pk=pk)
        initial['item'] = item

    if request.method == 'POST':
        form = UseStockForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['item']
            quantity = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']

            if quantity > item.quantity:
                form.add_error(
                    'quantity',
                    f'Only {item.quantity} {item.inventory_type.unit_of_measure} in stock.',
                )
            else:
                with transaction.atomic():
                    item.quantity -= quantity
                    item.save()
                    StockTransaction.objects.create(
                        item=item,
                        user=request.user,
                        transaction_type='use',
                        quantity_changed=-quantity,
                        reason=reason,
                    )
                messages.success(
                    request,
                    f'Logged use of {quantity} {item.inventory_type.unit_of_measure} of {item.inventory_type.name}.',
                )
                return redirect('item_detail', pk=item.pk)
    else:
        form = UseStockForm(initial=initial)

    items_qs = InventoryItem.objects.select_related('inventory_type').all()
    item_stock_json = json.dumps({
        str(i.pk): {'qty': i.quantity, 'unit': i.inventory_type.unit_of_measure}
        for i in items_qs
    })
    return render(request, 'inventory/use_stock.html', {
        'form': form,
        'item_stock_json': item_stock_json,
    })


@login_required
def capacity_estimator(request):
    results = None
    form = CapacityEstimatorForm(request.GET or None)

    if form.is_valid():
        inv_type = form.cleaned_data['inventory_type']
        size_filter = form.cleaned_data.get('size', '').strip()

        results = []
        for space in StorageSpace.objects.all():
            used = space.inventoryitem_set.aggregate(total=Sum('quantity'))['total'] or 0
            available = space.max_capacity - used

            items_qs = space.inventoryitem_set.filter(inventory_type=inv_type)
            if size_filter:
                items_qs = items_qs.filter(size=size_filter)
            items_of_type = sum(i.quantity for i in items_qs)

            results.append({
                'space': space,
                'used_capacity': used,
                'available_capacity': available,
                'is_preferred': bool(inv_type.preferred_storage and space.room_type == inv_type.preferred_storage),
                'items_of_type_here': items_of_type,
            })

        # Preferred spaces first, then by available capacity descending
        results.sort(key=lambda x: (not x['is_preferred'], -x['available_capacity']))

    return render(request, 'inventory/capacity_estimator.html', {
        'form': form,
        'results': results,
    })
