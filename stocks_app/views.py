from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import UserGroup, Transaction, Group, StockData, AppUser
from django.contrib.auth.models import User
import requests
import os
from .utils import initialise_db
from collections import defaultdict
from rest_framework import status


@api_view(['POST'])
def buy_stock(request):
    try:
        user_id = request.data.get("user_id")
        group_id = request.data.get("group_id")
        ticker = request.data.get("ticker")
        quantity = request.data.get("quantity")
        timestamp = request.data.get("timestamp")  # Unix timestamp

        if not user_id or not group_id or not ticker or not quantity or not timestamp:
            return Response(
                {"error": "Missing required parameters"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            timestamp = int(timestamp)
            if quantity <= 0:
                return Response(
                    {"error": "Quantity must be a positive integer"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Invalid quantity or timestamp format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(AppUser, id=user_id)
        group = get_object_or_404(Group, id=group_id)
        user_group = get_object_or_404(UserGroup, user=user, group=group)

        # Get the closest stock price for the given timestamp
        stock_entry = (
            StockData.objects.filter(ticker=ticker, datetime__lte=timestamp)
            .order_by("-datetime")
            .first()
        )

        if not stock_entry:
            return Response(
                {"error": "No stock price found for the given timestamp"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        latest_price = Decimal(str(stock_entry.close_price))
        total_price = latest_price * Decimal(quantity)

        if user_group.current_balance < total_price:
            return Response(
                {"error": "Insufficient balance"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user_group.current_balance -= total_price
        user_group.save()

        Transaction.objects.create(
            user=user,
            group=group,
            action="buy",
            ticker=ticker,
            quantity=quantity,
            price=latest_price,
            total_price=total_price,
        )

        return Response({
            "message": "Stock purchased successfully",
            "price_per_stock": str(latest_price),
            "total_price": str(total_price),
            "remaining_balance": str(user_group.current_balance),
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def sell_stock(request):
    try:
        user_id = request.data.get("user_id")
        group_id = request.data.get("group_id")
        ticker = request.data.get("ticker")
        timestamp = request.data.get("timestamp")
        quantity = request.data.get("quantity")

        if not user_id or not group_id or not ticker or not timestamp or not quantity:
            return Response(
                {"error": "Missing required parameters"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            timestamp = int(timestamp)
            if quantity <= 0:
                return Response(
                    {"error": "Quantity must be a positive integer"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Invalid quantity or timestamp format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(AppUser, id=user_id)
        group = get_object_or_404(Group, id=group_id)
        user_group = get_object_or_404(UserGroup, user=user, group=group)

        # Check if user has enough stocks to sell
        transactions = Transaction.objects.filter(user=user, group=group, ticker=ticker)
        current_holdings = 0
        
        for transaction in transactions:
            if transaction.action == "buy":
                current_holdings += transaction.quantity
            elif transaction.action == "sell":
                current_holdings -= transaction.quantity
        
        if current_holdings < quantity:
            return Response(
                {"error": f"Insufficient stocks. You have {current_holdings} stocks of {ticker}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        stock_entry = (
            StockData.objects.filter(ticker=ticker, datetime__lte=timestamp)
            .order_by("-datetime")
            .first()
        )

        if not stock_entry:
            return Response(
                {"error": "No stock price found for the given timestamp"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        latest_price = Decimal(str(stock_entry.close_price))
        total_price = latest_price * Decimal(quantity)

        user_group.current_balance += total_price
        user_group.save()

        Transaction.objects.create(
            user=user,
            group=group,
            action="sell",
            ticker=ticker,
            quantity=quantity,
            price=latest_price,
            total_price=total_price,
        )

        return Response({
            "message": "Stock sold successfully",
            "price_per_stock": str(latest_price),
            "total_price": str(total_price),
            "updated_balance": str(user_group.current_balance),
            "remaining_stocks": current_holdings - quantity
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
def get_user_stocks(request):
    try:
        user_id = request.data.get("user_id")
        group_id = request.data.get("group_id")

        if not user_id or not group_id:
            return Response(
                {"error": "Missing required parameters"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(id=user_id)
        group = Group.objects.get(id=group_id)
        user_group = UserGroup.objects.get(user=user, group=group)    
        
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
        
        return Response(list(stock_holdings.values()), status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Group.DoesNotExist:
        return Response(
            {"error": "Group not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except UserGroup.DoesNotExist:
        return Response(
            {"error": "User is not a member of this group"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_group(request):
    group_name = request.data.get('group_name')
    
    if not group_name:
        return Response(
            {"error": "Group name is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if Group.objects.filter(group_name=group_name).exists():
        return Response(
            {"error": "Group name already exists"}, 
            status=status.HTTP_409_CONFLICT
        )
    
    try:
        group = Group.objects.create(group_name=group_name)
        return Response(
            {
                "message": "Group created successfully",
                "group_id": group.id,
                "group_name": group.group_name
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {"error": "Failed to create group", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def join_group(request):
    user_id = request.data.get('user_id')
    group_id = request.data.get('group_id')
    
    if not user_id or not group_id:
        return Response(
            {"error": "Missing required parameters"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(id=user_id)
        group = Group.objects.get(id=group_id)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Group.DoesNotExist:
        return Response(
            {"error": "Group not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if UserGroup.objects.filter(user=user, group=group).exists():
        return Response(
            {"error": "User already in group"}, 
            status=status.HTTP_409_CONFLICT
        )
    
    UserGroup.objects.create(user=user, group=group)
    return Response(
        {"message": "User joined group successfully"}, 
        status=status.HTTP_201_CREATED
    )

@api_view(['GET'])
def get_grp_leaderboard(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response(
            {"error": "Group not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    leaderboard = UserGroup.objects.filter(group=group).order_by('-current_balance')
    result = [{"user": ug.user.username, "portfolio_value": float(ug.current_balance)} for ug in leaderboard]
    
    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
def init_db(request):
    try:
        bool = initialise_db()
        if bool:
            return Response(
                {"message": "Database initialized successfully"}, 
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Failed to initialize database"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@api_view(['GET'])
def get_last_trade(request, group_id):
    try:
        transactions = Transaction.objects.filter(group_id=group_id).order_by('-timestamp')
        
        if transactions.exists():
            last_trade = transactions.first()
            result = {
                "user": last_trade.user.username,
                "action": last_trade.action,
                "ticker": last_trade.ticker,
                "quantity": last_trade.quantity,
                "price": float(last_trade.price),
                "timestamp": last_trade.timestamp
            }
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "No trades found for this group"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_user_transactions(request, user_id, group_id):
    try:
        transactions = Transaction.objects.filter(user_id=user_id, group_id=group_id).order_by('-timestamp')
        
        if not transactions.exists():
            return Response(
                {"message": "No transactions found for this user in this group"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = [
            {
                "action": txn.action,
                "ticker": txn.ticker,
                "quantity": txn.quantity,
                "price": float(txn.price),
                "total_price": float(txn.total_price),
                "timestamp": txn.timestamp
            }
            for txn in transactions
        ]
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )