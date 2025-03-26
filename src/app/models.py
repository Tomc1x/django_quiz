from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.utils import timezone


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image_url = models.URLField(blank=True,
                                null=True)  # Lien vers l'image sur Imgur
    created_at = models.DateTimeField(default=timezone.now)

    def average_score(self):
        return UserQuizResult.objects.filter(quiz=self).aggregate(
            Avg('score'))['score__avg'] or 0

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey('Quiz',
                             on_delete=models.CASCADE,
                             related_name='questions')
    text = models.CharField(max_length=500)
    reponse1 = models.CharField(max_length=200, null=True)
    reponse1_is_correct = models.BooleanField(default=False)
    reponse2 = models.CharField(max_length=200, null=True)
    reponse2_is_correct = models.BooleanField(default=False)
    reponse3 = models.CharField(max_length=200, null=True)
    reponse3_is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class UserQuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    completion_time = models.PositiveIntegerField(default=0)  # en secondes
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.score})"
