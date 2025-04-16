from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

# Create your models here.
class AbstractBase(models.Model):
    name = models.CharField(max_length=25)
    slug = models.SlugField(max_length=100, blank=True)
    desc = models.CharField(max_length=2000, blank=True)

# Make no table in db
    class Meta: 
        abstract = True
# Return your name
    def __str__(self):  
        return f"{self.__class__.__name__} {self.name}, ID: {self.pk}"

# When saving create a slug after creating pk
    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name) # ! not unique, IDs in URLs needed! 
        super().save(*args, **kwargs)

# Abstract class, is either django User or my UserPlaceholder until the User is identified
class Person(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="person")
    placeholder = models.OneToOneField("UserPlaceholder", null=True, blank=True, on_delete=models.SET_NULL, related_name="person")
#Take a name from connected model
    @property
    def name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        elif self.placeholder:
            return self.placeholder.name
        return "Unknown user"
    def __str__(self):
         return f"{self.__class__.__name__} {self.name}, ID: {self.pk}"

# Temporary placeholder user to register balances and payments before User account is connected to the Ledger, before is known or before the account exists.
class UserPlaceholder(models.Model):
    name = models.CharField(max_length=25)
    # Creator of this placeholder:
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
         return f"{self.__class__.__name__} {self.name}, ID: {self.pk}"

# Ledger - an accounting book with all payments dedicated to same topic
# meaning of user - is the creator and owner of the Ledger, can edit all entries in the ledger
# Ledger is always created by real loged user, never by UserPlaceholder
class Ledger(AbstractBase):
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name ="Ledger creator and owner")
    creation_time = models.DateTimeField(default=now, verbose_name ="Time of creation of this ledger")
    def get_absolute_url(self):
        return reverse('main:ListOfLedgersView', kwargs={'pk': self.pk, 'slug': self.slug})

# Payment - contains describtion and details about one payment
# meaning of user - is the owner of the entry, can edit it
# Payment is always created by real loged user, never by UserPlaceholder
class Payment(AbstractBase):
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name ="Payment creator")
    ledger = models.ForeignKey(Ledger, on_delete=models.PROTECT)
    entry_time = models.DateTimeField(default=now, verbose_name ="Time of this entry")
    payment_time = models.DateTimeField(default=now, verbose_name ="Time of payment")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name ="Total cost of the payment")
    def get_absolute_url(self):
        return reverse('main:PaymentDetailView', kwargs={'pk': self.pk, 'slug': self.slug})
    
# PaymentBalance - junction table with relation between the user who paid this bill and the user(s) who benefited from the payment
# positive balance: user paid
# negative balance: user has been paid for => a new debt
# Sum of balances for each payment = 0 - Check is done in forms.py
class PaymentBalance(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):  
        return f"Payment balance, ID: {self.pk}, {self.payment.name}, {self.person.name}: {self.balance}"
