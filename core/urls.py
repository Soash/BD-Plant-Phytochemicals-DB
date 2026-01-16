from django.urls import path
from . import views

urlpatterns = [
    path('bmppd/', views.bmppd, name='bmppd'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('', views.home, name='home'),
]
