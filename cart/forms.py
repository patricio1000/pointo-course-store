from django import forms


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99, initial=1, widget=forms.NumberInput(attrs={'min': 1, 'max': 99, 'class': 'quantity'}))
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)
