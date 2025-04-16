import random
from datetime import datetime, timedelta, time
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.models import User
from main.models import Person, Ledger, Payment, PaymentBalance

print("Začínám generovat testovací data...")

# Pomocná funkce pro zaokrouhlení
def round_decimal(value):
    return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

# Pomocná funkce pro náhodný lorem text
def random_lorem(min_len, max_len):
    lorem_words = (
        "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt "
        "ut labore et dolore magna aliqua Ut enim ad minim veniam quis nostrud exercitation ullamco "
        "laboris nisi ut aliquip ex ea commodo consequat Duis aute irure dolor in reprehenderit in "
        "voluptate velit esse cillum dolore eu fugiat nulla pariatur"
    ).split()
    result = ""
    while len(result) < min_len:
        result += " " + random.choice(lorem_words)
    return result.strip()[:random.randint(min_len, max_len)]

# Příkladové osoby
people_names = ["alena", "bara", "cecílie", "dana", "eva", "filip", "hynek", "ivan", "jakub", "karel"]
female = people_names[:5]
male = people_names[5:]

# Vytvoření uživatelů a person
people_map = {}  # name -> Person

for name in people_names:
    user = User.objects.create_user(username=name, password=name)
    person = Person.objects.create(user=user)
    people_map[name] = person

# Ledger přiřazení
ledgers = {
    "Polsko": female,
    "Německo": male,
    "Rakousko": people_names,
    "Slovensko": ["alena", "bara", "filip", "jakub"],
}

# Výlety podle let
start_dates = {
    "Polsko": datetime(2015, 7, 4),
    "Německo": datetime(2016, 7, 2),
    "Rakousko": datetime(2017, 7, 1),
    "Slovensko": datetime(2018, 6, 30),
}

# Kategorie výdajů
expense_categories = [
    "ubytování", "vstupné hrad", "vstupné muzeum", "půjčení auta", "benzín", "večeře", "oběd", "snídaně",
    "lanovka", "parkovné", "lístek na vlak", "pivo", "víno", "suvenýry", "kemp", "lístky na koncert",
    "vstup do aquaparku", "svačina", "vstup na rozhlednu"
]

# Vytvoření ledgerů a plateb
for ledger_name, participant_names in ledgers.items():
    owner_user = people_map[participant_names[0]].user
    ledger = Ledger.objects.create(
        user=owner_user,
        name=ledger_name,
        desc=f"{ledger_name}: {random_lorem(50, 150)}",
    )

    start_date = start_dates[ledger_name]
    num_payments = random.randint(15, 30)

    for _ in range(num_payments):
        payer_name = random.choice(participant_names)
        payer_person = people_map[payer_name]

        num_recipients = random.randint(1, min(4, len(participant_names)))
        recipient_names = random.sample(participant_names, num_recipients)

        if len(recipient_names) == 1 and recipient_names[0] == payer_name:
            continue

        includes_self = payer_name in recipient_names
        description = random.choice(expense_categories)
        cost = round_decimal(random.randint(80, 1200))

        # Náhodné datum a čas
        random_day = timedelta(days=random.randint(0, 8))
        random_time = time(hour=random.randint(7, 22), minute=random.randint(0, 59))
        payment_time = datetime.combine(start_date + random_day, random_time)

        # Vytvoření platby
        payment = Payment.objects.create(
            user=payer_person.user,
            ledger=ledger,
            name=description,
            desc=f"{description}: {random_lorem(20, 30)}",
            cost=cost,
            payment_time=payment_time,
        )

        # Vytvoření balances
        balances = {}
        balances[payer_name] = cost

        share = round_decimal(-cost / len(recipient_names))
        for recipient_name in recipient_names:
            if recipient_name == payer_name:
                continue
            balances[recipient_name] = share

        if includes_self:
            balances[payer_name] += share

        # Korekce zaokrouhlení
        total = round_decimal(sum(balances.values()))
        if abs(total) > 0.01:
            last_key = list(balances.keys())[-1]
            balances[last_key] = round_decimal(balances[last_key] - total)

        # Ulož balances do DB
        for person_name, balance_value in balances.items():
            PaymentBalance.objects.create(
                person=people_map[person_name],
                payment=payment,
                balance=balance_value,
            )

print("✅ Testovací data úspěšně vytvořena.")
