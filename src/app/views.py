import csv
import json
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.db.models import Avg, Count, Max, Min, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .forms import LoginForm, QuestionForm, QuizForm, RegisterForm
from .imgur_uploader import ImgurUploader
from .models import Question, Quiz, UserQuizResult
from django.contrib.auth import update_session_auth_hash


def login_view(request):
    if request.user.is_authenticated:
        messages.info(request, 'Vous êtes déjà connecté.')
        return redirect(
            'quiz_list')  # Redirige vers la page d'accueil si déjà connecté

    if request.GET.get('next'):
        messages.info(request,
                      'Veuillez vous connecter pour accéder à cette page.')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get(
                    'next', 'admin_quiz_list'
                )  # Redirige vers 'next' ou 'admin_quiz_list'
                return redirect(next_url)
            else:
                # Ajoute un message d'erreur si l'authentification échoue
                messages.error(request,
                               'Identifiant ou mot de passe incorrect.')
        else:
            # Ajoute un message d'erreur si le formulaire est invalide
            messages.error(request,
                           'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form})


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email', )


def register_view(request):
    if request.user.is_authenticated:
        messages.info(request, 'Vous êtes déjà connecté.')
        return redirect('quiz_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        # Vérification reCAPTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify',
                          data=data)
        result = r.json()

        if not result.get('success'):
            messages.error(request, 'Validation reCAPTCHA requise')
        elif form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Inscription réussie !')
            return redirect('quiz_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()

    return render(request, 'app/register.html', {
        'form': form,
        'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
    })


@user_passes_test(lambda u: u.is_superuser)
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')

    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur est déjà pris.')
        else:
            user = User.objects.create_user(username=username,
                                            password=password1)
            user.is_staff = True
            user.save()
            messages.success(request, 'Administrateur créé avec succès.')
            return redirect('admin_users')

    return render(request, 'app/admin/admin_users.html', {'users': users})


@user_passes_test(lambda u: u.is_superuser)
def promote_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_staff = True
    user.save()
    messages.success(request, f'{user.username} a été promu administrateur.')
    return redirect('admin_users')


@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    if request.user == user:
        messages.error(request,
                       'Vous ne pouvez pas supprimer votre propre compte.')
    else:
        user.delete()
        messages.success(request, 'Utilisateur supprimé avec succès.')
    return redirect('admin_users')


@login_required
def stats(request):
    # Récupération des résultats de l'utilisateur
    user_results = UserQuizResult.objects.filter(
        user=request.user).order_by('completed_at')

    quiz_stats = []
    quizzes = Quiz.objects.filter(questions__isnull=False).distinct()

    for quiz in quizzes:
        quiz_results = user_results.filter(quiz=quiz)

        total_questions = quiz.questions.count()
        total_correct_answers = sum(result.score for result in quiz_results)
        calculated_points = quiz.level * total_correct_answers
        has_been_attempted = quiz_results.exists()
        if has_been_attempted:
            print("attempted")
        else:
            print("not attempted")

        quiz_stats.append({
            'quiz': quiz,
            'level': quiz.level,
            'total_questions': total_questions,
            'total_correct_answers': total_correct_answers,
            'calculated_points': calculated_points,
            'has_been_attempted': has_been_attempted
        })

    # Données pour le graphique d'évolution
    evolution_data = []
    for result in user_results:
        evolution_data.append({
            'date': result.completed_at.strftime('%Y-%m-%d'),
            'quiz': result.quiz.title,
            'score': result.score,
            'max_possible': result.quiz.questions.count(),
            'completion_time': result.completion_time
        })

    # Classement global
    # 1. Calcul du classement avec moyenne des scores
    leaderboard_data = UserQuizResult.objects.values(
        'user__id', 'user__username', 'user__date_joined').annotate(
            avg_score=Avg('score'),
            total_quizzes=Count('id')).order_by('-avg_score')

    # Calcul des scores totaux en multipliant le score par le niveau des quiz
    leaderboard_data = UserQuizResult.objects.values(
        'user__id', 'user__username', 'user__date_joined').annotate(
            total_points=Sum(F('score') * F('quiz__level')),
            avg_score=Avg('score'),
            total_quizzes=Count('id')).order_by('-total_points')

    # 2. Calcul de la position de l'utilisateur
    user_rank = None
    leaderboard = []
    for rank, entry in enumerate(leaderboard_data, start=1):
        leaderboard.append({
            'id': entry['user__id'],
            'username': entry['user__username'],
            'date_joined': entry['user__date_joined'],
            'avg_score': round(entry['avg_score'], 1),
            'total_quizzes': entry['total_quizzes'],
            'total_points': entry['total_points'],  # Ajout du score total
            'progress': 0  # À calculer si vous avez des données historiques
        })
        if entry['user__username'] == request.user.username:
            user_rank = rank

    # 3. Calcul du pourcentage top
    total_users = User.objects.count()
    top_percent = round(
        (user_rank / total_users) * 100, 1) if user_rank and total_users else 0

    # 4. Score moyen de l'utilisateur
    user_avg_score = user_results.aggregate(
        avg_score=Avg('score'))['avg_score'] or 0
    user_avg_score = round(user_avg_score, 1)

    # 5. Score total des points
    total_score = sum(result.score * result.quiz.level
                      for result in user_results)

    # Calcul de tous les points pour connaitre le maximum de points possible
    max_points = Quiz.objects.annotate(
        total_points=F('level') * Count('questions')).aggregate(
            Sum('total_points'))['total_points__sum'] or 0

    # Calculer le pourcentage de réussite
    percentage = round(total_score * 100 /
                       max_points, 1) if max_points > 0 else 0

    context = {
        'quiz_stats': quiz_stats,
        'evolution_data': evolution_data,
        'leaderboard': leaderboard[:50],  # Limiter à top 50
        'total_score': total_score,  # Ajouter le score total au contexte
        'user_rank': user_rank,
        'average_score': user_avg_score,  # Pour ranking_stats.html
        'top_percent': top_percent,
        'total_users': total_users,
        'max_points': max_points,  # Ajouter le score maximum au contexte
        'percentage': percentage,  # Ajouter le pourcentage au contexte
    }

    return render(request, 'app/stats.html', context)


from django.db.models import Sum, Count, F, Window, FloatField
from django.db.models.functions import DenseRank
from django.contrib.auth import get_user_model
from .models import UserQuizResult, Quiz

User = get_user_model()


class RankingSystem:

    @classmethod
    def get_global_ranking(cls, limit=100):
        """Classement général basé sur les points cumulés"""
        return User.objects.annotate(
            total_points=Sum('userquizresult__calculated_points'),
            total_quizzes=Count('userquizresult'),
            avg_score=Sum('userquizresult__score') * 1.0 /
            Sum('userquizresult__quiz__questions__count'),
            rank=Window(expression=DenseRank(),
                        order_by=F('total_points').desc())).filter(
                            total_points__isnull=False).order_by(
                                '-total_points')[:limit]

    @classmethod
    def get_quiz_ranking(cls, quiz_id, limit=50):
        """Classement spécifique à un quiz"""
        return UserQuizResult.objects.filter(quiz_id=quiz_id).annotate(
            rank=Window(expression=DenseRank(),
                        order_by=F(
                            'calculated_points').desc())).select_related(
                                'user',
                                'quiz').order_by('-calculated_points')[:limit]

    @classmethod
    def get_user_rank(cls, user):
        """Position de l'utilisateur dans le classement général"""
        rank = User.objects.annotate(
            total_points=Sum('userquizresult__calculated_points')).filter(
                total_points__gt=User.objects.filter(pk=user.pk).annotate(
                    user_points=Sum('userquizresult__calculated_points')).
                values('user_points')[0]['user_points']).count() + 1

        total_users = User.objects.annotate(
            total_points=Sum('userquizresult__calculated_points')).filter(
                total_points__isnull=False).count()

        return {
            'rank':
            rank,
            'top_percent':
            round((rank / total_users) * 100, 1) if total_users > 0 else 0,
            'total_users':
            total_users
        }

    @classmethod
    def get_user_stats(cls, user):
        """Statistiques détaillées de l'utilisateur"""
        stats = UserQuizResult.objects.filter(user=user).aggregate(
            total_points=Sum('calculated_points'),
            total_quizzes=Count('id'),
            total_questions=Sum('quiz__questions__count'),
            total_correct=Sum('score'),
            avg_time=Avg('completion_time'))

        stats['accuracy'] = round(
            (stats['total_correct'] / stats['total_questions'] *
             100), 1) if stats['total_questions'] else 0

        return stats


def custom_logout(request):
    logout(request)  # Déconnecte l'utilisateur
    messages.success(
        request,
        'Vous avez été déconnecté avec succès.')  # Ajoute un message de succès
    return redirect('login')  # Redirige vers la page de connexion


def terms_view(request):
    return render(request, 'app/terms.html')


def privacy_view(request):
    return render(request, 'app/privacy.html')


# Administration
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    if request.method == 'POST':
        if 'delete_quiz' in request.POST:
            quiz.delete()
            messages.success(request, 'Le quiz a été supprimé avec succès.')
            return redirect('custom_admin')
        elif 'update_quiz' in request.POST:
            form = QuizForm(request.POST, instance=quiz)
            if form.is_valid():
                form.save()
                messages.success(request,
                                 'Le quiz a été mis à jour avec succès.')
                return redirect('admin_quiz_detail', quiz_id=quiz.id)
            else:
                # Le formulaire invalide sera réaffiché avec les erreurs
                pass
        elif 'go_back' in request.POST:
            return redirect('custom_admin')
    else:
        form = QuizForm(instance=quiz)

    return render(request, 'app/admin/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions,
        'form': form
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def custom_admin(request):
    quizzes = Quiz.objects.all()
    questions = Question.objects.all()

    if request.method == 'POST':
        if 'add_quiz' in request.POST:
            quiz_form = QuizForm(request.POST)
            if quiz_form.is_valid():
                quiz = quiz_form.save()
                messages.success(
                    request, f'Le quiz "{quiz.title}" a été créé avec succès!')
                return redirect('custom_admin')
            else:
                for field, errors in quiz_form.errors.items():
                    for error in errors:
                        messages.error(
                            request, f"Erreur dans le champ {field}: {error}")
        elif 'add_question' in request.POST:
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                question = question_form.save()
                messages.success(request,
                                 f'La question a été ajoutée avec succès!')
                return redirect('custom_admin')
            else:
                for field, errors in question_form.errors.items():
                    for error in errors:
                        messages.error(
                            request, f"Erreur dans le champ {field}: {error}")

    quiz_form = QuizForm()
    question_form = QuestionForm()

    return render(
        request, 'app/admin/custom_admin.html', {
            'quizzes': quizzes,
            'questions': questions,
            'quiz_form': quiz_form,
            'question_form': question_form,
        })


@login_required
@user_passes_test(
    lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            return redirect('admin_quiz_detail', quiz_id=quiz.id)
    else:
        form = QuestionForm()
    return render(request, 'app/admin/add_question.html', {
        'form': form,
        'quiz': quiz
    })


@login_required
@user_passes_test(
    lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    quiz_id = question.quiz.id  # Récupère l'ID du quiz associé

    if request.method == 'POST':
        if 'delete_question' in request.POST:  # Si le bouton "Supprimer" est cliqué
            question.delete()
            messages.success(request,
                             'La question a été supprimée avec succès.')
            return redirect('admin_quiz_detail', quiz_id=quiz_id)
        elif 'go_back' in request.POST:  # Si le bouton "Retour" est cliqué
            print('go back')
            return redirect('admin_quiz_detail', quiz_id=quiz_id)
        else:
            messages.success(request,
                             'La question a été modifiée avec succès.')
            form = QuestionForm(request.POST, instance=question)
            if form.is_valid():
                form.save()
                return redirect('admin_quiz_detail', quiz_id=quiz_id)
    else:
        form = QuestionForm(instance=question)

    return render(request, 'app/admin/edit_question.html', {
        'form': form,
        'question': question,
        'quiz_id': quiz_id,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def add_quiz(request):
    if request.method == 'POST':
        form = QuizForm(request.POST, request.FILES)
        if form.is_valid():
            quiz = form.save(commit=False)

            # Gestion de l'upload d'image
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                # Upload vers Imgur
                image_url = ImgurUploader.upload_image(image_file)
                if image_url:
                    quiz.image_url = image_url

            quiz.save()
            messages.success(request, 'Le quiz a été ajouté avec succès.')
            return redirect('admin_quiz_list')
    else:
        form = QuizForm()

    return render(request, 'app/admin/add_quiz.html', {
        'form': form,
        'imgur_client_id': settings.IMGUR_CLIENT_ID
    })


from collections import defaultdict


@login_required
def quiz_list(request):
    user = request.user

    # Récupération des résultats de l'utilisateur
    user_results = UserQuizResult.objects.filter(
        user=request.user).order_by('completed_at')

    # Calcul de tous les points pour connaitre le maximum de points possible
    max_points = Quiz.objects.annotate(
        total_points=F('level') * Count('questions')).aggregate(
            Sum('total_points'))['total_points__sum'] or 0

    # Récupérer tous les quiz triés par niveau
    quizzes = Quiz.objects.all().order_by('level')

    # Filtrer les quiz qui ont été réalisés par l'utilisateur
    completed_quiz_ids = UserQuizResult.objects.filter(user=user).values_list(
        'quiz_id', flat=True)

    # Annoter chaque quiz complété avec le nombre de questions et le score de l'utilisateur
    completed_quizzes = []
    for quiz_id in completed_quiz_ids:
        quiz = Quiz.objects.get(id=quiz_id)
        result = UserQuizResult.objects.filter(user=user, quiz=quiz).latest(
            'completed_at')  # Prend le résultat le plus récent
        total_questions = quiz.questions.count()
        percentage = round(result.score * 100 /
                           total_questions, 1) if total_questions > 0 else 0
        completed_quizzes.append({
            'quiz': quiz,
            'total_questions': total_questions,
            'user_score': result.score,
            'percentage': percentage,
        })

    # 5. Score total des points
    total_score = sum(result.score * result.quiz.level
                      for result in user_results)

    # Calculer le pourcentage de réussite
    percentage = round(total_score * 100 /
                       max_points, 1) if max_points > 0 else 0

    # Grouper les quiz non complétés par thème
    remaining_quizzes = quizzes.exclude(id__in=completed_quiz_ids)
    quizzes_by_theme = defaultdict(list)
    for quiz in remaining_quizzes:
        theme = quiz.theme if quiz.theme else "Autres"
        quizzes_by_theme[theme].append(quiz)

    # Convertir en liste de tuples pour le template
    quizzes_by_theme = sorted(quizzes_by_theme.items(), key=lambda x: x[0])

    # Classement des joueurs en calculant leurs points.
    leaderboard_data = UserQuizResult.objects.values(
        'user__id', 'user__username', 'user__date_joined').annotate(
            total_points=Sum(F('score') * F('quiz__level')),
            avg_score=Avg('score'),
            total_quizzes=Count('id')).order_by('-total_points')

    leaderboard = []
    for rank, entry in enumerate(leaderboard_data, start=1):
        leaderboard.append({
            'id': entry['user__id'],
            'username': entry['user__username'],
            'date_joined': entry['user__date_joined'],
            'avg_score': round(entry['avg_score'], 1),
            'total_quizzes': entry['total_quizzes'],
            'total_points': entry['total_points'],
            'rank': rank
        })

    context = {
        'quizzes_by_theme': quizzes_by_theme,
        'quizzes': remaining_quizzes,
        'total_score': total_score,
        'max_points': max_points,
        'percentage': percentage,
        'completed_quizzes_data':
        completed_quizzes,  # Renommé pour éviter la confusion
        'leaderboard': leaderboard[:3],  # Limiter à top 3
    }
    return render(request, 'app/quiz_list.html', context)


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    total = quiz.questions.count()
    # Récupérer le score enregistré pour l'utilisateur et le quiz
    user_result = UserQuizResult.objects.filter(user=request.user,
                                                quiz=quiz).first()
    saved_score = user_result.score if user_result else None

    if saved_score:
        # Calculer le pourcentage de réussite
        percentage = round(saved_score * 100 / total, 1) if total > 0 else 0

    # Classement des joueurs pour le quiz actuel
    leaderboard_data = UserQuizResult.objects.filter(quiz=quiz).values(
        'user__id', 'user__username', 'user__date_joined').annotate(
            total_points=Sum(F('score') * F('quiz__level')),
            avg_score=Avg('score'),
            total_quizzes=Count('id')).order_by('-total_points')

    leaderboard = []
    for rank, entry in enumerate(leaderboard_data, start=1):
        leaderboard.append({
            'id': entry['user__id'],
            'username': entry['user__username'],
            'date_joined': entry['user__date_joined'],
            'avg_score': round(entry['avg_score'], 1),
            'total_quizzes': entry['total_quizzes'],
            'total_points': entry['total_points'],
            'rank': rank
        })

    if request.method == 'POST':
        start_time = datetime.now()  # À enregistrer au début du quiz

        # Calcul du score et préparation des corrections
        score = 0
        corrections = []

        for question in quiz.questions.all():
            user_answer = request.POST.get(f'question_{question.id}')
            is_correct = False
            correct_answer = None

            # Déterminer la bonne réponse
            if question.reponse1_is_correct:
                correct_answer = 'reponse1'
            elif question.reponse2_is_correct:
                correct_answer = 'reponse2'
            elif question.reponse3_is_correct:
                correct_answer = 'reponse3'

            # Vérifier la réponse de l'utilisateur
            if user_answer == correct_answer:
                score += 1
                is_correct = True

            corrections.append({
                'question': question,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })

        # Calcul du temps de complétion en secondes
        end_time = datetime.now()
        completion_time = (end_time - start_time).total_seconds()

        # Enregistrement du résultat uniquement si le quiz n'a pas été fait
        if not UserQuizResult.objects.filter(user=request.user,
                                             quiz=quiz).exists():
            UserQuizResult.objects.create(user=request.user,
                                          quiz=quiz,
                                          score=score,
                                          completion_time=completion_time)

        # Calculer le pourcentage de réussite
        percentage = round(score * 100 / total, 1) if total > 0 else 0

        return render(
            request,
            'app/quiz_results.html',
            {
                'quiz': quiz,
                'score': score,
                'total': total,
                'percentage': percentage,
                'corrections': corrections,
                'completion_time': int(completion_time),
                'leaderboard': leaderboard[:3],  # Limiter à top 3
                'level': quiz.level,
            })

    # Vérifier si l'utilisateur a déjà complété ce quiz
    if UserQuizResult.objects.filter(user=request.user, quiz=quiz).exists():
        messages.warning(
            request,
            "Vous avez déjà complété ce quiz. Les points ne seront pas comptabilisés."
        )

        return render(
            request,
            'app/take_quiz.html',
            {
                'quiz': quiz,
                'score': saved_score,
                'total': total,
                'percentage': percentage,
                'leaderboard': leaderboard[:3],  # Limiter à top 3
                'level': quiz.level,
            })

    return render(request, 'app/take_quiz.html', {
        'quiz': quiz,
    })


def my_results(request):
    results = UserQuizResult.objects.filter(
        user=request.user).order_by('-completed_at')
    return render(request, 'app/my_results.html', {'results': results})


class QuizExportView(View):

    def get(self, request, quiz_id, format_type):
        quiz = Quiz.objects.get(pk=quiz_id)

        if format_type == 'json':
            return self.export_as_json(quiz)
        elif format_type == 'csv':
            return self.export_as_csv(quiz)
        else:
            return JsonResponse({'error': 'Format non supporté'}, status=400)

    def export_as_json(self, quiz):
        data = {
            "title": quiz.title,
            "description": quiz.description,
            "theme": quiz.theme,  # Ajout du thème
            "level": quiz.level,
            "questions": []
        }

        for question in quiz.questions.all():
            q_data = {
                "text": question.text,
                "reponse1": question.reponse1,
                "reponse1_is_correct": question.reponse1_is_correct,
                "reponse2": question.reponse2,
                "reponse2_is_correct": question.reponse2_is_correct,
                "reponse3": question.reponse3,
                "reponse3_is_correct": question.reponse3_is_correct
            }
            data["questions"].append(q_data)

        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response[
            'Content-Disposition'] = f'attachment; filename="{quiz.title}.json"'
        return response

    def export_as_csv(self, quiz):
        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = f'attachment; filename="{quiz.title}.csv"'

        writer = csv.writer(response)
        # Modifiez l'en-tête pour inclure le thème
        writer.writerow([
            'title', 'description', 'theme', 'level', 'question_text',
            'reponse1', 'reponse1_correct', 'reponse2', 'reponse2_correct',
            'reponse3', 'reponse3_correct'
        ])

        for question in quiz.questions.all():
            writer.writerow([
                quiz.title,
                quiz.description,
                quiz.theme,
                quiz.level,
                question.text,  # Ajout du thème
                question.reponse1,
                int(question.reponse1_is_correct),
                question.reponse2,
                int(question.reponse2_is_correct),
                question.reponse3,
                int(question.reponse3_is_correct)
            ])


class QuizImportView(View):

    def post(self, request):
        format_type = request.POST.get('format_type')
        file = request.FILES.get('file')

        if not file:
            messages.error(request, "Aucun fichier n'a été fourni")
            return redirect('admin_quiz_list')

        try:
            if format_type == 'json':
                return self.import_from_json(request, file)
            elif format_type == 'csv':
                return self.import_from_csv(request, file)
            else:
                messages.error(request, "Format de fichier non supporté")
                return redirect('admin_quiz_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'import: {str(e)}")
            return redirect('admin_quiz_list')

    def import_from_json(self, request, file):
        data = json.load(file)

        quiz = Quiz.objects.create(
            title=data['title'],
            description=data['description'],
            theme=data.get('theme', 'autre'),  # Valeur par défaut si absent
            level=data.get('level', 2))
        for q_data in data['questions']:
            Question.objects.create(
                quiz=quiz,
                text=q_data['text'],
                reponse1=q_data['reponse1'],
                reponse1_is_correct=q_data['reponse1_is_correct'],
                reponse2=q_data['reponse2'],
                reponse2_is_correct=q_data['reponse2_is_correct'],
                reponse3=q_data['reponse3'],
                reponse3_is_correct=q_data['reponse3_is_correct'])

        messages.success(request,
                         f"Le quiz '{quiz.title}' a été importé avec succès!")
        return redirect('admin_quiz_list')

    def import_from_csv(self, request, file):
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        quiz = None

        for row in reader:
            if not quiz:
                quiz = Quiz.objects.create(
                    title=row['title'],
                    description=row['description'],
                    theme=row.get('theme',
                                  'autre'),  # Valeur par défaut si absent
                    level=int(row.get('level', 2)))
            Question.objects.create(
                quiz=quiz,
                text=row['question_text'],
                reponse1=row['reponse1'],
                reponse1_is_correct=bool(int(row['reponse1_correct'])),
                reponse2=row['reponse2'],
                reponse2_is_correct=bool(int(row['reponse2_correct'])),
                reponse3=row['reponse3'],
                reponse3_is_correct=bool(int(row['reponse3_correct'])))

        messages.success(request,
                         f"Le quiz '{quiz.title}' a été importé avec succès!")
        return redirect('admin_quiz_list')


@login_required
@user_passes_test(lambda u: u.is_staff)
def import_export_view(request):
    quizzes = Quiz.objects.all()
    return render(request, 'app/admin/import_export.html',
                  {'quizzes': quizzes})


@login_required
@user_passes_test(lambda u: u.is_staff)
def export_quiz_selection(request):
    quizzes = Quiz.objects.all()
    return render(request, 'app/admin/export_selection.html',
                  {'quizzes': quizzes})


def import_from_json(self, file):
    try:
        data = json.load(file)
        quiz = Quiz.objects.create(title=data['title'],
                                   description=data['description'])

        for q_data in data['questions']:
            Question.objects.create(
                quiz=quiz,
                text=q_data['text'],
                reponse1=q_data['reponse1'],
                reponse1_is_correct=q_data['reponse1_is_correct'],
                reponse2=q_data['reponse2'],
                reponse2_is_correct=q_data['reponse2_is_correct'],
                reponse3=q_data['reponse3'],
                reponse3_is_correct=q_data['reponse3_is_correct'])

        messages.success(self.request,
                         f'Quiz "{quiz.title}" importé avec succès!')
        return redirect('admin_quiz_detail', quiz_id=quiz.id)

    except Exception as e:
        messages.error(self.request, f"Erreur lors de l'import: {str(e)}")
        return redirect('import_export')


@login_required
def leaderboard(request):
    # 1. On récupère d'abord tous les utilisateurs ayant des résultats
    users_with_results = User.objects.filter(
        userquizresult__isnull=False).distinct()

    # 2. On prépare une liste pour stocker les statistiques
    leaderboard_data = []

    for user in users_with_results:
        # Récupère tous les résultats de l'utilisateur
        results = UserQuizResult.objects.filter(user=user)

        # Calcule le nombre total de quizzes tentés
        total_quizzes = results.count()

        # Calcule le score total (somme des scores)
        total_score = results.aggregate(Sum('score'))['score__sum'] or 0

        # Calcule le total des questions (somme des questions de chaque quiz)
        total_questions = sum(result.quiz.questions.count()
                              for result in results)

        # Calcule le pourcentage moyen de réussite
        if total_questions > 0:
            avg_percentage = round((total_score / total_questions) * 100, 1)
        else:
            avg_percentage = 0

        # Dernière activité
        last_activity = results.aggregate(
            Max('completed_at'))['completed_at__max']

        leaderboard_data.append({
            'user': user,
            'total_quizzes': total_quizzes,
            'avg_percentage': avg_percentage,
            'last_activity': last_activity,
            'total_score': total_score,
            'total_questions': total_questions
        })

    # Trie par pourcentage moyen décroissant
    leaderboard_data.sort(key=lambda x: x['avg_percentage'], reverse=True)

    # Position de l'utilisateur actuel
    user_position = None
    for idx, entry in enumerate(leaderboard_data, start=1):
        if entry['user'].id == request.user.id:
            user_position = {
                'position': idx,
                'total_quizzes': entry['total_quizzes'],
                'avg_percentage': entry['avg_percentage'],
                'total_score': entry['total_score'],
                'total_questions': entry['total_questions']
            }
            break

    context = {
        'leaderboard': leaderboard_data[:100],  # Top 100
        'user_position': user_position,
    }
    return render(request, 'app/leaderboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def update_quiz_image(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == 'POST' and 'image' in request.FILES:
        image_file = request.FILES['image']
        image_url = ImgurUploader.upload_image(image_file)

        if image_url:
            quiz.image_url = image_url
            quiz.save()
            messages.success(request, "L'image du quiz a été mise à jour.")
        else:
            messages.error(request, "Erreur lors de l'upload de l'image.")

    return redirect('admin_quiz_detail', quiz_id=quiz.id)


def contact_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        message = request.POST.get('message')
        captcha_response = request.POST.get('g-recaptcha-response')

        # Vérification du captcha
        if not captcha_response:
            messages.error(request, 'Veuillez compléter le captcha.')
        else:
            data = {
                'secret': settings.RECAPTCHA_PRIVATE_KEY,
                'response': captcha_response
            }
            r = requests.post(
                'https://www.google.com/recaptcha/api/siteverify', data=data)
            result = r.json()

            if not result['success']:
                messages.error(request,
                               'Captcha invalide. Veuillez réessayer.')
            else:
                # Envoi de l'email
                subject = f"Message de contact de {email}"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Votre message a bien été envoyé !')
                return redirect('contact')

    return render(request, 'app/contact.html',
                  {'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from .models import Message
from .forms import MessageForm

from django.db.models import Q


@login_required
def message_inbox(request):
    messages = Message.objects.filter(
        Q(recipients=request.user) | Q(is_public=True)).exclude(
            author=request.user).distinct().order_by('-created_at')

    # Ajoute l'information de lecture à chaque message
    for message in messages:
        message.user_has_read = message.read_by.filter(
            id=request.user.id).exists()

    return render(request, 'app/message_inbox.html', {
        'messages': messages,
        'current_user': request.user
    })


@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if not message.is_public and request.user not in message.recipients.all():
        return HttpResponseForbidden()

    # Marquer comme lu
    if not message.read_by.filter(id=request.user.id).exists():
        message.read_by.add(request.user)

    return render(request, 'app/message_detail.html', {'message': message})


@user_passes_test(lambda u: u.is_staff)
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.save()
            form.save_m2m()  # Pour les destinataires

            # Ajouter une notification
            messages.success(request, "Message envoyé avec succès")
            return redirect('message_inbox')
    else:
        form = MessageForm()

    return render(request, 'app/send_message.html', {'form': form})


@login_required
def update_profile(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get(
            'first_name',
            '').strip()  # Convertit None en '' et supprime les espaces
        last_name = request.POST.get(
            'last_name',
            '').strip()  # Convertit None en '' et supprime les espaces
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        user = request.user

        # Mise à jour des champs seulement s'ils sont fournis
        if email and email != user.email:
            user.email = email
            messages.success(request, 'Adresse email mise à jour avec succès.')

        # Mise à jour du prénom (peut être vide)
        user.first_name = first_name
        if first_name:
            messages.success(request, 'Prénom mis à jour avec succès.')

        # Mise à jour du nom de famille (peut être vide)
        user.last_name = last_name
        if last_name:
            messages.success(request, 'Nom de famille mis à jour avec succès.')

        # Changement de mot de passe
        if current_password and new_password1 and new_password2:
            if user.check_password(current_password):
                if new_password1 == new_password2:
                    user.set_password(new_password1)
                    messages.success(request,
                                     'Mot de passe changé avec succès.')
                    update_session_auth_hash(request, user)
                else:
                    messages.error(
                        request,
                        'Les nouveaux mots de passe ne correspondent pas.')
            else:
                messages.error(request, 'Mot de passe actuel incorrect.')

        user.save()
        return redirect('stats')

    return redirect('stats')
