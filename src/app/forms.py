from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Quiz, Question
from django.forms import inlineformset_factory


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Entrez votre identifiant',
        }))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Entrez votre mot de passe',
        }))


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
import requests

from django import forms
from .models import Message
from django.contrib.auth.models import User


class MessageForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Destinataires spécifiques")

    class Meta:
        model = Message
        fields = [
            'title', 'content', 'message_type', 'is_public', 'recipients'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False,
                             widget=forms.EmailInput(
                                 attrs={
                                     'class': 'form-control form-control-lg',
                                     'placeholder': 'Email (facultatif)'
                                 }))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des champs existants
        self.fields['username'].widget.attrs.update({
            'class':
            'form-control form-control-lg',
            'placeholder':
            'Nom d\'utilisateur'
        })
        self.fields['password1'].widget.attrs.update({
            'class':
            'form-control form-control-lg',
            'placeholder':
            'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class':
            'form-control form-control-lg',
            'placeholder':
            'Confirmation du mot de passe'
        })


from django import forms
from .models import Quiz


class QuizForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        label="Image du quiz",
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control',
            'id': 'quizImageUpload'
        }))

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'image']


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question
        fields = [
            'text',
            'reponse1',
            'reponse1_is_correct',
            'reponse2',
            'reponse2_is_correct',
            'reponse3',
            'reponse3_is_correct',
        ]
        widgets = {
            'text':
            forms.TextInput(attrs={'class': 'form-control'}),
            'reponse1':
            forms.TextInput(attrs={'class': 'form-control'}),
            'reponse2':
            forms.TextInput(attrs={'class': 'form-control'}),
            'reponse3':
            forms.TextInput(attrs={'class': 'form-control'}),
            'reponse1_is_correct':
            forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reponse2_is_correct':
            forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reponse3_is_correct':
            forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# # Formulaire en ligne pour les réponses
# AnswerFormSet = inlineformset_factory(
#     Question,  # Modèle parent
#     Answer,    # Modèle enfant
#     form=AnswerForm,  # Formulaire pour les réponses
#     extra=3,  # Nombre de réponses vides à afficher
#     can_delete=False,  # Désactiver la suppression des réponses
# )
