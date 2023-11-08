from django.urls import path, include
from . import views

app_name = 'home'  # Specify the namespace for your app's URLs

urlpatterns = [
    path('', views.home, name='home'),  # URL pattern for the 'home' view
    path('product/<str:product_id>/', views.product_detail, name='product_detail'),  # URL pattern for the 'product_detail' view
    path('category/<str:category_name>/', views.category, name='category'),


    # Add more URL patterns as needed for other views
    path('discounts/', views.discounts, name='discounts'),

    path('chart/', views.chart, name='chart'),
    path('charts/', include('charts.urls')),
    path('search_results/', views.search, name='search_results'),
    path('product_detail/<str:product_id>/', views.product_detail, name='product_detail'),
    path('aboutus/', views.about_us, name='about_us'),

    path('contactus/', views.contact_us, name='contact_us'),

    path('toggle-like-dislike/', views.toggle_like_dislike, name='toggle_like_dislike'),

    # Add this URL pattern for adding comments
    path('product/<str:product_id>/add-comment/', views.add_comment, name='add_comment'),
    path('add-to-favorites/<str:product_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('track-click/', views.track_product_click, name='track_click'),


    # ... other URL patterns for the "home" app ...
    path('supermarket/', include('supermarket.urls')),



]


