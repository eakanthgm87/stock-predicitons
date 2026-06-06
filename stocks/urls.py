from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_ticker/', views.add_ticker, name='add_ticker'),
    path('remove_ticker/<int:pk>/', views.remove_ticker, name='remove_ticker'),
    path('ticker/<str:ticker>/', views.ticker_detail, name='ticker_detail'),
    path('api/train/<str:ticker>/', views.api_train, name='api_train'),
    path('api/import/<str:ticker>/', views.api_import, name='api_import'),
    path('api/predict/<str:ticker>/', views.api_predict, name='api_predict'),
    path("api/quote/<str:ticker>/", views.api_quote, name="api_quote"),
    path("api/live/<str:ticker>/", views.live_price, name="live_price"),
    path("api/price/<str:ticker>/", views.api_price, name="api_price"),
     path("api/td_price/<str:ticker>/", views.td_price, name="td_price"),
    path('trade/<str:ticker>/', views.trade_stock, name='trade_stock'),

    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('history/', views.history_view, name='history'),
]
