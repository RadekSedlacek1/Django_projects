from django.contrib import admin
from Bill_2_split.models import Ledger, Payment, Relation

# Registrace modelů
admin.site.register(Ledger)
admin.site.register(Payment)
admin.site.register(Relation)