from django.db.models import Q
from .models import Message


def messages_context(request):
    if request.user.is_authenticated:
        recent_messages = Message.objects.filter(
            Q(recipients=request.user) | Q(is_public=True)).exclude(
                author=request.user).distinct().order_by('-created_at')[:8]

        # Ajoute l'information de lecture
        for msg in recent_messages:
            msg.user_has_read = msg.read_by.filter(id=request.user.id).exists()

        unread_count = sum(1 for msg in recent_messages
                           if not msg.user_has_read)

        return {
            'unread_messages_count': unread_count,
            'recent_messages': recent_messages,
        }
    return {}
