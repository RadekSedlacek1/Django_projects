from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Ledger, Payment, PaymentBalance
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.core.exceptions import ValidationError

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class LedgerForm(forms.ModelForm):
    class Meta:
        model = Ledger
        fields = ["name", "desc"]
        widgets = {
            "desc": forms.Textarea(attrs={"rows": 3, "placeholder": "Description"}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["name", "cost", "desc"]
        widgets = {
            "desc": forms.Textarea(attrs={"rows": 3, "placeholder": "Description"}),
        }

class PaymentBalanceForm(forms.ModelForm):
    class Meta:
        model = PaymentBalance
        fields = ["person", "balance"]
        widgets = {
            "balance": forms.NumberInput(attrs={"placeholder": "payment balance"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['person'].required = False
        self.fields['balance'].required = False
        # To allow sending form from template with empty fields