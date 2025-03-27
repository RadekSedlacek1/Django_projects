from django.contrib import admin
from .models import Ledger, Payment, PaymentBalance

# Register your models here.
admin.site.register(Ledger)
admin.site.register(Payment)
admin.site.register(PaymentBalance)