from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Category,MenuItem ,Cart,Order,OrderItem
from django.contrib.auth.models import User
from django.utils.timezone import now

#Category Serializer
class CategorySerilizer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=['id','slug','title']
        extra_kwargs={
            'slug':{'required':True},
            'title':{'required':True}
        }
# MenuItem Serializer
class MenuItemSerializer(serializers.ModelSerializer):
    category=CategorySerilizer(read_only=True) 
    # Read-Only: Isko request body mein bhejkar change nahi kar sakte—sirf response mein dikhta hai.
    # Fayda: Frontend pe pura category detail dikhane ke liye—user/manager ko clear info milti hai.
    category_id=serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),source='category',write_only=True  
        # Ye response mein nahi dikhta—sirf request mein use hota hai.
    )
    class Meta:
        model=MenuItem
        fields=['id','title','price','featured','category','category_id']
        extra_kwargs={
            'title':{'required':True},
            'price':{'required':True},
            'featured':{'default':False}
        }

#Cart Serializers
class CartSerilizer(serializers.ModelSerializer):
    user=serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    menuitem=MenuItemSerializer(read_only=True)
    menuitem_id=serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(),
        source='menuitem',
        write_only=True
    )
    class Meta:
        model=Cart
        fields = ['id', 'user', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        extra_kwargs = {
            'quantity': {'required': True, 'min_value': 1},
            'unit_price': {'read_only': True},
            'price': {'read_only': True}
        }
        validators=[
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=['user', 'menuitem'],
                message='This menu item is already in the cart.'
            )
        ]
        #User ne sirf menuitem ID aur quantity bhejhai.
        # unit_price aur price ka data user se nahi lena hai, yeh database se auto-set hoga!
    def create(self,validated_data):
        menuitem = validated_data['menuitem'] 
        quantity = validated_data['quantity'] 
        validated_data['unit_price'] = menuitem.price  
        validated_data['price'] = menuitem.price * quantity 
        return Cart.objects.create(**validated_data)
        # 1️⃣ User jo menu item select karega uska data lelo 
        # Ex: Pizza object mila (₹200 price ka)
        # Ex: User ne quantity 2 select ki
        # 2️⃣ Automatically `unit_price` aur `price` set karo
        # Pizza ka price ₹200
        # Total price = 200 * 2 = ₹400
        # 3️⃣ Ab final validated_data se Cart me entry create karo
        # 3️⃣ Ab final validated_data se Cart me entry create karo
        

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(), source='menuitem', write_only=True
    )
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        extra_kwargs = {
            'order': {'read_only': True},
            'quantity': {'required': True, 'min_value': 1},
            'unit_price': {'read_only': True},
            'price': {'read_only': True}
        }
        validators = [
            UniqueTogetherValidator(
                queryset=OrderItem.objects.all(),
                fields=['order', 'menuitem'],
                message='This menu item is already in the order.'
            )
        ]

    def create(self, validated_data):
        # Auto-set unit_price and price from menuitem
        menuitem = validated_data['menuitem']
        quantity = validated_data['quantity']
        validated_data['unit_price'] = menuitem.price
        validated_data['price'] = menuitem.price * quantity
        return OrderItem.objects.create(**validated_data)


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name='Delivery crew'),
        allow_null=True,
        required=False
    )
    order_items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'order_items']
        extra_kwargs = {
            'status': {'required': False, 'default': 0},
            'total': {'read_only': True},
            'date': {'read_only': True, 'default': now}
        }

    def validate_status(self, value):
        if value not in [0, 1]:
            raise serializers.ValidationError("Status must be 0 (out for delivery) or 1 (delivered).")
        return value

    def update(self, instance, validated_data):
        # Ensure only Manager or Delivery crew can update specific fields
        user = self.context['request'].user

        if user.groups.filter(name='Delivery crew').exists():
            if 'delivery_crew' in validated_data or 'user' in validated_data or 'total' in validated_data:
                raise serializers.ValidationError("Delivery crew can only update status.")
        
        # Proceed with the update
        return super().update(instance, validated_data)

      
                    