from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from .models import Ledger, Payment, PaymentBalance
from .forms import UserRegisterForm, LedgerForm, PaymentForm, PaymentBalanceForm, PaymentBalanceFormSet
from django.forms import inlineformset_factory

def index(request):
    return render(request, 'main/_index.html')

def sign_up(request):
    if request.method =='POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/home')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/sign_up.html', {"form": form})

@login_required(login_url="/login")     # if not login, redirect to: /login
def home(request):
    ledgers = Ledger.objects.all()
    if request.method == "POST":
        ledger_id = request.POST.get("ledger-id")
        if ledger_id:
            ledger = Ledger.objects.filter(id=ledger_id).first()
            if ledger and (ledger.author == request.user):
                ledger.delete()
    return render(request, 'main/home.html', {"ledgers":ledgers})

@login_required(login_url="/login")     # if not login, redirect to: /login
def list_of_ledgers(request):
    ledgers = Ledger.objects.all()
    if request.method == "POST":
        ledger_id = request.POST.get("ledger-id")
        if ledger_id:
            ledger = Ledger.objects.filter(id=ledger_id).first()
            if ledger and (ledger.author == request.user):
                ledger.delete()
    return render(request, 'main/list_of_ledgers.html', {"ledgers":ledgers})

@login_required(login_url="/login")     # if not login, redirect to: /login
def list_of_payments(request):
    ledgers = Ledger.objects.all()
    if request.method == "POST":
        ledger_id = request.POST.get("ledger-id")
        if ledger_id:
            ledger = Ledger.objects.filter(id=ledger_id).first()
            if ledger and (ledger.author == request.user):
                ledger.delete()
    return render(request, 'main/list_of_payments.html', {"ledgers":ledgers})

# From Chat GPT: - redo later
@login_required(login_url="/login")
def create_payment(request):
    PaymentBalanceFormSetFactory = inlineformset_factory(
        Payment, PaymentBalance, form=PaymentBalanceForm, formset=PaymentBalanceFormSet, extra=2  # Výchozí 2 řádky
    )
    if request.method == "POST":
        form = PaymentForm(request.POST)
        formset = PaymentBalanceFormSetFactory(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():  # Zajištění, že se uloží buď vše, nebo nic
                payment = form.save(commit=False)
                payment.user = request.user  # Přiřazení aktuálního uživatele jako vlastníka platby
                payment.save()
                formset.instance = payment
                formset.save()  # Uloží všechny záznamy v PaymentBalance

            return redirect("success_url")  # Přesměrování po uložení
    else:
        form = PaymentForm()
        formset = PaymentBalanceFormSetFactory()
    return render(request, "payment_form.html", {"form": form, "formset": formset})

