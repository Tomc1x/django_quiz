from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

from .forms import LoginForm, QuizForm, QuestionForm
from .models import Quiz, Question, UserQuizResult


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


@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all()  # Récupère tous les quiz
    return render(request, 'app/admin/quiz_list.html', {'quizzes': quizzes})


from django.db.models import Avg, Count, Max
from datetime import datetime, timedelta

from django.db.models import Avg, Count, Max, Min
from datetime import datetime, timedelta
import json
from django.db.models.functions import TruncDate
from django.contrib.auth.models import User

from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone


@login_required
def stats(request):
    # Gestion de la période
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    end_date = timezone.now()

    # Si période personnalisée
    if 'start_date' in request.GET and 'end_date' in request.GET:
        try:
            start_date = datetime.strptime(request.GET['start_date'],
                                           '%Y-%m-%d')
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d')
            days = (end_date - start_date).days
        except (ValueError, TypeError):
            pass

    # Récupération des résultats de l'utilisateur
    user_results = UserQuizResult.objects.filter(
        user=request.user,
        completed_at__gte=start_date,
        completed_at__lte=end_date).order_by('completed_at')

    quiz_stats = []
    quizzes = Quiz.objects.filter(questions__isnull=False).distinct()

    for quiz in quizzes:
        quiz_results = user_results.filter(quiz=quiz)
        if not quiz_results.exists():
            continue

        total_questions = quiz.questions.count()
        scores = [
            round((result.score / total_questions) * 100)
            for result in quiz_results
        ]

        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        last_score = scores[-1]
        first_score = scores[0] if len(scores) > 1 else last_score

        progress = ((last_score - first_score) /
                    first_score) * 100 if first_score != 0 else 0

        quiz_stats.append({
            'quiz':
            quiz,
            'attempts':
            len(scores),
            'best_score':
            max_score,
            'max_score':
            max_score,
            'min_score':
            min_score,
            'last_score':
            last_score,
            'progress':
            round(progress, 1),
            'completion_time_avg':
            round(
                quiz_results.aggregate(
                    Avg('completion_time'))['completion_time__avg'], 1),
            'results':
            quiz_results
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

    context = {
        'quiz_stats':
        quiz_stats,
        'evolution_data':
        evolution_data,
        'leaderboard':
        leaderboard[:50],  # Limiter à top 50
        'user_rank':
        user_rank,
        'average_score':
        user_avg_score,  # Pour ranking_stats.html
        'top_percent':
        top_percent,
        'total_users':
        total_users,
        'selected_days':
        days,
        'start_date':
        start_date.strftime('%Y-%m-%d')
        if 'start_date' not in request.GET else request.GET['start_date'],
        'end_date':
        end_date.strftime('%Y-%m-%d')
        if 'end_date' not in request.GET else request.GET['end_date'],
    }

    return render(request, 'app/stats.html', context)


def custom_logout(request):
    logout(request)  # Déconnecte l'utilisateur
    messages.success(
        request,
        'Vous avez été déconnecté avec succès.')  # Ajoute un message de succès
    return redirect('login')  # Redirige vers la page de connexion


# Administration
@login_required
@user_passes_test(
    lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
def admin_quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()  # Récupère toutes les questions du quiz
    if request.method == 'POST':
        if 'delete_quiz' in request.POST:
            print('delete_quiz')
            quiz.delete()
            messages.success(request, 'Le quiz a été supprimé avec succès.')
            return redirect('custom_admin')
        elif 'go_back' in request.POST:
            print('go back')
            return redirect('custom_admin')

    return render(request, 'app/admin/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions
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


from django.core.files.storage import default_storage
from .imgur_uploader import ImgurUploader


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


from django.shortcuts import render
from .models import Quiz


def quiz_list(request):
    quizzes = Quiz.objects.all()
    return render(request, 'app/quiz_list.html', {'quizzes': quizzes})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Quiz, UserQuizResult


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

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

        # Enregistrement du résultat
        UserQuizResult.objects.create(user=request.user,
                                      quiz=quiz,
                                      score=score,
                                      completion_time=completion_time)

        return render(
            request, 'app/quiz_results.html', {
                'quiz': quiz,
                'score': score,
                'total': quiz.questions.count(),
                'corrections': corrections,
                'completion_time': int(completion_time)
            })

    return render(request, 'app/take_quiz.html', {'quiz': quiz})


def my_results(request):
    results = UserQuizResult.objects.filter(
        user=request.user).order_by('-completed_at')
    return render(request, 'app/my_results.html', {'results': results})


import json
import csv
from django.http import HttpResponse, JsonResponse
from django.views import View
from .models import Quiz, Question


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
        # En-tête
        writer.writerow([
            'title', 'description', 'question_text', 'reponse1',
            'reponse1_correct', 'reponse2', 'reponse2_correct', 'reponse3',
            'reponse3_correct'
        ])

        for question in quiz.questions.all():
            writer.writerow([
                quiz.title, quiz.description, question.text, question.reponse1,
                int(question.reponse1_is_correct), question.reponse2,
                int(question.reponse2_is_correct), question.reponse3,
                int(question.reponse3_is_correct)
            ])

        return response


from django.contrib import messages
from django.shortcuts import redirect


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

        messages.success(request,
                         f"Le quiz '{quiz.title}' a été importé avec succès!")
        return redirect('admin_quiz_list')

    def import_from_csv(self, request, file):
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        quiz = None

        for row in reader:
            if not quiz:
                quiz = Quiz.objects.create(title=row['title'],
                                           description=row['description'])

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
    # Classement complet avec plus de détails
    leaderboard = UserQuizResult.objects.values(
        'user__username', 'user__id').annotate(
            total_quizzes=Count('id'),
            avg_score=Avg('score'),
            last_activity=Max('completed_at')).order_by('-avg_score')

    # Position de l'utilisateur actuel
    user_position = None
    for idx, entry in enumerate(leaderboard, start=1):
        if entry['user__id'] == request.user.id:
            user_position = {
                'position': idx,
                'total_quizzes': entry['total_quizzes'],
                'avg_score': entry['avg_score']
            }
            break

    context = {
        'leaderboard': leaderboard[:100],  # Top 100
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
