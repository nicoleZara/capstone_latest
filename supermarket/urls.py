# in urls.py of 'supermarket' app
from django.urls import path
from . import views

app_name = 'supermarket'  # Make sure the app_name is set

urlpatterns = [
    path('market/<str:supermarket_name>/', views.supermarket_page, name='supermarket_page'),
    path('product/<str:supermarket_name>/<str:category_name>/', views.supermarket_category, name='supermarket_category'),

    # Add more URL patterns as needed
    path('compare/<str:product_id>/', views.compare_modal, name='compare_modal'),
    path('view/<str:product_id>/', views.quickview_modal, name='quickview_modal'),




]
