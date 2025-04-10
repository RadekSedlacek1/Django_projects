from django.shortcuts import render, redirect, get_object_or_404
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
    if request.method == 'POST':                                        # when from template returns POST
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
            ledger_id = request.POST.get('new-payment')                 # take the id form the template
            if ledger_id:                                               # do the rest only if you have id to go to
                return redirect('payment_add',ledger_pk=ledger_id)

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
    if request.method == 'POST':                                            # when from template returns POST
        if 'new-payment' in request.POST:
            ledger_id = request.POST.get('new-payment')                 # take the id form the template
            if ledger_id:                                               # do the rest only if you have id to go to
                return redirect('payment_add',ledger_pk=ledger_id)
    
    ledger = Ledger.objects.get(id=ledger_pk)
    payments = Payment.objects.filter(ledger=ledger)
    balances = PaymentBalance.objects.filter(payment__in=payments).select_related('user')
    user_balances = balances.values('user__username').annotate(total_balance=Sum('balance'))

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
def payment_add(request, ledger_pk):
    ledger = get_object_or_404(Ledger, pk=ledger_pk)

    participants = User.objects.filter(
        Q(payment__ledger=ledger) | Q(paymentbalance__payment__ledger=ledger)
    ).distinct()

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.ledger = ledger
            payment.save()

            payer_id = int(request.POST.get('payer'))
            payer_user = get_object_or_404(User, id=payer_id)

            # 1. Vždy uložit +cost pro plátce
            PaymentBalance.objects.create(
                user=payer_user,
                payment=payment,
                balance=payment.cost
            )

            # 2. Zpracování balances pro zatržené uživatele (včetně plátce jako beneficienta)
            for user in participants:
                include_user = request.POST.get(f'include_{user.id}') == 'on'
                balance_value = request.POST.get(f'balance_{user.id}')
                if include_user and balance_value is not None:
                    try:
                        balance = float(balance_value)
                        PaymentBalance.objects.create(
                            user=user,
                            payment=payment,
                            balance=balance
                        )
                    except ValueError:
                        # špatná hodnota, ignoruj
                        pass

            return redirect('ledger_detail', ledger_pk=ledger_pk)

    all_balances = PaymentBalance.objects.filter(payment__ledger=ledger)
    involved_users_ids = all_balances.values_list('user_id', flat=True).distinct()
    involved_users = User.objects.filter(id__in=involved_users_ids)

    payment_form = PaymentForm()
    balance_forms = []
    for i, user in enumerate(sorted(involved_users, key=lambda u: u != request.user)):  # přihlášený uživatel první
        form = PaymentBalanceForm(prefix=f'balance-{i}', initial={'user': user})
        balance_forms.append((user, form))

    else:
        form = PaymentForm()

    return render(request, 'main/payment_add.html', {
        'payment_form': payment_form,
        'balance_forms': balance_forms,
        'users': involved_users,
        'logged_in_user': request.user,
        'ledger_pk': ledger_pk,
    })

@login_required(login_url='/login')
def payment_edit(request):
    return render(request, 'main/payment_edit.html', {})