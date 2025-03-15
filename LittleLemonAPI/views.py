# LittleLemonAPI/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer
from django.contrib.auth.models import User, Group

# Category Add (Manager Only)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_category(request):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = CategorySerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Menu Items
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def menu_items(request):
    if request.method == 'GET':
        items = MenuItem.objects.all()
        serializer = MenuItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        serializer = MenuItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def single_menu_item(request, menuItem):
    item = get_object_or_404(MenuItem, id=menuItem)
    if request.method == 'GET':
        serializer = MenuItemSerializer(item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method in ['PUT', 'PATCH']:
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        serializer = MenuItemSerializer(item, data=request.data, partial=(request.method == 'PATCH'), context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        item.delete()
        return Response({'message': 'Deleted'}, status=status.HTTP_200_OK)

# Group Management
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manager_users(request):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'GET':
        managers = User.objects.filter(groups__name='Manager')
        return Response({'managers': [user.username for user in managers]}, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        Group.objects.get(name='Manager').user_set.add(user)
        return Response({'message': f'{username} added to Manager'}, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def manager_user_remove(request, userId):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    user = get_object_or_404(User, id=userId)
    Group.objects.get(name='Manager').user_set.remove(user)
    return Response({'message': f'User {userId} removed'}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def delivery_crew_users(request):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'GET':
        crew = User.objects.filter(groups__name='Delivery crew')
        return Response({'delivery_crew': [user.username for user in crew]}, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        Group.objects.get(name='Delivery crew').user_set.add(user)
        return Response({'message': f'{username} added to Delivery crew'}, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delivery_crew_user_remove(request, userId):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    user = get_object_or_404(User, id=userId)
    Group.objects.get(name='Delivery crew').user_set.remove(user)
    return Response({'message': f'User {userId} removed'}, status=status.HTTP_200_OK)

# Cart
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_items(request):
    if request.method == 'GET':
        cart = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = CartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)  # User auto-set hai serializer mein, context se validation
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        Cart.objects.filter(user=request.user).delete()
        return Response({'message': 'Cart cleared'}, status=status.HTTP_200_OK)

# Orders
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def orders(request):
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists():
            orders = Order.objects.all()
        elif request.user.groups.filter(name='Delivery crew').exists():
            orders = Order.objects.filter(delivery_crew=request.user)
        else:
            orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        if request.user.groups.filter(name='Manager').exists() or request.user.groups.filter(name='Delivery crew').exists():
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        total = sum(item.price for item in cart_items)
        order = Order.objects.create(user=request.user, total=total, status=0)
        for item in cart_items:
            OrderItem.objects.create(
                order=order, menuitem=item.menuitem, quantity=item.quantity,
                unit_price=item.unit_price, price=item.price
            )
        cart_items.delete()
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def single_order(request, orderId):
    order = get_object_or_404(Order, id=orderId)
    if request.method == 'GET':
        if order.user != request.user and not request.user.groups.filter(name='Manager').exists():
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method in ['PUT', 'PATCH']:
        if request.user.groups.filter(name='Manager').exists():
            serializer = OrderSerializer(order, data=request.data, partial=(request.method == 'PATCH'), context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.user.groups.filter(name='Delivery crew').exists() and order.delivery_crew == request.user:
            serializer = OrderSerializer(order, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                status_val = request.data.get('status')
                if status_val not in [0, 1]:
                    return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    elif request.method == 'DELETE':
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        order.delete()
        return Response({'message': 'Order deleted'}, status=status.HTTP_200_OK)