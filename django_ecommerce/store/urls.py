from django.urls import path
from . import views

urlpatterns = [
    # Base URLs
    path('', views.store, name="store"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),

    # Authentication URLs
    path("login/", views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),  # Added '/' for consistency

    # Dashboard & Profile URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),

    # Product URLs
    path('products/', views.product_list, name="products"),

    # Order Processing
    path('update_item/', views.updateItem, name="update_item"),
    path('process_order/', views.processOrder, name="process_order"),
]
