from caidao_tools.django.helper_sqlite import SetWalConfig

class SimpleNewsConfig(SetWalConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simple_news'
