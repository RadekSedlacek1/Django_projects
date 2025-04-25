from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Ledger, Payment, PaymentBalance, Notification
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.core.exceptions import ValidationError

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class AddContactForm(forms.Form):
    email = forms.EmailField(label='email')
    message = forms.CharField(
        label = 'message',
        required = False,
        widget = forms.Textarea(attrs={'rows':2, 'placeholder': 'Message for the contact'})
    )

class LedgerForm(forms.ModelForm):
    class Meta:
        model = Ledger
        fields = ['name', 'desc']
        widgets = {
            'desc': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Description'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['name', 'cost', 'desc']
        widgets = {
            'desc': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Description'}),
        }

class PaymentBalanceForm(forms.ModelForm):
    class Meta:
        model = PaymentBalance
        fields = ['person', 'balance']
        widgets = {
            'balance': forms.NumberInput(attrs={'placeholder': 'payment balance'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['person'].required = False
        self.fields['balance'].required = False
        # To allow sending form from template with empty fields, if not all memners of ledger are in the payment

class NotificationMessage(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a message here...'}),
        }

class NotificationResponse(forms.Form):
    response_message = forms.CharField(
        label='response',
        required=False,
        widget= forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a response here...'})
    )