from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):
    """Form for creating payments."""

    class Meta:
        model = Payment
        fields = ['booking', 'farmer', 'amount_kes', 'payment_method']
        widgets = {
            'booking': forms.Select(attrs={'class': 'form-control'}),
            'farmer': forms.Select(attrs={'class': 'form-control'}),
            'amount_kes': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter bookings that are pending payment
        self.fields['booking'].queryset = self.fields['booking'].queryset.filter(status='pending_payment')
        # Make farmer read-only if booking is selected
        if self.instance and self.instance.booking:
            self.fields['farmer'].initial = self.instance.booking.farmer
            self.fields['farmer'].widget.attrs['readonly'] = True


class MPesaPaymentForm(forms.Form):
    """Form for initiating MPesa payment."""

    phone_number = forms.CharField(
        max_length=15,
        label="MPesa Phone Number",
        help_text="Enter your MPesa registered phone number (e.g., 254712345678)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254712345678'
        })
    )

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        # Basic validation for Kenyan phone numbers
        if not phone.startswith('254') or len(phone) != 12:
            raise forms.ValidationError("Please enter a valid Kenyan phone number starting with 254")
        return phone