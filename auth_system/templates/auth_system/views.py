from datetime import date
from .models import UserProfile, MongoDBUser
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import ProfilePictureForm
from django.core.files import File 
from pymongo import MongoClient


from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect  
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

from django.conf import settings
import requests
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from collections import defaultdict


client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
product_collection = db['NP_Final_Data']
like_dislike_collection = db['ProductLikesDislikes']
product_collection = db['TryGraph']
favorites_collection = db['Favorites']




# Create your views here.
def HomePage(request):
    return render(request, 'home/index.html', {})

@csrf_protect
def Register(request):
    if request.method == 'POST':
        # account
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        uname = request.POST.get('uname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # personal information
        gender = request.POST.get('gender')
        birthday = request.POST.get('birthday')
        region = request.POST.get('region')
        city = request.POST.get('city')
        purpose = request.POST.get('purpose')

        # Calculate age
        today = date.today()
        birth_date = date.fromisoformat(birthday)
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

         # Check if the username already exists
        if User.objects.filter(username=uname).exists():
            messages.error(request, 'This username is already in use.')
        # Check if the email already exists
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'This email address is already in use.')

        else:

            # separate account info | saving into database
            new_user = User.objects.create_user(uname, email, password)
            new_user.first_name = fname
            new_user.last_name = lname
            new_user.save()

            # Generate a unique verification token
            verification_token = get_random_string(length=32)  # You can adjust the length as needed

            # Create a UserProfile model (assuming you have one) to store additional user information
            # Update the UserProfile model with the token
            user_profile = UserProfile(user=new_user, email_verification_token=verification_token, gender=gender, birthday=birthday, region=region, city=city, age=age, purpose=purpose)

            # Set the default profile picture for the user profile
            # First, you need to open the default profile picture file and assign it to the profile_picture field.
            with open('media/profile_pics/default_profile.png', 'rb') as f:
                default_profile_picture = File(f)
                user_profile.profile_picture.save('default_profile.png', default_profile_picture, save=True)

            user_profile.save()

            # Create a MongoDBUser object and save user details to MongoDB
            mongo_user = MongoDBUser(user_id=new_user.id, username=uname, email=email, password=password, confirm_password=confirm_password, fname=fname, lname=lname,
                                    gender=gender, birthday=birthday, region=region, city=city, age=age, purpose=purpose)
            mongo_user.save()  # Save user details to MongoDB

            # Send a verification email to the user
            send_verification_email(new_user, verification_token)

            return redirect('auth_system:verification-page') # proceed to verification-page when form submitted successfully
    return render(request, 'auth_system/register.html',{}) # return to register page when form submission failed


# Verifies user once link is clicked
def EmailVerification(request, token):
    user_profile = UserProfile.objects.filter(email_verification_token=token).first()
    if user_profile:
        user_profile.email_verified = True
        user_profile.save()
        messages.success(request, 'Email verification successful. You can now log in.')
        return redirect('auth_system:login-page')
        # return render('auth_system:login-page')

    else:
        messages.error(request, 'Invalid verification token.')
        return redirect('auth_system:verification-page')
        # return render('auth_system:verification-page')


# Email containing verification link 
def send_verification_email(user, token):
    subject = 'Email Verification'
    message = f'Please click the following link to verify your email: http://http://127.0.0.1:8000/verification/{token}/'
    # message = f'Please click the following link to verify your email: http://127.0.0.1:8000/verification/{token}/'

    from_email = settings.EMAIL_HOST_USER
    to_email = user.email

    data = {
        'from': from_email,
        'to': to_email,
        'subject': subject,
        'text': message,
    }
    response = requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),
        data=data
    )

    if response.status_code == 200:
        print("Email sent successfully")
    else:
        print("Failed to send email. Status code:", response.status_code)

# def send_verification_email(user, token):
#     subject = 'Email Verification'
#     # message = f'Please click the following link to verify your email: http://127.0.0.1:8000/verification/{token}/'
#     # message = f'Please click the following link to verify your email: http://127.0.0.1:8000/verification/{token}/'

#     from_email = settings.EMAIL_HOST_USER
#     to_email = user.email

#     # Prepare context to render the template
#     context = {
#         'user': user,
#         'token': token,
#     }
#      # Load the email template as a string
#     html_content = render_to_string('auth_system/verify_email.html', context)
#     text_content = strip_tags(html_content)

#     data = {
#         'from': from_email,
#         'to': to_email,
#         'subject': subject,
#         # 'text': message,
#         'text': text_content,
#     }
#     response = requests.post(
#         f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
#         auth=("api", settings.MAILGUN_API_KEY),
#         data=data
#     )

#     if response.status_code == 200:
#         print("Email sent successfully")
#     else:
#         print("Failed to send email. Status code:", response.status_code)



# Pending verification page
def VerificationPage(request):
    return render(request, 'auth_system/verification-page.html', {})



# For real time error message } email and username validation
@csrf_protect
def check_email(request):
    email = request.POST.get('email')
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

csrf_protect
def check_uname(request):
    uname = request.POST.get('uname')
    exists = User.objects.filter(username=uname).exists()
    return JsonResponse({'exists': exists})




@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    form = ProfilePictureForm(instance=user_profile)  # Define the form here

     # Retrieve the user's liked and disliked product IDs from MongoDB
    user_id = request.user.id
    liked_products = like_dislike_collection.distinct('product_id', {'user_id': user_id, 'action': 'like'})
    disliked_products = like_dislike_collection.distinct('product_id', {'user_id': user_id, 'action': 'dislike'})

    print("Liked products:", liked_products)
    print("Disliked products:", disliked_products)

    # Fetch the product details for liked and disliked products from MongoDB
    liked_product_details = list(product_collection.find({'id': {'$in': liked_products}}))
    disliked_product_details = list(product_collection.find({'id': {'$in': disliked_products}}))

    print("Liked product details:", liked_product_details)
    print("Disliked product details:", disliked_product_details)

    context = {
        'user_profile': user_profile,
        'form': form,
        'liked_products': liked_product_details,
        'disliked_products': disliked_product_details,
    }

    return render(request, 'auth_system/profile.html', context)

@login_required
def update_profile_picture(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfilePictureForm(instance=request.user.userprofile)
    
    return render(request, 'auth_system/update_profile_picture.html', {'form': form})


def Login(request):
    if request.method == 'POST':
        # account
        username = request.POST.get('username')
        password = request.POST.get('passwordli')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome Back, {user.first_name} {user.last_name}')
            return redirect('auth_system:auth_home')
        else:
            messages.error(request, 'Error, User does not Exist')

    return render(request, 'auth_system/login.html', {})


@login_required
def display_favorites(request):
    user = request.user
    favorite_products_cursor = favorites_collection.find({'user_id': user.id})
    favorite_products = list(favorite_products_cursor)  # Convert the cursor to a list

    # Group products by batch_identifier and supermarket
    grouped_products = defaultdict(list)
    for product in favorite_products:
        batch_identifier = product['batch_identifier']
        supermarket = product['supermarket']
        grouped_products[(batch_identifier, supermarket)].append(product)

    # Create a new dictionary for displaying prices per batch
    display_data = {}
    for (batch_identifier, supermarket), products in grouped_products.items():
        if batch_identifier not in display_data:
            display_data[batch_identifier] = {
                'image': products[0]['image'],
                'title': products[0]['title'],
                'puregold_price': None,
                'shopmetro_price': None,
                'waltermart_price': None,
                'min_price': float('inf'),  # Initialize min_price as positive infinity
            }
        if supermarket == 'Puregold':
            # Extract and convert the numeric part of the price string
            price_str = products[0]['original_price']
            price = float(price_str.replace('₱', '').replace(',', ''))
            display_data[batch_identifier]['puregold_price'] = price
        elif supermarket == 'ShopMetro':
            price_str = products[0]['original_price']
            price = float(price_str.replace('₱', '').replace(',', ''))
            display_data[batch_identifier]['shopmetro_price'] = price
        elif supermarket == 'WalterMart':
            price_str = products[0]['original_price']
            price = float(price_str.replace('₱', '').replace(',', ''))
            display_data[batch_identifier]['waltermart_price'] = price

        # Update the minimum price if a lower price is found
        if price < display_data[batch_identifier]['min_price']:
            display_data[batch_identifier]['min_price'] = price

    context = {
        'favorite_products': display_data,  # Pass the data for displaying prices to the template
        'batch_identifiers': display_data.keys(),
        'is_empty': len(display_data) == 0,  # Check if favorites are empty
    }

    return render(request, 'auth_system/add_to_list.html', context)

def remove_favorite(request):
    if request.method == "POST":
        batch_identifier = request.POST.get("batch_identifier")
        user = request.user

        try:
            # Use user ID and batch_identifier to remove records from MongoDB favorites collection.
            favorites_collection.delete_many({"user_id": user.id, "batch_identifier": batch_identifier})

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})

def clear_favorites(request):
    if request.method == "POST":
        user = request.user
        try:
            # Use user ID to remove all records associated with the user from the favorites collection
            favorites_collection.delete_many({"user_id": user.id})

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})



def Logout(request):
    logout(request)
    return redirect('auth_system:login-page')



# def request_password_reset(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         # Check if the email exists in your database
#         user = User.objects.filter(email=email).first()
#         if user:
#             # Generate a unique token for this user
#             token = default_token_generator.make_token(user)
#             # Send the password reset email with the token
            
#             send_password_reset_email(user, token)
#             # send_password_reset_email(user)

#             # return render(request, 'password_reset_instructions_sent.html')
#             messages.success(request, 'Instructions has been sent. Please check your email.')

#         else:
#             # Handle cases where the email does not exist
#             messages.error(request, 'Your email is not valid')

#             # return render(request, 'password_reset_error.html')

#     return render(request, 'auth_system/request_password_reset.html')




# def request_password_reset(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         # Check if the email exists in your database
#         user = User.objects.filter(email=email).first()
#         # user_profile = UserProfile.objects.filter(email=email).first()

#         if user:
#             # Generate a unique token for this user
#             token = default_token_generator.make_token(user)

#             # Store the token in the user's UserProfile model
#             user_profile, created = UserProfile.objects.get_or_create(user=user)
#             user_profile.password_reset_token = token
#             user_profile.save()
#             # Store the token in the user model
#             # user = UserProfile(password_reset_token = token)
#             # user.password_reset_token = token
#             # user.save()

#             # Send the password reset email with the token
#             send_password_reset_email(user, token)
#             messages.success(request, 'Instructions have been sent. Please check your email.')
#         else:
#             messages.error(request, 'Your email is not valid')
#     return render(request, 'auth_system/request_password_reset.html')



def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Check if the email exists in your database
        user_profile = User.objects.filter(email=email).first()
        # user_profile = UserProfile.objects.filter(email=email).first()

        if user_profile:
            # Generate a unique token for this user
            token = default_token_generator.make_token(user_profile)
            # Store the token in the user model
            user_profile.password_reset_token = token
            user_profile.save()
            # Send the password reset email with the token
            send_password_reset_email(user_profile, token)
            messages.success(request, 'Instructions have been sent. Please check your email.')
        else:
            messages.error(request, 'Your email is not valid')
    return render(request, 'auth_system/request_password_reset.html')


def send_password_reset_email(user, token):
    subject = 'Password Reset'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]

    # Prepare context to render the template
    context = {
        'user': user,
        'token': token,
    }
     # Load the email template as a string
    html_content = render_to_string('auth_system/password_reset_email.html', context)
    text_content = strip_tags(html_content)

    data = {
        'from': from_email,
        'to': recipient_list,
        'subject': subject,
        'text': text_content,
        'html': html_content,
    }
    response = requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),
        data=data
    )

    if response.status_code == 200:
        print("Email sent successfully")
    else:
        print("Failed to send email. Status code:", response.status_code)



# def send_password_reset_email(user, token):
#     subject = 'Password Reset'
#     from_email = settings.EMAIL_HOST_USER
#     recipient_list = [user.email]
#     message = f'Click the link below: http://127.0.0.1:8000/password-reset/{token}/ '

   
#     data = {
#         'from': from_email,
#         'to': recipient_list,
#         'subject': subject,
#         'text': message,
#     }
#     response = requests.post(
#         f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
#         auth=("api", settings.MAILGUN_API_KEY),
#         data=data
#     )

#     if response.status_code == 200:
#         print("Email sent successfully")
#     else:
#         print("Failed to send email. Status code:", response.status_code)



# def reset_password_form(request, token): 
#     # Verify the token
#     User = get_user_model()
    
#     # Find the user with the associated token
#     user_profile = UserProfile.objects.filter(password_reset_token=token).first()
    
#     if user_profile and default_token_generator.check_token(user_profile, token):
#         if request.method == 'POST':
#             new_password = request.POST.get('new_password')
#             confirm_password = request.POST.get('confirm_password')
#             if new_password == confirm_password:
#                 # Update the user's password in the User model
#                 user = user_profile.user
#                 user.set_password(new_password)
#                 user.save()

#                 # # Update the password in the MongoDBUser model
#                 # mongo_user = MongoDBUser.find_by_username(user.username)
#                 # if mongo_user:
#                 #     mongo_user.password = new_password
#                 #     mongo_user.save()

#                  # Clear the password reset token in the UserProfile model
#                 user_profile.password_reset_token = ""
#                 user_profile.save()

#                 messages.success(request, 'Password reset successful')
#                 return render(request, 'auth_system/login.html')
#             else:
#                 messages.error(request, 'Password reset failed. Please make sure the passwords match.')
#                 return render(request, 'auth_system/reset_password_form.html')
#     else:
#         messages.error(request, 'Invalid or expired password reset token.')
#         return render(request, 'auth_system/reset_password_form.html')


def reset_password_form(request, token): 
    # Verify the token
    User = get_user_model()
    # Find the user with the associated token
    user_profile = UserProfile.objects.filter(password_reset_token=token).first()
    
    if user_profile and default_token_generator.check_token(user_profile, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password == confirm_password:
                # Update the user's password
                user_profile.set_password(new_password)
                user_profile.password_reset_token = ""  # Clear the password reset token
                user_profile.save()
                return render(request, 'auth_system/login.html')
            else:
                return render(request, 'auth_system/reset_password_form.html')
    else:
        return render(request, 'auth_system/reset_password_form.html')