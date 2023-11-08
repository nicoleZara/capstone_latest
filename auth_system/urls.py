from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import HomePage, Register, Login, Logout, profile, update_profile_picture, display_favorites, remove_favorite, clear_favorites

from . import views
from django.views.generic import TemplateView



app_name = 'auth_system'

urlpatterns = [
    path('', HomePage, name='auth_home'), 
    path('register/', Register, name='register-page'),
    path('login/', Login, name='login-page'),
    path('logout/', Logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('profile/update_picture/', update_profile_picture, name='update-profile-picture'),  # Add this line


    path('edit-profile/', views.edit_profile, name='edit_profile'),


    path('check_email/', views.check_email, name='check_email'),
    path('check_uname/', views.check_uname, name='check_uname'),

    path('verification/<str:token>/', views.EmailVerification, name='email-verification'),
    path('verification/', views.VerificationPage, name='verification-page'),

    path('password-reset/', views.request_password_reset, name='request_password_reset'),
    path('password-reset/<str:token>/', views.reset_password_form, name='reset_password_form'),

    path('added-to-list/', display_favorites, name='display_favorites'),
    path('remove-favorite/', remove_favorite, name='remove-favorite'),
    path('clear-favorites/', clear_favorites, name='clear-favorites'),



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)