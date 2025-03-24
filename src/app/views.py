from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import LoginForm, QuizForm, QuestionForm, AnswerForm
from .models import Quiz, Question, Answer, UserQuizResult
from django.contrib import messages


def login_view(request):
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


@login_required
def stats(request):
    results = UserQuizResult.objects.filter(
        user=request.user)  # Récupère les résultats de l'utilisateur
    return render(request, 'app/stats.html', {'results': results})


def custom_logout(request):
    logout(request)  # Déconnecte l'utilisateur
    messages.success(
        request,
        'Vous avez été déconnecté avec succès.')  # Ajoute un message de succès
    return redirect('login')  # Redirige vers la page de connexion


from django.shortcuts import render, redirect
from .forms import QuestionForm, AnswerForm, AnswerFormSet
from .models import Quiz
from django.template.loader import render_to_string

from django.http import JsonResponse
from django.template.loader import render_to_string


# Administration
@login_required
@user_passes_test(
    lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
def admin_quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()  # Récupère toutes les questions du quiz
    return render(request, 'app/admin/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions
    })


@login_required
@user_passes_test(
    lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
def custom_admin(request):
    quizzes = Quiz.objects.all()
    questions = Question.objects.all()
    answers = Answer.objects.all()

    if request.method == 'POST':
        if 'add_quiz' in request.POST:
            quiz_form = QuizForm(request.POST)
            if quiz_form.is_valid():
                quiz_form.save()
                return redirect('custom_admin')
        elif 'add_question' in request.POST:
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                question_form.save()
                return redirect('custom_admin')
        elif 'add_answer' in request.POST:
            answer_form = AnswerForm(request.POST)
            if answer_form.is_valid():
                answer_form.save()
                return redirect('custom_admin')
    else:
        quiz_form = QuizForm()
        question_form = QuestionForm()
        answer_form = AnswerForm()

    return render(
        request, 'app/admin/custom_admin.html', {
            'quizzes': quizzes,
            'questions': questions,
            'answers': answers,
            'quiz_form': quiz_form,
            'question_form': question_form,
            'answer_form': answer_form,
        })


@login_required
@user_passes_test(
    lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_formset = AnswerFormSet(request.POST)
        if question_form.is_valid() and answer_formset.is_valid():
            # Sauvegarder la question
            question = question_form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'La question a été ajoutée avec succès.')
            # Sauvegarder les réponses
            answers = answer_formset.save(commit=False)
            for answer in answers:
                answer.question = question
                answer.save()
            return redirect('admin_quiz_detail', quiz_id=quiz.id)
    else:
        messages.info(request, 'Veuillez remplir le formulaire ci-dessous.')
        question_form = QuestionForm()
        answer_formset = AnswerFormSet()
    return render(
        request, 'app/admin/add_question.html', {
            'quiz': quiz,
            'question_form': question_form,
            'answer_formset': answer_formset,
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
            return redirect('admin_quiz_detail', quiz_id=quiz_id)
        else:

            question_form = QuestionForm(request.POST, instance=question)
            answer_formset = AnswerFormSet(request.POST, instance=question)
            if question_form.is_valid() and answer_formset.is_valid():
                print('test')
                # Sauvegarder la
                # question
                question_form.save()
                # Sauvegarder les réponses
                answers = answer_formset.save(commit=False)
                for answer in answers:
                    # Ne pas enregistrer les réponses vides
                    if answer.text.strip(
                    ):  # Vérifie si le champ n'est pas vide
                        answer.question = question
                        answer.save()
                # Rediriger vers la page de détail du quiz
                return redirect('admin_quiz_detail', quiz_id=quiz_id)
    else:
        question_form = QuestionForm(instance=question)
        # Limiter le nombre de réponses à 3
        answer_formset = AnswerFormSet(instance=question)
        if question.answers.count() >= 3:
            answer_formset.extra = 0  # Ne pas afficher de champs supplémentaires

    return render(
        request, 'app/admin/edit_question.html', {
            'question_form': question_form,
            'answer_formset': answer_formset,
            'question': question,
        })


@login_required
@user_passes_test(
    lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
def add_quiz(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Le quiz a été ajouté avec succès.')
            form.save()
            return redirect('admin_quiz_list')
    else:
        form = QuizForm()
    return render(request, 'app/admin/add_quiz.html', {'form': form})


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

        # Enregistrement du score
        if request.user.is_authenticated:
            UserQuizResult.objects.create(user=request.user,
                                          quiz=quiz,
                                          score=score)

        return render(
            request, 'app/quiz_results.html', {
                'quiz': quiz,
                'score': score,
                'total': quiz.questions.count(),
                'corrections': corrections
            })

    return render(request, 'app/take_quiz.html', {'quiz': quiz})


def my_results(request):
    results = UserQuizResult.objects.filter(
        user=request.user).order_by('-completed_at')
    return render(request, 'app/my_results.html', {'results': results})
