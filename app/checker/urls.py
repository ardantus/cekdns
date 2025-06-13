from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:domain>', views.domain_check, name='domain-check'),
]
