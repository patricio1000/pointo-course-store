from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    checkout_token = forms.UUIDField(widget=forms.HiddenInput)

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']
        widgets = {'email': forms.EmailInput(attrs={'autocomplete': 'email'})}
