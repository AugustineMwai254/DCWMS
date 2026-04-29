"""Booking Forms"""
from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['cereal_type', 'quantity_bags', 'storage_start_date', 'storage_end_date', 'farmer_notes']
        widgets = {
            'storage_start_date': forms.DateInput(attrs={'type': 'date'}),
            'storage_end_date': forms.DateInput(attrs={'type': 'date'}),
            'farmer_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any special requirements or notes...'}),
        }

    def __init__(self, *args, warehouse=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.warehouse = warehouse
        if warehouse:
            max_bags = warehouse.available_bags
            self.fields['quantity_bags'].widget.attrs['max'] = max_bags
            self.fields['quantity_bags'].help_text = f"Max available: {max_bags} bags (90kg each). Warehouse: {warehouse.available_capacity_mt} MT free."

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('storage_start_date')
        end = cleaned_data.get('storage_end_date')
        bags = cleaned_data.get('quantity_bags')
        
        import datetime
        if start and start < datetime.date.today():
            raise forms.ValidationError("Storage start date cannot be in the past.")
        if start and end and end <= start:
            raise forms.ValidationError("End date must be after start date.")
        
        if bags and self.warehouse:
            quantity_mt = bags * 90 / 1000
            if quantity_mt > float(self.warehouse.available_capacity_mt):
                raise forms.ValidationError(
                    f"Requested quantity ({quantity_mt:.2f} MT) exceeds available capacity ({self.warehouse.available_capacity_mt} MT)."
                )
        return cleaned_data


class BookingApprovalForm(forms.Form):
    action = forms.ChoiceField(choices=[('approve', 'Approve'), ('reject', 'Reject')])
    operator_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
    rejection_reason = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
