from django.contrib import admin
from .models import Ledger, Payment, PaymentBalance, Person, UserPlaceholder

# Register your models here.
admin.site.register(Ledger)
admin.site.register(Payment)
admin.site.register(PaymentBalance)
admin.site.register(Person)
admin.site.register(UserPlaceholder)
