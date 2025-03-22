from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import UserGroup, Transaction, Group
from django.contrib.auth.models import User
import requests
import os
from nsetools import Nse
from collections import defaultdict

nse=Nse()

@api_view(['POST'])
def buy_stock(request):
    try:
        user_id = request.data.get("user_id")
        group_id = request.data.get("group_id")
        ticker = request.data.get("ticker")
        quantity = request.data.get("quantity")
        buying_price=request.data.get("buying_price")
        if not user_id or not group_id or not ticker or not quantity:
            return Response({"error": "Missing required parameters"}, status=400)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({"error": "Quantity must be a positive integer"}, status=400)
        except ValueError:
            return Response({"error": "Invalid quantity format"}, status=400)

        user = get_object_or_404(User, id=user_id)
        group = get_object_or_404(Group, id=group_id)
        user_group = get_object_or_404(UserGroup, user=user, group=group)

      

        latest_price=buying_price

        total_price = latest_price * quantity

        if user_group.current_balance < total_price:
            return Response({"error": "Insufficient balance"}, status=400)

        user_group.current_balance -= total_price
        user_group.save()

        Transaction.objects.create(
            user=user, 
            group=group, 
            action="buy", 
            ticker=ticker, 
            quantity=quantity, 
            price=latest_price, 
            total_price=total_price
        )

        return Response({
            "message": "Stock purchased successfully",
            "remaining_balance": str(user_group.current_balance)
        })

    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)

@api_view(['POST'])
def sell_stock(request):
    user_id = request.data.get("user_id")
    group_id = request.data.get("group_id")
    ticker = request.data.get("ticker")
    selling_price=request.data.get("selling_price")
    quantity = int(request.data.get("quantity", 1))

    user = get_object_or_404(User, id=user_id)
    group = get_object_or_404(Group, id=group_id)
    user_group = get_object_or_404(UserGroup, user=user, group=group)


   
    latest_price=selling_price
    
    total_price = latest_price * quantity
    
    # Assume the user has the stocks to sell (You may want to add validation for this)
    user_group.current_balance += total_price
    user_group.save()
    
    Transaction.objects.create(user=user, group=group, action="sell", ticker=ticker, quantity=quantity, price=latest_price, total_price=total_price)
    
    return Response({"message": "Stock sold successfully", "updated_balance": str(user_group.current_balance)})




@api_view(['POST'])
def get_user_stocks(request):
    user_id = request.data.get("user_id")
    group_id = request.data.get("group_id")


   

    user=User.objects.get(id=user_id)
    print(user)

    group=Group.objects.get(id=group_id)
    print(group)
    user_group=UserGroup.objects.get(user=user, group=group)    
    transactions = Transaction.objects.filter(user=user, group=group)
    stock_holdings = defaultdict(lambda: {'ticker': '', 'quantity': 0, 'total_invested': Decimal(0)})
    
    for transaction in transactions:
        ticker = transaction.ticker
        if transaction.action == "buy":
            stock_holdings[ticker]['ticker'] = ticker
            stock_holdings[ticker]['quantity'] += transaction.quantity
            stock_holdings[ticker]['total_invested'] += transaction.total_price
        elif transaction.action == "sell":
            stock_holdings[ticker]['quantity'] -= transaction.quantity
            stock_holdings[ticker]['total_invested'] -= transaction.total_price
            
            if stock_holdings[ticker]['quantity'] <= 0:
                del stock_holdings[ticker]
    return Response(list(stock_holdings.values()))

