from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import requests

from nsetools import Nse
nse=Nse()

API_KEY = "2NKGY1LYTK34VW95"
BASE_URL = "https://www.alphavantage.co/query"

class Group(models.Model):
    group_name = models.CharField(max_length=100, unique=True)  # Prevent duplicate group names
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.group_name


class UserGroup(models.Model):  # Renamed for better readability
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_users")
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("10000.00"))
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "group")

    def __str__(self):
        return f"{self.user.username} in {self.group.group_name}"


class Transaction(models.Model):
    BUY = "buy"
    SELL = "sell"
    ACTION_CHOICES = [
        (BUY, "Buy"),
        (SELL, "Sell"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="transactions")
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    ticker = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField()  # Ensures only positive values
    price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, editable=False)  # Precomputed for efficiency
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)  # Indexing for optimized queries

    

    def __str__(self):
        return f"{self.user.username} {self.action} {self.quantity} {self.ticker} @ INR {self.price}"










    
