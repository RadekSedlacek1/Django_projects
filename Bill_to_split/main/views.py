from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from .models import Ledger, Payment, PaymentBalance, Person, UserPlaceholder, ContactConnection, Notification
from .forms import UserRegisterForm, LedgerForm, PaymentForm, PaymentBalanceForm, AddContactForm, NotificationResponse
from django.forms import inlineformset_factory
from django.db.models import Q, Sum
from collections import defaultdict
import pprint

##############################        main views        ##############################

def index(request):
    persons = Person.objects.all().distinct()
    context = {'persons': persons}
    return render(request, 'main/_index.html', context)

@login_required(login_url='/login')
def notifications(request):
    person_self = get_object_or_404(Person, user=request.user)
    notifications_all = Notification.objects.filter(
    Q(recipient=person_self) | Q(sender=person_self)
        ).order_by("-created_at")                       #All notofications with person_self.name in it
    info_pending = notifications_all.filter(recipient=person_self, type="info", status="pending").order_by("-created_at")
    account_connection_pending = notifications_all.filter(recipient=person_self, type="account_connection", status="pending").order_by("-created_at")
    ledger_connection_pending = notifications_all.filter(recipient=person_self, type="ledger_connection", status="pending").order_by("-created_at")
    balance_approve_pending = notifications_all.filter(recipient=person_self, type="balance_approve", status="pending").order_by("-created_at")
    
    if request.method == "POST":
        notification_id = request.POST.get("notification_id")
        action = request.POST.get("action")  # "accept" or "reject"
        response_message = request.POST.get("response_message")
        
        if notification_id:

            notification = get_object_or_404(Notification, id=notification_id, recipient=person_self)

        # ("info", "Info"),
        # ("account_connection", "Account Connection"),
        # ("ledger_connection", "Ledger Connection"),
        # ("balance_approve", "Balance Approve"),

            if notification.type == "info" and notification.status == "pending":
                # only action == "accept": possible
                # Update the notification status
                notification.status = "accepted"
                notification.save()

            if notification.type == "account_connection" and notification.status == "pending":
                sender = notification.sender

                if action == "accept":
                    # Create contact connection
                    ContactConnection.objects.create(
                        person_a=person_self,
                        person_b=sender,
                        explicit=True
                    )
                    # Update the notification status
                    notification.status = "accepted"
                    notification.save()

                    # Create new info notification for the sender
                    Notification.objects.create(
                        sender=person_self,
                        recipient=sender,
                        type="info",
                        status="pending",
                        message=response_message or f"The request for connection has been accepted by {person_self.name}",
                    )
                    messages.success(request, f"The request has been accepted and connection with {sender.name} created")

                elif action == "reject":
                    notification.status = "rejected"
                    notification.save()

                    Notification.objects.create(
                        sender=person_self,
                        recipient=sender,
                        type="info",
                        status="pending",
                        message=response_message or f"The request for connection has been declined by {person_self.name}",
                    )
                    messages.info(request, f"The request from {sender.name} has been declined")

            if notification.type == "ledger_connection" and notification.status == "pending":
                person_self = notification.recipient
                sender = notification.sender
                ledger = notification.ledger

                if action == "accept":
                    # Dummy payment to connect new person to existing ledger
                    with transaction.atomic():
                        dummy_payment = Payment.objects.create(
                            ledger=ledger,
                            name=f"{person_self.name} added to the ledger",
                            desc=f"Dummy payment to connect {person_self.name} with ledger",
                            user=request.user,
                            cost=0,
                        )
                        # Dummy Balance to connect new person to existing ledger
                        PaymentBalance.objects.create(
                            payment=dummy_payment,
                            person=person_self,
                            balance=0
                        )
                        
                        # Change notification status
                        notification.status = "accepted"
                        notification.save()
                        
                        # Send a info notification back to sender
                        Notification.objects.create(
                            sender = person_self,
                            recipient = sender,
                            type = "info",
                            status = "pending",
                            message = response_message or f"{person_self.name} accepted your request to join '{ledger.name}'"
                        )
                        messages.success(request, f"{sender.name} has been added to ledger '{ledger.name}'")
                
                elif action == "reject":
                    # Change notification status
                    notification.status = "rejected"
                    notification.save()
                    
                    Notification.objects.create(
                        sender=person_self,
                        recipient=sender,
                        type="info",
                        status="rejected",
                        message=response_message or f"{person_self.name} declined your request to join '{ledger.name}'"
                    )
                    messages.info(request, f"The request from {sender.name} has been rejected")
                                                
            
            if notification.type == "balance_approve" and notification.status == "pending":
                payment = notification.balance.payment
                person_self = notification.recipient
                sender = notification.sender
                if action == "accept":
                    
                    with transaction.atomic():
                        # Notification status change
                        notification.status = "accepted"
                        notification.save()
                        
                        # Payment status change?
                        non_accepted_notifications = Notification.objects.filter(
                            balance__payment = payment
                            ).exclude(status="accepted")
                        
                        # Info message if payment still pending
                        if non_accepted_notifications.exists():
                            Notification.objects.create(
                                sender = person_self,
                                recipient = sender,
                                type = "info",
                                status = "pending",
                                message = response_message or f"{person_self.name} accepted his/her share in payment {payment.name}"
                            )
                            messages.success(request, f"{sender.name} accepted his/her share in payment {payment.name}")
                            
                        # Info message if all accepted, payment status change
                        else:
                            payment.status = 'accepted'
                            payment.save()
                            
                            Notification.objects.create(
                                sender = person_self,
                                recipient = sender,
                                type = "info",
                                status = "pending",
                                message = response_message or f"The payment {payment.name} has been accepted by all involved users, last accepting is {person_self.name}."
                            )
                            messages.success(request, f"The payment {payment.name} has been accepted by all involved users, last accepting is {person_self.name}.")
                        
                elif action == "reject":
                    with transaction.atomic():
                        # Notification status change
                        notification.status = "rejected"
                        notification.save()

                        Notification.objects.create(
                            sender = person_self,
                            recipient = sender,
                            type = "info",
                            status = "pending",
                            message = response_message or f"{person_self.name} rejected his/her share in payment {payment.name}"
                        )
                        messages.success(request, f"{sender.name} rejected his/her share in payment {payment.name}")

        return redirect("notifications")

    info_with_forms = []
    for notification in info_pending:
        info_with_forms.append((notification,NotificationResponse() ))
    
    account_connection_with_forms = []
    for notification in account_connection_pending:
        account_connection_with_forms.append((notification,NotificationResponse() ))
        
    ledger_connection_with_forms = []
    for notification in ledger_connection_pending:
        ledger_connection_with_forms.append((notification,NotificationResponse() ))
        
    balance_approve_with_forms = []
    for notification in balance_approve_pending:
        balance_approve_with_forms.append((notification,NotificationResponse() ))
    
    context = {
        "notifications_all" : notifications_all,
        "info_with_forms": info_with_forms,
        "account_connection_with_forms": account_connection_with_forms,
        "ledger_connection_with_forms": ledger_connection_with_forms,
        "balance_approve_with_forms": balance_approve_with_forms,
    }

    return render(request, "main/notifications.html", context)

##############################  Account management views  ##############################

def sign_up(request):
    if request.method =='POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)            # Create person entity as well
            Person.objects.create(user=user)
            return redirect('/overview')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/sign_up.html', {'form': form})


@login_required(login_url='/login')         # if not loged in, redirect to: /login
def overview(request):
    person_self = get_object_or_404(Person, user=request.user)
    ledgers = Ledger.objects.filter(
        Q(payment__paymentbalance__person=person_self)
    ).distinct()
    form = AddContactForm()

    if request.method == "POST":
        form = AddContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            message_text = form.cleaned_data['message']
            
            try:
                other_user = User.objects.get(email=email)
                other_person = Person.objects.get(user=other_user)

                # Check if the connection already exists (both ways)
                exists = ContactConnection.objects.filter(
                    person_a=person_self, person_b=other_person
                ).exists() or ContactConnection.objects.filter(
                    person_a=other_person, person_b=person_self
                ).exists()

                # Check if the request already exists
                if not exists:
                    already_sent = Notification.objects.filter(
                        sender = person_self,
                        recipient = other_person,
                        type = "account_connection",
                        status = "pending",
                    ).exists()

                    if not already_sent:
                        Notification.objects.create(
                            sender = person_self,
                            recipient = other_person,
                            type = "account_connection",
                            status = "pending",
                            message=message_text,
                    )

                    messages.success(request, f"Request fo contact with user {email} has been sent.")
                    return redirect('overview')
                else:
                    messages.info(request, "You are already in contact with this user.")
            except User.DoesNotExist:
                messages.error(request, f"User with e-mail: {email} does not exist.")

    connections = ContactConnection.objects.filter(
        Q(person_a=person_self) | Q(person_b=person_self)
    )

    context = {
        'form': form,
        'connections': connections,
        'ledgers':ledgers
    }

    return render(request, 'main/overview.html', context)



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
    ledger = Ledger.objects.get(id=ledger_pk)
    user_person = Person.objects.get(user=request.user)
    
    if request.method == 'POST':                                            # when from template returns POST
        if 'new-payment' in request.POST:
            ledger_id = request.POST.get('new-payment')                     # take the id form the template
            if ledger_id:                                                   # do the rest only if you have id to go to
                return redirect('payment_add', ledger_pk=ledger_id)

        if 'payment-edit' in request.POST:
            payment_id = request.POST.get('payment-edit')
            if payment_id:
                return redirect('payment_edit', payment_pk = payment_id)

        if 'payment-delete' in request.POST:
            payment_id = request.POST.get('payment-delete')                     # take the id form the template
            if payment_id:                                                   # do the rest only if you have id to go to
                        with transaction.atomic():
                            payment = get_object_or_404(Payment, id=payment_id)
                            PaymentBalance.objects.filter(payment=payment).delete()
                            payment.delete()
                            
        if 'request-ledger-connection' in request.POST:
            person_id = request.POST.get('person_to_add')
            person_to_add = get_object_or_404(Person, pk=person_id)

            # Does the same notification already exist?
            existing = Notification.objects.filter(
                sender=user_person,
                recipient=person_to_add,
                type="ledger_connection",
                status="pending",
                ledger=ledger
            ).exists()

            if not existing:
                Notification.objects.create(
                    sender=user_person,
                    recipient=person_to_add,
                    type="ledger_connection",
                    status="pending",
                    message=f"{user_person.name} is asking you to join ledger '{ledger.name}'",
                    ledger=ledger,
                )
                messages.success(request, f"Request to join '{ledger.name}' sent to {person_to_add.name}")
            else:
                messages.info(request, f"A request is already pending for {person_to_add.name}")

    # List of contacts, which are not in the ledger yet - people user can add
    connected_persons = ContactConnection.objects.filter(
        Q(person_a=user_person) | Q(person_b=user_person)
    )
    
    related_people = set()
    for conn in connected_persons:
        other = conn.person_b if conn.person_a == user_person else conn.person_a
        related_people.add(other)

    people_in_ledger = Person.objects.filter(
        paymentbalance__payment__ledger=ledger
    ).distinct()

    people_available_to_add = [p for p in related_people if p not in people_in_ledger]


    payments = Payment.objects.filter(ledger=ledger)
    balances = PaymentBalance.objects.filter(payment__in=payments).select_related('person')

    from collections import defaultdict
    user_balances = defaultdict(lambda: 0)

    for b in balances:
        user_balances[b.person] += b.balance

    # převod do seznamu slovníků pro template
    user_balances_list = [{'person': p, 'name': p.name, 'balance': total} for p, total in user_balances.items()]

    # Balance for each payment of the loged user:
    for payment in payments:
        user_balance = PaymentBalance.objects.filter(payment=payment, person=request.user.person).first()
        if user_balance:
            payment.user_balance = user_balance.balance
        else:
            payment.user_balance = None

    # Status for each balance:
    for balance in balances:
        notification = Notification.objects.filter(balance=balance).first()
        if notification:
            balance.status = notification.status

    return render(request, 'main/ledger_detail.html', {
        'ledger': ledger,
        'payments': payments,
        'balances': balances,
        'user_balances': user_balances_list,  # posíláme připravená data
        'people_available_to_add': people_available_to_add,
    })

@login_required(login_url='/login')
def ledger_edit(request):
    
    return render(request, 'main/ledger_edit.html', {})

##############################    Payment related views    ##############################


@login_required(login_url='/login')
def payment_add(request, ledger_pk):
    ledger = get_object_or_404(Ledger, pk=ledger_pk)

    # Načteme účastníky, aby plátce byl na prvním místě
    participants = list(Person.objects.filter(paymentbalance__payment__ledger=ledger).distinct())
    participants = [request.user.person] + [person for person in participants if person != request.user.person]

    form = PaymentForm(request.POST or None)

    if request.method == 'POST':
        # Debugging: výpis POST dat
        print("POST data:", request.POST)

        # 1. Přečíst hodnoty z POST dat
        participant_values = []
        payer_person = None
        for person in participants:
            balance_raw = request.POST.get(f"balance_{person.id}", "")
            balance = balance_raw.strip() if balance_raw else ""
            # Pokud je balance vyplněná, přidáme do participant_values
            if balance != "":
                participant_values.append({
                    "person": person,
                    "balance": float(balance),  # Převod balance na float
                })

            # Identifikace plátce
            if request.POST.get("payer") == str(person.id):
                payer_person = person

        print("Payer Person:", payer_person)
        print("Participant Values:", participant_values)

        if form.is_valid() and payer_person:
            print("Formulář je validní a plátce je určen.")
            # Získáme celkový náklad platby z formuláře
            cost = round(float(request.POST.get("cost", 0)), 2)
            total_balance = 0

            # 2. Vytvoříme seznam balance pro plátce
            balances_to_create = []
            if payer_person:
                balances_to_create.append((payer_person, cost))  # Kladná balance pro plátce
                total_balance += cost  # Přičteme kladnou balance plátce

            # 3. Vytvoříme záporné balance pro ostatní účastníky
            for item in participant_values:
                person = item["person"]
                balance = item["balance"]
                balances_to_create.append((person, balance))  # Záporná balance pro účastníky
                total_balance += balance  # Přičteme zápornou balance do součtu
            print(balances_to_create)
            
            # 4. Validace součtu balance (cost + balances)
            if round(total_balance, 2) != 0:
                print(f"Chyba v součtu balance: {total_balance}")
                return render(request, 'main/payment_add.html', {
                    'form': form,
                    'ledger': ledger,
                    'participant_values': participant_values,
                    'error': 'Součet balance (platba + dluhy) není nulový.',
                })

            # 5. Uložení balance do databáze v transakci
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.user = request.user
                payment.ledger = ledger
                payment.cost = cost
                payment.save()
                print("Platba uložena do databáze.")

                # 6. Ukládáme jednotlivé balances do databáze
                for person, balance in balances_to_create:
                    if balance != 0:  # Neuložíme balance, která je 0
                        payment_balance = PaymentBalance.objects.create(
                            person=person,
                            payment=payment,
                            balance=balance,
                        )
                        print(f"Balance {balance} uložena pro {person.name}")
                        
                        # 7. Notifikace 
                        status = "pending"
                        sender = payment.user.person
                        recipient = person
                        
                        # Accepted automaticaly the paying part for the payer => only 1 nottification
                        if balance > 0:
                            status = "accepted"
                        
                        # Payment creator accepts the notification
                        if sender is recipient:
                            status = "accepted"

                        Notification.objects.create(
                            type = "balance_approve",
                            sender = sender,
                            recipient = recipient,
                            status = status,
                            message = f"Approve your balance of {payment_balance.balance} for payment {payment.name}",
                            balance = payment_balance,
                        )

        else:
            print("Formulář není validní nebo plátce není určen.")
            return render(request, 'main/payment_add.html', {
                'form': form,
                'ledger': ledger,
                'participant_values': participant_values,
                'error': 'Formulář obsahuje chyby nebo plátce není vybrán.',
            })

        # Po úspěšném uložení přesměrujeme na detail ledgeru
        print("Přesměrování na detail ledgeru.")
        return redirect('ledger_detail', ledger_pk=ledger_pk)

    else:
        # GET - inicializujeme prázdné hodnoty balance
        participant_values = [{"person": person, "balance": ""} for person in participants]

        return render(request, 'main/payment_add.html', {
            'form': form,
            'ledger': ledger,
            'participant_values': participant_values,
        })

@login_required(login_url='/login')
def payment_edit(request, payment_pk):
    payment = get_object_or_404(Payment, pk=payment_pk)
    ledger = payment.ledger

    # Načteme účastníky, aby plátce byl na prvním místě
    balances = PaymentBalance.objects.filter(payment=payment)
    participants = list(Person.objects.filter(paymentbalance__payment__ledger=ledger).distinct())
    participants = [request.user.person] + [p for p in participants if p != request.user.person]

    # Předvyplníme formulář a hodnoty z databáze
    form = PaymentForm(request.POST or None, instance=payment)

    if request.method == 'POST':
        participant_values = []
        payer_person = None

        for person in participants:
            balance_raw = request.POST.get(f"balance_{person.id}", "")
            balance = balance_raw.strip() if balance_raw else ""
            if balance != "":
                participant_values.append({
                    "person": person,
                    "balance": float(balance),
                })

            if request.POST.get("payer") == str(person.id):
                payer_person = person

        if form.is_valid() and payer_person:
            cost = round(float(request.POST.get("cost", 0)), 2)
            total_balance = 0

            balances_to_create = []
            if payer_person:
                balances_to_create.append((payer_person, cost))
                total_balance += cost

            for item in participant_values:
                person = item["person"]
                balance = item["balance"]
                balances_to_create.append((person, balance))
                total_balance += balance

            if round(total_balance, 2) != 0:
                return render(request, 'main/payment_add.html', {
                    'form': form,
                    'ledger': ledger,
                    'participant_values': participant_values,
                    'error': 'Součet balance (platba + dluhy) není nulový.',
                    'edit': True,
                    'payment': payment,
                })

            with transaction.atomic():
                payment = form.save(commit=False)
                payment.user = request.user
                payment.ledger = ledger
                payment.cost = cost
                payment.save()

                # Smažeme původní balances a notifikace
                PaymentBalance.objects.filter(payment=payment).delete()
                Notification.objects.filter(balance__payment=payment).delete()

                for person, balance in balances_to_create:
                    if balance != 0:
                        payment_balance = PaymentBalance.objects.create(
                            person=person,
                            payment=payment,
                            balance=balance,
                        )
                        status = "pending"
                        sender = payment.user.person
                        recipient = person
                        if balance > 0 or sender == recipient:
                            status = "accepted"
                        Notification.objects.create(
                            type="balance_approve",
                            sender=sender,
                            recipient=recipient,
                            status=status,
                            message=f"Approve your balance of {payment_balance.balance} for payment {payment.name}",
                            balance=payment_balance,
                        )

            return redirect('ledger_detail', ledger_pk=ledger.pk)

        else:
            return render(request, 'main/payment_add.html', {
                'form': form,
                'ledger': ledger,
                'participant_values': participant_values,
                'error': 'Formulář obsahuje chyby nebo plátce není vybrán.',
                'edit': True,
                'payment': payment,
            })

    else:
        # Předvyplněné hodnoty pro GET
        participant_values = []
        payer_id = None
        for person in participants:
            balance = balances.filter(person=person).first()
            balance_value = balance.balance if balance else ""
            if balance and balance.balance > 0:
                payer_id = person.id
            participant_values.append({
                "person": person,
                "balance": balance_value,
            })

        return render(request, 'main/payment_add.html', {
            'form': form,
            'ledger': ledger,
            'participant_values': participant_values,
            'payer_id': payer_id,
            'edit': True,
            'payment': payment,
        })