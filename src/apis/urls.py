from django.urls import path

from .views import 新闻快讯双播音频接口_whole

urlpatterns = [
    # path('fast_news_prodcast', 新闻快讯双播音频接口.as_view()),
    path('fast_news_prodcast_whole', 新闻快讯双播音频接口_whole.as_view()),
    # path('fast_news_mp3', 新闻快讯双播音频下载.as_view()),
]