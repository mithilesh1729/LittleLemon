from django.urls import path
from . import views

urlpatterns=[
    path('menu-items/',views.menu_items),
    path('menu-items/<int:menuItem>/',views.single_menu_item),
    path('groups/manager/users/',views.manager_users),
    path('groups/manager/users/<int:userId>/',views.manager_user_remove),
    path('groups/delivery-crew/users/',views.delivery_crew_users),
    path('groups/delivery-crew/users/<int:userId>/',views.delivery_crew_user_remove),
    path('cart/menu-items/',views.cart_items),
    path('orders/',views.orders),
    path('orders/<int:orderId>/',views.single_order),
]