from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.utils import timezone


class Message(models.Model):
    TYPE_CHOICES = [
        ('NEWS', 'Nouveauté'),
        ('QUIZ', 'Nouveau quiz'),
        ('UPDATE', 'Mise à jour'),
        ('STAFF', 'Message interne'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='sent_messages')
    recipients = models.ManyToManyField(User,
                                        related_name='received_messages',
                                        blank=True)
    is_public = models.BooleanField(default=True)
    read_by = models.ManyToManyField(User,
                                     related_name='read_messages',
                                     blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_type_class(self):
        return {
            'NEWS': 'info',
            'QUIZ': 'success',
            'UPDATE': 'warning',
            'STAFF': 'danger'
        }.get(self.message_type, 'secondary')

    def is_unread_by_user(self, user):
        return not self.read_by.filter(id=user.id).exists()


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    theme = models.CharField(max_length=200, null=True, blank=True)
    level = models.IntegerField(default=1, null=True, blank=True)
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
    calculated_points = models.FloatField(
        default=0)  # Nouveau champ pour stocker les points calculés

    class Meta:
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'quiz']),
            models.Index(fields=['-calculated_points']),
        ]

    def save(self, *args, **kwargs):
        # Calcul des points selon la formule (score * niveau) / temps (en minutes)
        time_factor = max(1, self.completion_time /
                          60)  # Éviter la division par 0
        self.calculated_points = (self.score * self.quiz.level) / time_factor
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.score})"
