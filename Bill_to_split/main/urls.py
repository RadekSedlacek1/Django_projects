from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [

    path('', views.index, name='index'),
# welcome page with app desc and stats

    path('welcome', views.index, name='index'),
# welcome page with app desc and stats

    path('sign-up/', views.sign_up, name='sign_up'),
# account creation

    path('login/', LoginView.as_view(), name='login'),
# user login

    path('logout/', LogoutView.as_view(), name='logout'),
# redirected to login

    path('home/', views.home, name='home'),
# user overview and stats

    path('list_of_ledgers/', views.list_of_ledgers, name='list_of_ledgers'),
# user overview and stats

    path('list_of_payments/', views.list_of_payments, name='list_of_payments'),
# user overview and stats

]

