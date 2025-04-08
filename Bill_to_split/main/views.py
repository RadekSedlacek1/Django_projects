from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from .models import Ledger, Payment, PaymentBalance
from .forms import UserRegisterForm, LedgerForm, PaymentForm, PaymentBalanceForm
from django.forms import inlineformset_factory
from django.db.models import Q, Sum


import pprint # for testing only

##############################        main views        ##############################

def index(request):
    return render(request, 'main/_index.html')

@login_required(login_url='/login')     # if not loged in, redirect to: /login
def home(request):
    ledgers = Ledger.objects.all()
    if request.method == 'POST':
        ledger_id = request.POST.get('ledger-id')
        if ledger_id:
            ledger = Ledger.objects.filter(id=ledger_id).first()
            if ledger and (ledger.author == request.user):
                ledger.delete()
    return render(request, 'main/home.html', {'ledgers':ledgers})

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
    return render(request, 'registration/sign_up.html', {'form': form})

##############################    Ledger related views    
##############################

@login_required(login_url='/login')
def list_of_ledgers(request):
    if request.method == 'POST':                                    # when from template returns POST
        if 'ledger-delete' in request.POST:
            ledger_id = request.POST.get('ledger-delete')               # take the id form the template
            if ledger_id:                                               # do the rest only if you have id to delete
                ledger = Ledger.objects.filter(id=ledger_id).first()    # take this ledger from the db
                print(f"{ledger} deleted")                              # must be before delete, after deletion there is no ID anymore
                ledger.delete()
                
        if 'ledger-detail' in request.POST:
            ledger_id = request.POST.get('ledger-detail')               # take the id form the template
            if ledger_id:                                               # do the rest only if you have id to go to
                return redirect('ledger_detail', ledger_pk=ledger_id)
            
        if 'new-payment' in request.POST:
            ledger_id = request.POST.get('new-payment')               # take the id form the template
            if ledger_id:                                               # do the rest only if you have id to go to
                pass

    user = request.user
    ledgers = Ledger.objects.filter(
        Q(payment__paymentbalance__user=user)
    ).distinct()

    for ledger in ledgers:
        balances = PaymentBalance.objects.filter(
            payment__ledger=ledger                                  # Take all payments and balances
        ).values('user__username').annotate(
            total_balance=Sum('balance')
        )

        ledger.user_balance = 0
        ledger.balances = {}
        # Make sum of all entries for each user
        for b in balances:
            if b['user__username'] == user.username:                
                ledger.user_balance = b['total_balance']
            else:
                ledger.balances[b['user__username']] = b['total_balance']

    return render(request, 'main/list_of_ledgers.html', {'ledgers':ledgers})




@login_required(login_url='/login')
def ledger_add(request):
    if request.method == 'POST':                # if sending filled form
        form = LedgerForm(request.POST)
        if form.is_valid():                     # and if it fits database
            ledger = form.save(commit=False)    # do not send it yet
            ledger.user = request.user          # who saved it is an owner
            ledger.save()                       # now save it
            return redirect ('/list_of_ledgers')
    else:                                       # if not sending form yet
        form = LedgerForm()                     
    return render(request, 'main/ledger_add.html', {'form': form})

@login_required(login_url='/login')
def ledger_detail(request, ledger_pk):
    ledger = Ledger.objects.get(id=ledger_pk)
    payments = Payment.objects.filter(ledger=ledger)
    balances = PaymentBalance.objects.filter(payment__in=payments).select_related('user')
    user_balances = balances.values('user__username').annotate(total_balance=Sum('balance'))
    user = request.user

                
    return render(request, 'main/ledger_detail.html', {
        'ledger': ledger,
        'payments': payments,
        'balances': balances,
        'user_balances': user_balances,
    })

@login_required(login_url='/login')
def ledger_edit(request):
    
    return render(request, 'main/ledger_edit.html', {})

##############################    Payment related views    ##############################

@login_required(login_url='/login')
def list_of_payments(request):
    
    if request.method == 'POST':                                      # when from template returns POST
        payment_id = request.POST.get('payment-delete')               # take the id form the template
        if payment_id:                                                # do the rest only if you have id to delete
            payment = Payment.objects.filter(id=payment_id).first()   # take this ledger from the db
            print(f"{payment} deleted")                               # must be before delete, after deletion there is no ID anymore
            payment.delete()
        
    payments = Payment.objects.all()
    return render(request, 'main/list_of_payments.html', {'payments':payments})


@login_required(login_url='/login')
def payment_add(request):

    pprint.pprint(request.POST)  # Debug
    print("Metoda requestu:", request.method)

    num_participants = 5                            # if 5 users
    referer = request.META.get("HTTP_REFERER", "")  # to check where from the POST method comes
    
    if request.method == 'POST':
        if "payment_add" in referer:                 # only if you see POST from this page

            form = PaymentForm(request.POST)         # if sending filled form
            
            if form.is_valid():                      # and if it fits database
                payment = form.save(commit=False)    # do not send it yet
                payment.user = request.user          # who saved it is an owner
                payment.save()                       # now save it

            for i in range(num_participants):        # for each form
                balance_form = PaymentBalanceForm(request.POST, prefix=f"balance-{i}") # balance forms decomposition
                if balance_form.is_valid() and balance_form.cleaned_data.get('user') and balance_form.cleaned_data.get('balance'):
                    balance = balance_form.save(commit=False)
                    balance.payment = payment
                    balance.save()
            return redirect ('/list_of_payments')


# Pozor, zatím můžou proběhnout prázdné platby, udělá se záznam o platbě, ale nejsou na ni navázané žádné balances



    # if not: rendering a form 
    payment = PaymentForm()
    balances = []
        
    for i in range(num_participants):
        balance = PaymentBalanceForm(prefix=f"balance-{i}")  # return 5 times form of balance
        balances.append(balance)
            
    return render(request, 'main/payment_add.html', {'payment': payment,'balances': balances})

@login_required(login_url='/login')
def payment_detail(request):
    payment = Payment()
    return render(request, 'main/payment_detail.html', {})

@login_required(login_url='/login')
def payment_edit(request):
    return render(request, 'main/payment_edit.html', {})