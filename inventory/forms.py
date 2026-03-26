from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import InventoryItem, InventoryType, StorageSpace


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class AddStockForm(forms.Form):
    inventory_type = forms.ModelChoiceField(
        queryset=InventoryType.objects.all(),
        empty_label='— Select item type —',
    )
    size = forms.CharField(
        max_length=100,
        help_text='Must match a standard size for the selected item type.',
    )
    quantity = forms.IntegerField(min_value=1, label='Quantity to Add')
    storage_space = forms.ModelChoiceField(
        queryset=StorageSpace.objects.all(),
        empty_label='— Select storage location —',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Item Notes (optional)',
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Reason / Transaction Notes',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['inventory_type'].widget.attrs['id'] = 'id_inventory_type'
        self.fields['size'].widget.attrs['id'] = 'id_size'
        self.fields['size'].widget.attrs['list'] = 'size-suggestions'


class UseStockForm(forms.Form):
    item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.select_related('inventory_type', 'storage_space').all(),
        empty_label='— Select item —',
        label='Item',
    )
    quantity = forms.IntegerField(min_value=1, label='Quantity Used')
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Reason / Notes',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class CapacityEstimatorForm(forms.Form):
    inventory_type = forms.ModelChoiceField(
        queryset=InventoryType.objects.all(),
        empty_label='— Select item type —',
    )
    size = forms.CharField(
        max_length=100,
        required=False,
        help_text='Optional: filter results by a specific size.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
