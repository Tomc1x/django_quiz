from django.contrib import admin
from .models import Quiz, Question

# Configuration pour les questions (Question)
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True  # Permet d'éditer la question directement

# Configuration pour les quiz (Quiz)
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')  # Colonnes affichées dans la liste des quiz
    search_fields = ('title',)  # Permet de rechercher par titre
    inlines = [QuestionInline]  # Inclut les questions dans la page du quiz

# Configuration pour les questions (Question)
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz')  # Colonnes affichées dans la liste des questions
    list_filter = ('quiz',)  # Filtre par quiz
    search_fields = ('text',)  # Permet de rechercher par texte de la question
