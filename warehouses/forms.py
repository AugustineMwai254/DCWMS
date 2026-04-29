"""Warehouse Forms"""
from django import forms
from .models import Warehouse, COUNTY_CHOICES, STORAGE_TYPE_CHOICES, CERTIFICATION_CHOICES


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        exclude = ['operator', 'registration_number', 'available_capacity_mt', 'created_at', 'updated_at']
        widgets = {
            'certification_expiry': forms.DateInput(attrs={'type': 'date'}),
            'physical_address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_capacity_mt')
        available = cleaned_data.get('available_capacity_mt')
        if total and available and available > total:
            raise forms.ValidationError("Available capacity cannot exceed total capacity.")
        return cleaned_data


class WarehouseSearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search warehouse name or location...'}))
    county = forms.ChoiceField(
        choices=[('', 'All Counties')] + list(COUNTY_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sort = forms.ChoiceField(
        choices=[('', 'Best Match'), ('nearest', 'Nearest Warehouse')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sub_county = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Sub-county'}))
    min_capacity = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Min. metric tonnes'}))
    storage_type = forms.ChoiceField(choices=[('', 'Any Type')] + list(STORAGE_TYPE_CHOICES), required=False)
    certified_only = forms.BooleanField(required=False, label='Certified Warehouses Only')
