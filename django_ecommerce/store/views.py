from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.contrib.auth.forms import UserCreationForm , AuthenticationForm
from django.contrib.auth import login , logout , authenticate 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
import json
import datetime
from django.http import JsonResponse
from .models import Customer, Order, ShippingAddress
from django.conf import settings


def store(request):
    data = cartData(request)
    cartItems = data['cartItems']

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']

    context = {'items': data['items'], 'order': data['order'], 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

def product_list(request):
    products = Product.objects.all()  # Fetch all products
    return render(request, 'store/products.html', {'products': products})




def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            return redirect('dashboard')
    else:
        initial_data = {'username':'', 'password1':'','password2':""}
        form = UserCreationForm(initial=initial_data)
    return render(request, 'store/register.html',{'form':form})



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            return redirect('dashboard')
    else:
        initial_data = {'username':'', 'password':''}
        form = AuthenticationForm(initial=initial_data)
    return render(request, 'store/login.html',{'form':form})


def dashboard_view(request):
    return render(request, 'store/dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('store')



@login_required
def edit_profile(request):
    
    
    
    if request.method == 'POST':
        user = request.user
        name = request.POST['name']
        username = request.POST['username']
        email = request.POST['email']
        
        if User.objects.exclude(pk=user.pk).filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect('edit_profile')

        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect('edit_profile')

        user.first_name = name
        user.username = username
        user.email = email
        user.save()
        
        
        

        # Password change handling
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if current_password and new_password and confirm_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)  # Keep user logged in after password change
                    messages.success(request, "Profile updated successfully!")
                    return redirect('dashboard')
                else:
                    messages.error(request, "New passwords do not match.")
            else:
                messages.error(request, "Incorrect current password.")

        messages.success(request, "Profile updated successfully!")
        return redirect('dashboard')

    return render(request, 'store/edit_profile.html')


def checkout(request):
    data = cartData(request)
    cartItems = data['cartItems']

    context = {'items': data['items'], 'order': data['order'], 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data.get('productId')
    action = data.get('action')

    print(f"Action: {action}, Product: {productId}")

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=401)

    # Ensure the customer exists
    customer, created = Customer.objects.get_or_create(user=request.user, defaults={'name': request.user.username, 'email': request.user.email})
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was updated', safe=False)




def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(
            user=request.user, 
            defaults={'name': request.user.username, 'email': request.user.email}
        )
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    payment_method = data['form'].get('payment_method', 'Online')  # Default to Online if not provided

    order.transaction_id = transaction_id
    order.payment_method = payment_method  # Store COD or Online payment method

    if total == order.get_cart_total:
        order.complete = True  # Mark order as complete for both COD & Online payments
    
    order.save()

    # Handle shipping info if required
    if order.shipping:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping'].get('address', ''),
            city=data['shipping'].get('city', ''),
            state=data['shipping'].get('state', ''),
            zipcode=data['shipping'].get('zipcode', ''),
        )

    return JsonResponse({'message': 'Order processed successfully'}, safe=False)
