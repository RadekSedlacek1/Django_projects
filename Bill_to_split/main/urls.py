from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path ('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('home/', views.index, name='index'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]