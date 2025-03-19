from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('quiz/', views.quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('stats/', views.stats, name='stats'),
    path('custom-admin/', views.custom_admin, name='custom_admin'),  # Interface personnalisée
]