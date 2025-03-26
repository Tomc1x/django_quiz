from django.urls import path
from . import views
from django.contrib.auth import views as auth_views  # Importe les vues d'authentification

urlpatterns = [
    path('', views.login_view, name='login'),
    path('quiz/', views.quiz_list, name='quiz_list'),
    path('stats/', views.stats, name='stats'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('custom-admin/', views.custom_admin,
         name='custom_admin'),  # Interface personnalisée
    path('logout/', views.custom_logout,
         name='logout'),  # Déconnexion personnalisée
    path('custom-admin/quiz/', views.quiz_list, name='admin_quiz_list'),
    path('custom-admin/quiz/<int:quiz_id>/',
         views.admin_quiz_detail,
         name='admin_quiz_detail'),
    path('custom-admin/quiz/<int:quiz_id>/add-question/',
         views.add_question,
         name='add_question'),
    path('custom-admin/question/<int:question_id>/edit/',
         views.edit_question,
         name='edit_question'),
    path('custom-admin/quiz/add/', views.add_quiz, name='add_quiz'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/export/<int:quiz_id>/<str:format_type>/',
         views.QuizExportView.as_view(),
         name='export_quiz'),
    path('quiz/import/', views.QuizImportView.as_view(), name='import_quiz'),
    path('quiz/import-export/', views.import_export_view,
         name='import_export'),  # Nouvelle vue
    path('quiz/export/',
         views.export_quiz_selection,
         name='export_quiz_selection'),
    path('quiz/export/<int:quiz_id>/<str:format_type>/',
         views.QuizExportView.as_view(),
         name='export_quiz'),
    path('quiz/<int:quiz_id>/update-image/',
         views.update_quiz_image,
         name='update_quiz_image'),
]
