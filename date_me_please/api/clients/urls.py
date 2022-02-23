from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.RegisterView.as_view(), name='api_registration'),
]
