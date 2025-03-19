from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Quiz, Question, Answer

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz', 'text']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['question', 'text', 'is_correct']