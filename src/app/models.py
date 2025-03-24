from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey('Quiz',
                             on_delete=models.CASCADE,
                             related_name='questions')
    text = models.CharField(max_length=500)  # Texte de la question

    # Réponse 1
    reponse1 = models.CharField(max_length=200, null=True)
    reponse1_is_correct = models.BooleanField(default=False)

    # Réponse 2
    reponse2 = models.CharField(max_length=200, null=True)
    reponse2_is_correct = models.BooleanField(default=False)

    # Réponse 3
    reponse3 = models.CharField(max_length=200, null=True)
    reponse3_is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class UserQuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.score})"
