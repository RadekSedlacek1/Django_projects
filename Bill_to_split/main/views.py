from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from .models import Ledger, Payment, PaymentBalance, Person, UserPlaceholder
from .forms import UserRegisterForm, LedgerForm, PaymentForm, PaymentBalanceForm
from django.forms import inlineformset_factory
from django.db.models import Q, Sum
from collections import defaultdict


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
            login(request, user)            # Create person entity as well
            Person.objects.create(user=user)
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

    person_self = Person.objects.get(user=request.user)
    ledgers = Ledger.objects.filter(
        Q(payment__paymentbalance__person=person_self)
    ).distinct()

    for ledger in ledgers:
        balances = PaymentBalance.objects.filter(
            payment__ledger=ledger
        ).select_related('person')

        from collections import defaultdict
        balances_by_person = defaultdict(lambda: 0)
        
        # Need to do it manualy in python, because in database is a field, that is calculated when needed (@property), so not possible to ask the database its value, when it does not exist yet

        for b in balances:
            balances_by_person[b.person] += b.balance

        ledger.user_balance = 0
        ledger.balances = {}
        for person, total in balances_by_person.items():
            ledger.balances[person.name] = total  # ← vždy přidat, i sebe
            if person == person_self:
                ledger.user_balance = total
            else:
                ledger.balances[person.name] = total

    return render(request, 'main/list_of_ledgers.html', {'ledgers':ledgers})

@login_required(login_url='/login')
def ledger_add(request):
    if request.method == 'POST':                # if sending filled form
        form = LedgerForm(request.POST)
        if form.is_valid():                     # and if it fits database
            ledger = form.save(commit=False)    # do not send it yet
            ledger.user = request.user          # who saved it is an owner
            ledger.save()                       # now save it
            
            with transaction.atomic():          # Dummy payment and balance to ledger connection
                person = Person.objects.get(user=request.user)
                payment = Payment.objects.create(
                    name=f"{request.user} added to the ledger",
                    desc=f"Dummy payment to connect {request.user} with ledger",
                    user=request.user,
                    ledger=ledger,
                    cost=0,
                )

                PaymentBalance.objects.create(
                    person=person,
                    payment=payment,
                    balance=0
                )

            return redirect ('/list_of_ledgers')
    else:                                       # if not sending form yet
        form = LedgerForm()                     
    return render(request, 'main/ledger_add.html', {'form': form})

@login_required(login_url='/login')
def ledger_detail(request, ledger_pk):
    if request.method == 'POST':                                            # when from template returns POST
        if 'new-payment' in request.POST:
            ledger_id = request.POST.get('new-payment')                     # take the id form the template
            if ledger_id:                                                   # do the rest only if you have id to go to
                return redirect('payment_add', ledger_pk=ledger_id)

    ledger = Ledger.objects.get(id=ledger_pk)
    payments = Payment.objects.filter(ledger=ledger)
    balances = PaymentBalance.objects.filter(payment__in=payments).select_related('person')

    from collections import defaultdict
    user_balances = defaultdict(lambda: 0)

    for b in balances:
        user_balances[b.person] += b.balance  # `b.person` je instance Person

    # převod do seznamu slovníků pro template
    user_balances_list = [{'person': p, 'name': p.name, 'balance': total} for p, total in user_balances.items()]

    return render(request, 'main/ledger_detail.html', {
        'ledger': ledger,
        'payments': payments,
        'balances': balances,
        'user_balances': user_balances_list,  # posíláme připravená data
    })

@login_required(login_url='/login')
def ledger_edit(request):
    
    return render(request, 'main/ledger_edit.html', {})

##############################    Payment related views    ##############################


@login_required(login_url='/login')
def payment_add(request, ledger_pk):
    ledger = get_object_or_404(Ledger, pk=ledger_pk)

    participants = Person.objects.filter(
        paymentbalance__payment__ledger=ledger
        ).distinct()

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.person = request.user.person
                payment.ledger = ledger
                payment.save()

                payer_id = int(request.POST.get('payer'))
                payer_person = get_object_or_404(Person, id=payer_id)

                # 1. Vždy uložit +cost pro plátce
                PaymentBalance.objects.create(
                    person=payer_person,
                    payment=payment,
                    balance=payment.cost
                )

                # 2. Zpracování balances pro zatržené uživatele (včetně plátce jako beneficienta)
                total_balance = 0
                balances_to_create = []
                
                for person in participants:
                    include_user = request.POST.get(f'include_{person.id}') == 'on'
                    balance_value = request.POST.get(f'balance_{person.id}')
                    if include_user and balance_value is not None:
                        try:
                            balance = float(balance_value)
                            total_balance += balance
                            balances_to_create.append((person, balance))
                        except ValueError:
                            # špatná hodnota, ignoruj
                            pass
                        
                # 3. Validace – součet všech balances musí být opačný k částce
                if round(total_balance + payment.cost, 2) != 0:
                    # neplatný součet, vrať zpět s chybou
                    return render(request, 'main/payment_add.html', {
                        'form': form,
                        'participants': participants,
                        'ledger': ledger,
                        'error': 'Součet balances se nerovná celkové částce platby.',
                    })

                 # 4. Vytvoření balance záznamů pro všechny zahrnuté účastníky
                for person, balance in balances_to_create:
                    PaymentBalance.objects.create(
                        person=person,
                        payment=payment,
                        balance=balance
                    )

                return redirect('ledger_detail', ledger_pk=ledger_pk)

        else:
        # Nevalidní form – padne sem, pokud např. chybí název nebo cost
            return render(request, 'main/payment_add.html', {
                'form': form,
                'participants': participants,
                'ledger': ledger,
                'error': 'Formulář obsahuje chyby.',
            })

    else:
        # GET metoda – zobrazí prázdný formulář
        form = PaymentForm()
        return render(request, 'main/payment_add.html', {
            'form': form,
            'participants': participants,
            'ledger': ledger,
        })

@login_required(login_url='/login')
def payment_edit(request):
    return render(request, 'main/payment_edit.html', {})