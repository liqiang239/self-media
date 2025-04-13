from caidao_tools.django.helper_sqlite import SetWalConfig


class DocshareConfig(SetWalConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'docshare'
