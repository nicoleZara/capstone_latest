from django import forms

class PriceRangeFilterForm(forms.Form):
    min_price = forms.DecimalField(
        label='Minimum Price',
        required=False,
        widget=forms.NumberInput(attrs={'step': 20, 'min': 0})
    )
    max_price = forms.DecimalField(
        label='Maximum Price',
        required=False,
        widget=forms.NumberInput(attrs={'step': 20})
    )


# forms.py
from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
