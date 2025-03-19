from django.contrib import admin
from .models import Quiz, Question, Answer

# Configuration pour les réponses (Answer)
class AnswerInline(admin.TabularInline):  # Ou admin.StackedInline pour un affichage différent
    model = Answer
    extra = 1  # Nombre de champs vides affichés pour ajouter des réponses

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
    inlines = [AnswerInline]  # Inclut les réponses dans la page de la question

# Configuration pour les réponses (Answer)
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')  # Colonnes affichées dans la liste des réponses
    list_filter = ('question__quiz', 'is_correct')  # Filtre par quiz et par réponse correcte
    search_fields = ('text',)  # Permet de rechercher par texte de la réponse