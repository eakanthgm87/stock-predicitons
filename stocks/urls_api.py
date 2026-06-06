from django.urls import path
from . import views

urlpatterns = [
    path('ticker/<str:ticker>/', views.ticker_detail),
    path('train/<str:ticker>/', views.api_train),
]
