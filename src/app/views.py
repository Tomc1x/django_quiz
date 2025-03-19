from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import LoginForm, QuizForm, QuestionForm, AnswerForm
from .models import Quiz, Question, Answer, UserQuizResult
from django.contrib import messages

def login_view(request):
    if request.GET.get('next'):
        messages.info(request, 'Veuillez vous connecter pour accéder à cette page.')


    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'quiz_list')  # Redirige vers 'next' ou 'quiz_list'
                return redirect(next_url)
            else:
                # Ajoute un message d'erreur si l'authentification échoue
                messages.error(request, 'Identifiant ou mot de passe incorrect.')
        else:
            # Ajoute un message d'erreur si le formulaire est invalide
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form})



@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all()  # Récupère tous les quiz
    return render(request, 'app/quiz_list.html', {'quizzes': quizzes})



@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)

    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                selected_answer = Answer.objects.get(id=selected_answer_id)
                if selected_answer.is_correct:
                    score += 1

        # Enregistre le résultat
        UserQuizResult.objects.create(
            user=request.user,
            quiz=quiz,
            score=score
        )
        return redirect('stats')  # Redirige vers la page des statistiques

    return render(request, 'app/quiz_detail.html', {'quiz': quiz, 'questions': questions})



@login_required
def stats(request):
    results = UserQuizResult.objects.filter(user=request.user)  # Récupère les résultats de l'utilisateur
    return render(request, 'app/stats.html', {'results': results})



@login_required
@user_passes_test(lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
def custom_admin(request):
    if request.method == 'POST':
        quiz_form = QuizForm(request.POST)
        if quiz_form.is_valid():
            quiz_form.save()
            return redirect('custom_admin')
    else:
        quiz_form = QuizForm()

    quizzes = Quiz.objects.all()
    return render(request, 'app/admin.html', {'quiz_form': quiz_form, 'quizzes': quizzes})

@login_required
@user_passes_test(lambda u: u.is_staff)  # Seuls les administrateurs peuvent accéder
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

    return render(request, 'app/custom_admin.html', {
        'quizzes': quizzes,
        'questions': questions,
        'answers': answers,
        'quiz_form': quiz_form,
        'question_form': question_form,
        'answer_form': answer_form,
    })


def custom_logout(request):
    logout(request)  # Déconnecte l'utilisateur
    messages.success(request, 'Vous avez été déconnecté avec succès.')  # Ajoute un message de succès
    return redirect('login')  # Redirige vers la page de connexion