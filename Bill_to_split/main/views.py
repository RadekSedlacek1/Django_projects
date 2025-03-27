from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from .models import Ledger, Payment, PaymentBalance
from .forms import UserRegisterForm, LedgerForm, PaymentForm, PaymentBalanceForm, PaymentBalanceFormSet
from django.forms import inlineformset_factory

##############################        main views        ##############################

def index(request):
    return render(request, 'main/_index.html')

@login_required(login_url="/login")     # if not loged in, redirect to: /login
def home(request):
    ledgers = Ledger.objects.all()
    if request.method == "POST":
        ledger_id = request.POST.get("ledger-id")
        if ledger_id:
            ledger = Ledger.objects.filter(id=ledger_id).first()
            if ledger and (ledger.author == request.user):
                ledger.delete()
    return render(request, 'main/home.html', {"ledgers":ledgers})

##############################  Account management views  ##############################

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

##############################    Ledger related views    
##############################

@login_required(login_url="/login")
def list_of_ledgers(request):
    
    if request.method == "POST":                                # when from template returns POST
        ledger_id = request.POST.get("ledger-id")               # take the id form the template
        if ledger_id:
            ledger = Ledger.objects.filter(id=ledger_id).first()    # take this ledger from the db
            ledger.delete()
            print(f"{ledger} deleted")
        
    ledgers = Ledger.objects.all()
    return render(request, 'main/list_of_ledgers.html', {"ledgers":ledgers})

@login_required(login_url="/login")
def ledger_add(request):
    if request.method == 'POST':                # if sending filled form
        form = LedgerForm(request.POST)
        if form.is_valid():                     # and if it fits database
            ledger = form.save(commit=False)    # do not send it yet
            ledger.user = request.user          # who saved is is a owner
            ledger.save()                       # now save it
            return redirect ('/list_of_ledgers')
    else:                                       # if not sending form yet
        form = LedgerForm()                     
    return render(request, 'main/ledger_add.html', {"form": form})

@login_required(login_url="/login")
def ledger_detail(request):
    return render(request, 'main/ledger_detail.html', {})

@login_required(login_url="/login")
def ledger_edit(request):
    return render(request, 'main/ledger_edit.html', {})

##############################    Payment related views    ##############################

@login_required(login_url="/login")
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
def payment_add(request):
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
    return render(request, "main/payment_add.html", {"form": form, "formset": formset})

@login_required(login_url="/login")
def payment_detail(request):
    return render(request, 'main/payment_detail.html', {})

@login_required(login_url="/login")
def payment_edit(request):
    return render(request, 'main/payment_edit.html', {})