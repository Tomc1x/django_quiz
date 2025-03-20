from django.urls import path
from . import views
from django.contrib.auth import views as auth_views  # Importe les vues d'authentification


urlpatterns = [
    path('', views.login_view, name='login'),
    path('quiz/', views.quiz_list, name='quiz_list'),
    path('stats/', views.stats, name='stats'),
    path('custom-admin/', views.custom_admin, name='custom_admin'),  # Interface personnalisée
    path('logout/', views.custom_logout, name='logout'),  # Déconnexion personnalisée
    path('custom-admin/quiz/', views.quiz_list, name='quiz_list'),
    path('custom-admin/quiz/<int:quiz_id>/', views.admin_quiz_detail, name='admin_quiz_detail'),
    path('custom-admin/quiz/<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('custom-admin/question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('custom-admin/quiz/add/', views.add_quiz, name='add_quiz'),
]