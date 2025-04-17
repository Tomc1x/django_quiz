from django import template

register = template.Library()


@register.filter(name='score_color')
def score_color(value):
    """Retourne une classe Bootstrap en fonction du score"""
    try:
        score = float(value)
        if score >= 90: return 'success'
        if score >= 75: return 'primary'
        if score >= 50: return 'warning'
        return 'danger'
    except (ValueError, TypeError):
        return ''


@register.filter
def dictmax(value, key):
    return max(item[key] for item in value)


@register.filter
def dictsum(value, key):
    return sum(item[key] for item in value)


@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None
