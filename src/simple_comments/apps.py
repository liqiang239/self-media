from caidao_tools.django.helper_sqlite import SetWalConfig


class SimpleCommentsConfig(SetWalConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simple_comments'
