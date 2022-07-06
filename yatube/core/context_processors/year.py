from datetime import datetime


def current_year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'current_year': datetime.now().year
    }
