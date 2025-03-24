import os
import django
from datetime import datetime
from decimal import Decimal

# Nastavení Django prostředí
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from Bill_2_split.models import User, Ledger, Payment, Relation

# Vytvoření uživatelů
user1 = User(name="Karel", email="Karel@example.com", password="karel")
user1.save()

user2 = User(name="Martin", email="martin@example.com", password="martin")
user2.save()

user3 = User(name="Marta", email="marta@example.com", password="marta")
user3.save()

user4 = User(name="Honza", email="honza@example.com", password="honza")
user4.save()

user5 = User(name="Jana", email="jana@example.com", password="jana")
user5.save()

# Vytvoření Ledgerů
ledger1 = Ledger(name="Výlet do Paříže", user=user1, desc="Zápis společných nákladů pro cestu do Paříže")
ledger1.save()

ledger2 = Ledger(name="Stanování", user=user5, desc="Zápis společných nákladů během letního stanování 2024")
ledger2.save()


# Vytvoření Paymentů
payment1 = Payment(name="Benzín na cestu", user=user1, ledger=ledger2, cost=Decimal('8499.99'), payment_time=datetime.now())
payment1.save()

payment2 = Payment(name="Malaga - hotel", user=user5, ledger=ledger1, cost=Decimal('12568.85'), payment_time=datetime.now())
payment2.save()

payment3 = Payment(name="Autopůjčovna", user=user2, ledger=ledger2, cost=Decimal('13256.78'), payment_time=datetime.now())
payment3.save()

payment4 = Payment(name="Snídaně", user=user3, ledger=ledger1, cost=Decimal('1625.55'), payment_time=datetime.now())
payment4.save()

payment5 = Payment(name="Nákup", user=user4, ledger=ledger1, cost=Decimal('890.99'), payment_time=datetime.now())
payment5.save()

payment6 = Payment(name="Muzeum vstup", user=user1, ledger=ledger1, cost=Decimal('1396'), payment_time=datetime.now())
payment6.save()

# Vytvoření Relations
relation1 = Relation(user=user1, payment=payment1, relation=Decimal('0.666'))
relation1.save()

relation2 = Relation(user=user2, payment=payment1, relation=Decimal('-0.333'))
relation2.save()

relation3 = Relation(user=user3, payment=payment1, relation=Decimal('-0.333'))
relation3.save()

relation4 = Relation(user=user2, payment=payment3, relation=Decimal('0.666'))
relation4.save()

relation5 = Relation(user=user1, payment=payment3, relation=Decimal('-0.333'))
relation5.save()

relation6 = Relation(user=user3, payment=payment3, relation=Decimal('-0.333'))
relation6.save()

relation7 = Relation(user=user5, payment=payment2, relation=Decimal('0.8'))
relation7.save()

relation8 = Relation(user=user1, payment=payment2, relation=Decimal('-0.2'))
relation8.save()

relation9 = Relation(user=user2, payment=payment2, relation=Decimal('-0.2'))
relation9.save()

relation10 = Relation(user=user3, payment=payment2, relation=Decimal('-0.2'))
relation10.save()

relation11 = Relation(user=user4, payment=payment2, relation=Decimal('-0.2'))
relation11.save()

relation12 = Relation(user=user3, payment=payment4, relation=Decimal('0.4'))
relation12.save()

relation13 = Relation(user=user5, payment=payment4, relation=Decimal('-0.4'))
relation13.save()

relation14 = Relation(user=user4, payment=payment5, relation=Decimal('0.7'))
relation14.save()

relation15 = Relation(user=user1, payment=payment5, relation=Decimal('-0.2'))
relation15.save()

relation16 = Relation(user=user2, payment=payment5, relation=Decimal('-0.5'))
relation16.save()

relation17 = Relation(user=user1, payment=payment6, relation=Decimal('0.75'))
relation17.save()

relation18 = Relation(user=user2, payment=payment6, relation=Decimal('-0.25'))
relation18.save()

relation19 = Relation(user=user4, payment=payment6, relation=Decimal('-0.25'))
relation19.save()

relation20 = Relation(user=user5, payment=payment6, relation=Decimal('-0.25'))
relation20.save()