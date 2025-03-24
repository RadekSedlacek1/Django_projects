
from django.views import generic, View
from Bill_2_split.models import User, Ledger, Payment, Relation
from .functions import calculate_relation_costs
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from datetime import datetime
from .forms import RelationForm
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import UpdateView, DeleteView

class IndexView(generic.TemplateView):
    template_name = 'Bill_2_split/index.html'
    title = 'Welcome page'

class UserView(generic.TemplateView):
    template_name = 'Bill_2_split/user.html'
    title = 'User page'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context

class ListOfLedgersView(generic.TemplateView):
    template_name = 'Bill_2_split/list_of_ledgers.html'
    title = 'List of ledgers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_pk')
        user = User.objects.get(pk=user_id)  # získej uživatele podle pk
        context['user'] = user
        context['ledgers'] = Ledger.objects.filter(payment__relation__user=user).distinct()  # vyfiltruj ledgery pro daného uživatele
        return context

class LedgerAddView(generic.CreateView):
    model = Ledger
    template_name = 'Bill_2_split/ledger_add.html'
    fields = ['name', 'desc']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_pk')  # Získání ID uživatele z URL
        context['user'] = User.objects.get(pk=user_id)  # Přidání uživatele do kontextu
        return context

    def form_valid(self, form):
        # Získej ID uživatele z URL
        user_id = self.kwargs.get('user_pk')
        user = User.objects.get(pk=user_id)

        # Ulož prázdný ledger
        form.instance.user = user
        response = super().form_valid(form)
        ledger = form.instance

        # Zkontroluj, zda již payment neexistuje
        payment, created = Payment.objects.get_or_create(
            ledger=ledger,
            cost=0,
            user=user,
            defaults={
                'name': 'ledger_created',
                'desc': 'dummy_payment',
                'entry_time': datetime.now(),
                'payment_time': datetime.now(),
            }
        )

        # Vytvoř dummy relation pro uživatele
        Relation.objects.get_or_create(
            user=user,
            payment=payment,
            defaults={
                'relation': 1
            }
        )

        return HttpResponseRedirect(reverse('Bill_2_pay:ListOfLedgersView', kwargs={'user_pk': user.pk}))


class LedgerDetailView(generic.DetailView):
    model = Ledger
    template_name = 'Bill_2_split/ledger_detail.html'
    title = 'Ledger detail'

    def get_object(self):
        ledger_pk = self.kwargs.get('ledger_pk')
        return Ledger.objects.get(pk=ledger_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ledger = self.get_object()
        user_id = self.kwargs.get('user_pk')
        user = User.objects.get(pk=user_id)

        # Retrieve payments and relations for the ledger
        payments = Payment.objects.filter(ledger=ledger)
        relations = Relation.objects.filter(payment__in=payments)

        # Get users associated with the ledger through relations
        ledger_users = User.objects.filter(relation__in=relations).distinct()

        # Calculate balance for each user
        user_balances = []
        for user in ledger_users:
            # Get all relations for this user and ledger
            user_relations = relations.filter(user=user)

            # Calculate the total balance for this user
            balance = sum(
                payment.cost * relation.relation
                for payment in payments
                for relation in user_relations
                if relation.payment == payment
            )

            # Format the balance
            balance_str = f"{user.name}: {balance:+.2f}"
            user_balances.append(balance_str)

            # Debug print statement
            print(f'User: {user.name}, Balance: {balance}')

        # Adding context
        context['relations'] = relations
        context['ledger'] = ledger
        context['ledger_users'] = ledger_users
        context['payments'] = payments
        context['user'] = user
        context['user_balances'] = user_balances

        return context




class LedgerEditView(UpdateView):
    model = Ledger
    template_name = 'Bill_2_split/ledger_edit.html'
    fields = ['name', 'desc']
    context_object_name = 'ledger'

    def get_object(self, queryset=None):
        ledger_pk = self.kwargs.get('ledger_pk')
        return get_object_or_404(Ledger, pk=ledger_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_pk')
        context['user'] = get_object_or_404(User, pk=user_id)
        return context

    def form_valid(self, form):
        user_id = self.kwargs.get('user_pk')
        user = get_object_or_404(User, pk=user_id)
        form.instance.user = user
        return super().form_valid(form)

    def get_success_url(self):
        ledger = self.object
        user_id = self.kwargs.get('user_pk')
        return reverse('Bill_2_split:LedgerDetailView', kwargs={'ledger_pk': ledger.pk, 'user_pk': user_id})

class PaymentAddView(generic.CreateView):
    model = Payment
    template_name = 'Bill_2_split/payment_add.html'
    fields = ['name', 'cost', 'desc']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ledger_id = self.kwargs.get('ledger_pk')
        user_id = self.kwargs.get('user_pk')

        ledger = Ledger.objects.get(pk=ledger_id)
        user = User.objects.get(pk=user_id)

        context['ledger'] = ledger
        context['user'] = user
        return context

    def form_valid(self, form):
        ledger_id = self.kwargs.get('ledger_pk')
        user_id = self.kwargs.get('user_pk')
        ledger = Ledger.objects.get(pk=ledger_id)
        user = User.objects.get(pk=user_id)

        form.instance.ledger = ledger
        form.instance.user = user
        relation_value = self.request.POST.get('relation', '0')
        if int(relation_value) != 0:                                # Udělej zápis jen pro relatiok které má smysl - ne všechny uživatele
            Relation.objects.create(user=user, ledger=ledger, relation=int(relation_value))

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('Bill_2_pay:RelationsAddView', kwargs={
            'payment_pk': self.object.pk,
            'ledger_pk': self.object.ledger.pk,
            'user_pk': self.object.user.pk})

class PaymentDetailView(generic.DetailView):
    model = Payment
    template_name = 'Bill_2_split/payment_detail.html'
    title = 'Payment detail'

    def get_object(self):
        payment_pk = self.kwargs.get('payment_pk')
        return Payment.objects.get(pk=payment_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment = self.get_object()

        user_id = self.kwargs.get('user_pk')
        user = User.objects.get(pk=user_id)

        ledger_id = self.kwargs.get('ledger_pk')
        ledger = Ledger.objects.get(pk=ledger_id)

        relations = Relation.objects.filter(payment=payment)

        balance_change = calculate_relation_costs(relations, payment.cost)

        context['ledger'] = ledger
        context['user'] = user
        context['payment'] = payment
        context['relations'] = relations
        context['balance_change'] = balance_change

        return context

class PaymentEditView(UpdateView):
    model = Payment
    template_name = 'Bill_2_split/payment_edit.html'
    fields = ['name', 'cost', 'desc']

    def get_object(self, queryset=None):
        payment_pk = self.kwargs.get('payment_pk')
        return get_object_or_404(Payment, pk=payment_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_pk')
        context['user'] = get_object_or_404(User, pk=user_id)
        context['ledger'] = self.object.ledger
        return context

    def form_valid(self, form):
        user_id = self.kwargs.get('user_pk')
        user = get_object_or_404(User, pk=user_id)
        form.instance.user = user
        return super().form_valid(form)

    def get_success_url(self):
        ledger = self.object.ledger
        user_id = self.kwargs.get('user_pk')
        return reverse('Bill_2_split:RelationsEditView', kwargs={
                           'payment_pk': self.object.pk,
                           'ledger_pk': ledger.pk,
                           'user_pk': user_id
        })

#
class PaymentDeleteView(View):

    def post(self, request, *args, **kwargs):
        payment_pk = self.kwargs.get('payment_pk')
        ledger_pk = self.kwargs.get('ledger_pk')
        user_pk = self.kwargs.get('user_pk')

        payment = get_object_or_404(Payment, pk=payment_pk)
        # Smažte všechny vztahy související s tímto platbou
        Relation.objects.filter(payment=payment).delete()
        # Smažte samotnou platbu
        payment.delete()

        # Přesměrování zpět na detail ledgeru
        return redirect('Bill_2_split:LedgerDetailView', ledger_pk=ledger_pk, user_pk=user_pk)

#

class RelationsAddView(generic.DetailView):
    model = Payment
    template_name = 'Bill_2_split/relation_add.html'
    context_object_name = 'payment'

    def get_object(self):
        payment_id = self.kwargs.get('payment_pk')
        return Payment.objects.get(pk=payment_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ledger_id = self.kwargs.get('ledger_pk')
        user_id = self.kwargs.get('user_pk')
        ledger = Ledger.objects.get(pk=ledger_id)
        user = User.objects.get(pk=user_id)
        users = User.objects.all()      # Přidat filtr jen pro uživatele, kteří sdílejí ledger
        context['relation_forms'] = [RelationForm(prefix=str(u.id), initial={'user': u}) for u in users]
        context['ledger'] = ledger
        context['user'] = user
        return context

    def post(self, request, *args, **kwargs):
        payment = self.get_object()                 # Získání instance Payment na základě payment_pk
        ledger_id = self.kwargs.get('ledger_pk')
        ledger = Ledger.objects.get(pk=ledger_id)
        users = User.objects.all()  # Můžete filtrovat uživatele podle potřeby, např. jen pro uživatele sdílející ledger
        relation_forms = [RelationForm(request.POST, prefix=str(user.id)) for user in users]
        for form in relation_forms:
            if form.is_valid():
                relation = form.save(commit=False)
                relation.payment = payment
                relation.save()
        # Přesměrujte zpět po uložení relací
        return redirect(reverse('Bill_2_pay:PaymentDetailView', kwargs={
            'payment_pk': payment.pk,
            'ledger_pk': payment.ledger.pk,
            'user_pk': self.kwargs.get('user_pk')
        }))

class RelationsEditView(UpdateView):
    model = Payment
    template_name = 'Bill_2_split/relation_edit.html'
    fields = ['name', 'cost', 'desc']

    def get_object(self, queryset=None):
        payment_pk = self.kwargs.get('payment_pk')
        return get_object_or_404(Payment, pk=payment_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_pk')
        context['user'] = get_object_or_404(User, pk=user_id)
        context['ledger'] = self.object.ledger
        relations = Relation.objects.filter(payment=self.object)
        users = User.objects.all()
        relation_forms = [RelationForm(instance=rel, prefix=str(rel.user.id)) for rel in relations]
        context['relation_forms'] = relation_forms
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        relations = Relation.objects.filter(payment__ledger=self.object.ledger)         # Vrať mi formulář pro všechny uživatele ledgeru

        for relation in relations:
            form_prefix = str(relation.user.id)
            relation_form = RelationForm(self.request.POST, prefix=form_prefix, instance=relation)

            if relation_form.is_valid():
                relation_form.save()
                print(f"Relation for user {relation.user.id} was successfully updated.")
            else:
                print(f"Form with prefix {form_prefix} is invalid: {relation_form.errors}")

        return response
    def get_success_url(self):
        ledger = self.object.ledger
        user_id = self.kwargs.get('user_pk')
        return reverse('Bill_2_split:PaymentDetailView', kwargs={
                           'payment_pk': self.object.pk,
                           'ledger_pk': ledger.pk,
                           'user_pk': user_id
        })

