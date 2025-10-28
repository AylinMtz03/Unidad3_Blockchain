from django.urls import path
from . import views

urlpatterns = [
    path('envio/', views.envio, name='envio'),
    path('index/', views.index, name='index'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('get_balance/', views.get_balance, name='get_balance'),
    path("mi_wallet/", views.mi_wallet, name="mi_wallet"),
    path('info/', views.info, name='info'),
    path('contacto/', views.contacto, name='contacto'),
    path('agregar_contacto/', views.agregar_contacto, name='agregar_contacto'),
     path('transacciones/', views.transacciones, name='transacciones'),
     path('registrar_wallet/', views.registrar_wallet, name='registrar_wallet'),
]