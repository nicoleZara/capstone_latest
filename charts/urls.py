from django.urls import path
from . import views
app_name = 'charts' 
 
urlpatterns = [
    path('chart1/', views.chart1, name='chart1'),
]
