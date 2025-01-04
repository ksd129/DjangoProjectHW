from django.urls import path

from . import views

app_name = 'coin_app'
urlpatterns = [
    path('', views.index, name='index'),
    path('coin/<str:cripto_coin>/', views.single_coin, name='single_coin'),
    path('bases/', views.base_simple, name='base_simple'),
]