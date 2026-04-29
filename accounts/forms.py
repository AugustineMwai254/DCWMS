from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import FileExtensionValidator
from django.db import transaction
from .models import User, FarmerProfile, OperatorProfile, COUNTY_CHOICES

# Kenya county choices shared from accounts.models
KENYA_COUNTIES = [('', '-- Select County --')] + COUNTY_CHOICES


class FarmerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    national_id = forms.CharField(max_length=20, required=True)
    county = forms.ChoiceField(
        choices=KENYA_COUNTIES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sub_county = forms.CharField(max_length=100, required=True)
    village = forms.CharField(max_length=100, required=False)
    farm_size_acres = forms.DecimalField(max_digits=8, decimal_places=2, required=False)
    main_crop = forms.CharField(max_length=100, initial='Maize', required=False)
    cooperative_name = forms.CharField(max_length=200, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number',
                  'national_id', 'county', 'sub_county', 'village', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_FARMER
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.national_id = self.cleaned_data['national_id']
        user.county = self.cleaned_data['county']
        user.sub_county = self.cleaned_data['sub_county']
        user.village = self.cleaned_data.get('village', '')
        if commit:
            with transaction.atomic():
                user.save()
                FarmerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'farm_size_acres': self.cleaned_data.get('farm_size_acres'),
                        'main_crop': self.cleaned_data.get('main_crop', 'Maize'),
                        'cooperative_name': self.cleaned_data.get('cooperative_name', ''),
                    }
                )
        return user


class OperatorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    national_id = forms.CharField(max_length=20, required=True)
    county = forms.ChoiceField(
        choices=KENYA_COUNTIES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    company_name = forms.CharField(max_length=200, required=True)
    business_license = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number',
                  'national_id', 'county', 'company_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_OPERATOR
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.national_id = self.cleaned_data['national_id']
        user.county = self.cleaned_data['county']
        if commit:
            user.save()
            OperatorProfile.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                business_license=self.cleaned_data.get('business_license', ''),
            )
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username or Phone'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class UserProfileForm(forms.ModelForm):
    county = forms.ChoiceField(
        choices=KENYA_COUNTIES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    profile_photo = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
        ],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'county', 'sub_county', 'village', 'profile_photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_county': forms.TextInput(attrs={'class': 'form-control'}),
            'village': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo and photo.size > 5 * 1024 * 1024:  # 5MB limit
            raise forms.ValidationError("Image must be smaller than 5MB")
        return photo
