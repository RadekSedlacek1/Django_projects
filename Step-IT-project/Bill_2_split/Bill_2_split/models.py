from django.db import models
from datetime import datetime
from django.utils.text import slugify
from django.shortcuts import reverse


class AbstractBase(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    desc = models.CharField(max_length=2000, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name + self.pk)
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            # Uložení slug až po vytvoření primárního klíče
            super().save(*args, **kwargs)
            self.slug = slugify(self.name + str(self.pk))
            super().save(update_fields=['slug'])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class User(AbstractBase):
    email = models.CharField(max_length=50, blank=True)
    password = models.CharField(max_length=50, blank=True)
    # If no e-mail and password => user does not have an account yet, but can be established

class Ledger(AbstractBase):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    # meaning of user - is the owner of the Ledger, can edit it
    def get_absolute_url(self):
        return reverse('Bill_2_split:ListOfLedgersView', kwargs={'user_pk': self.user.pk})


class Payment(AbstractBase):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    ledger = models.ForeignKey(Ledger, on_delete=models.PROTECT)
    entry_time = models.DateTimeField(default=datetime.now)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    payment_time = models.DateTimeField(default=datetime.now)
    # meaning of user - is the owner of the entry, can edit it

    def get_absolute_url(self):
        return reverse('Bill_2_split:PaymentDetailView', kwargs={'slug': self.slug})


class Relation(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
    relation = models.DecimalField(max_digits=10, decimal_places=3)