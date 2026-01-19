from django.urls import path
from . import views

urlpatterns = [
    path('', views.bmppd, name='bmppd'),
    path('bmppd_result/', views.bmppd_result, name='bmppd_result'),
    path('about/', views.about, name='about'),
    path('acknowledgement/', views.acknowledgement, name='acknowledgement'),
    path("reference/", views.reference, name="reference"),
]
