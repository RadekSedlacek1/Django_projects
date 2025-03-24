from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Payment, Relation

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['name', 'cost', 'desc']
        widgets = {
            'desc': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Description'}),
        }

class RelationForm(forms.ModelForm):
    class Meta:
        model = Relation
        fields = ['user', 'relation']
        widgets = {
            'relation': forms.NumberInput(attrs={'placeholder': 'Relation Value'}),
        }


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'placeholder': 'Username'}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
    )