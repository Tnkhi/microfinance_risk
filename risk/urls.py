from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/nouveau/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/modifier/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/evaluer/', views.evaluer_client, name='evaluer_client'),
    path('clients/<int:pk>/credit/', views.add_credit, name='add_credit'),
    path('predictions/<int:pk>/', views.resultat_prediction, name='resultat_prediction'),
    path('api/stats/', views.api_stats, name='api_stats'),
]
