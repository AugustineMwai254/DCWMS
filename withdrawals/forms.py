"""Withdrawal Forms"""
from django import forms
from .models import Withdrawal


class WithdrawalForm(forms.ModelForm):
    class Meta:
        model = Withdrawal
        fields = ['bags_to_withdraw', 'scheduled_date', 'farmer_notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'farmer_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, inventory_record=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_record = inventory_record
        if inventory_record:
            self.fields['bags_to_withdraw'].widget.attrs['max'] = inventory_record.remaining_bags
            self.fields['bags_to_withdraw'].help_text = f"Max: {inventory_record.remaining_bags} bags remaining"

    def clean_bags_to_withdraw(self):
        bags = self.cleaned_data.get('bags_to_withdraw')
        if self.inventory_record and bags > self.inventory_record.remaining_bags:
            raise forms.ValidationError(f"Cannot withdraw more than {self.inventory_record.remaining_bags} remaining bags.")
        return bags

    def clean_scheduled_date(self):
        import datetime
        date = self.cleaned_data.get('scheduled_date')
        if date and date < datetime.date.today():
            raise forms.ValidationError("Scheduled date cannot be in the past.")
        return date
