from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    
##############################        main urls        ##############################
    
    path('', views.index, name='index'),
# welcome page with app desc and stats

    path('welcome/', views.index, name='index'),
# welcome page redirect after login

    path('overview/', views.overview, name='overview'),
# user account overview and stats

##############################  Account management urls  ##############################

    path('sign-up/', views.sign_up, name='sign_up'),
# account creation

    path('login/', LoginView.as_view(), name='login'),
# user login

    path('logout/', LogoutView.as_view(), name='logout'),
# redirected to login in settings.py

    path('notifications/', views.notifications, name='notifications'),
# Go to notifications management

##############################    Ledger related urls    ##############################

    path('list_of_ledgers/', views.list_of_ledgers, name='list_of_ledgers'),
# all ledgers overview and stats

    path('ledger_add/', views.ledger_add, name='ledger_add'),
# create a new empty ledger

    path('ledger_detail/<int:ledger_pk>/', views.ledger_detail, name='ledger_detail'),
# one ledger overview and stats

    path('ledger_edit/<int:ledger_pk>/', views.ledger_edit, name='ledger_edit'),
# edit name, desc. and users in the Ledger

##############################    Payment related urls    ##############################

    path('payment_add/<int:ledger_pk>/', views.payment_add, name='payment_add'),
# create a new payment

    path('payment_edit/<int:payment_pk>/', views.payment_edit, name='payment_edit'),
# edit name and desc of the payment and payment + or - balance increment for users of this payment
]

