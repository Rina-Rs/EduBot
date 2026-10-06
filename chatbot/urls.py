from django.urls import path

from .views import chat,home


urlpatterns = [
        path("", home, name="home"),
    path("api/chat/", chat, name="chat"),
]