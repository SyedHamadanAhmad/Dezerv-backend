
from django.urls import path
from .views import buy_stock, sell_stock, get_user_stocks

urlpatterns = [
    path('buy/', buy_stock, name='buy_stock'),
    path('sell/', sell_stock, name='sell_stock'),
    path('portfolio/', get_user_stocks, name='portfolio'),
]



