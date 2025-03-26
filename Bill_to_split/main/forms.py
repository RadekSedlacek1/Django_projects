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
        fields = ["user", "balance"]
        widgets = {
            "balance": forms.NumberInput(attrs={"placeholder": "Balance Value"}),
        }

class PaymentBalanceFormSet(BaseInlineFormSet):
    def clean(self):
        """Validation - sum of balances must be equal to zero."""
        super().clean()

        total_balance = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                total_balance += form.cleaned_data.get("balance", 0)

        if abs(total_balance) > 0.001:  # to cover a rounding error
            raise ValidationError("Sum of balances must be zero! Sum of balalnces is: {:.2f}".format(total_balance))
