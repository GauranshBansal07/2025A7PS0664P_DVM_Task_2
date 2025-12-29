from django import forms
from .models import Station
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

User = get_user_model()

class TicketPurchaseForm(forms.Form):
    source = forms.ModelChoiceField(
        queryset=Station.objects.all().order_by('name'),
        label="From Station",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    destination = forms.ModelChoiceField(
        queryset=Station.objects.all().order_by('name'),
        label="To Station",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class AddFundsForm(forms.Form):
    amount = forms.DecimalField(
        label="Amount to Add ($)", 
        max_digits=6, 
        decimal_places=2,
        min_value=1.00,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 20.00'})
    )

class EditProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}), # Make username read-only
        }